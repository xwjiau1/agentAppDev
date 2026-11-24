import logging
import math
import os
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


ENCODER_ID = "BAAI/bge-m3"
ENCODER_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
RERANKER_ID = "BAAI/bge-reranker-v2-m3"
RERANKER_REVISION = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
MAX_TOKENS = 1024
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8192)]


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EncodeRequest(RequestModel):
    texts: list[Text] = Field(min_length=1, max_length=8)


class Candidate(RequestModel):
    chunkId: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    text: Text


class RerankRequest(RequestModel):
    query: Text
    candidates: list[Candidate] = Field(min_length=1, max_length=20)


class VectorInputError(ValueError):
    pass


def sparse_vector(weights):
    pairs = sorted((int(token), float(weight)) for token, weight in weights.items())
    if any(token < 0 or not math.isfinite(weight) for token, weight in pairs):
        raise RuntimeError("Encoder returned an invalid sparse vector")
    return {"indices": [token for token, _ in pairs], "values": [weight for _, weight in pairs]}


def snapshot(model_id: str, revision: str) -> str:
    from huggingface_hub import snapshot_download

    path = os.getenv("MODEL_PATH")
    if path:
        directory = Path(path)
        if (directory / ".revision").read_text(encoding="utf-8").strip() != revision:
            raise RuntimeError(f"Mounted snapshot must declare revision {revision}")
        return str(directory.resolve())
    return snapshot_download(
        repo_id=model_id,
        revision=revision,
        allow_patterns=["*.json", "sentencepiece.bpe.model", "*.safetensors", "pytorch_model.bin", "*.pt"],
    )


class Encoder:
    signature = f"{ENCODER_ID}@{ENCODER_REVISION}:tokenizer=same:max=1024:normalized:fp32:v1"

    def __init__(self):
        from FlagEmbedding import BGEM3FlagModel

        self.model = BGEM3FlagModel(
            snapshot(ENCODER_ID, ENCODER_REVISION), devices="cpu", use_fp16=False, normalize_embeddings=True
        )
        self.encode(["模型预热 warmup"], dense=True, sparse=True)
        logging.getLogger("uvicorn.error").info("Loaded %s", self.signature)

    def encode(self, texts: list[str], *, dense: bool, sparse: bool) -> list[dict]:
        tokens = self.model.tokenizer(texts, add_special_tokens=True, truncation=False)["input_ids"]
        if any(len(item) > MAX_TOKENS for item in tokens):
            raise VectorInputError(f"Each text must fit within {MAX_TOKENS} tokens")
        output = self.model.encode(
            texts, batch_size=8, max_length=MAX_TOKENS,
            return_dense=dense, return_sparse=sparse, return_colbert_vecs=False,
        )
        items = [{} for _ in texts]
        if dense:
            for item, vector in zip(items, output["dense_vecs"], strict=True):
                item["dense"] = vector.tolist()
        if sparse:
            for item, weights in zip(items, output["lexical_weights"], strict=True):
                item["sparse"] = sparse_vector(weights)
        return items


class Reranker:
    signature = f"{RERANKER_ID}@{RERANKER_REVISION}:max=1024:raw:fp32:v1"

    def __init__(self):
        from FlagEmbedding import FlagReranker

        self.model = FlagReranker(snapshot(RERANKER_ID, RERANKER_REVISION), devices="cpu", use_fp16=False)
        self.score("warmup", [Candidate(chunkId="warmup", text="模型预热 warmup")])
        logging.getLogger("uvicorn.error").info("Loaded %s", self.signature)

    def score(self, query: str, candidates: list[Candidate]) -> list[dict]:
        pairs = [[query, candidate.text] for candidate in candidates]
        scores = self.model.compute_score(pairs, batch_size=4, max_length=MAX_TOKENS, normalize=False)
        if isinstance(scores, (int, float)):
            scores = [scores]
        items = []
        for candidate, score in zip(candidates, scores, strict=True):
            score = float(score)
            if not math.isfinite(score):
                raise RuntimeError("Reranker returned a non-finite score")
            items.append({"chunkId": candidate.chunkId, "score": score})
        return items
