import asyncio
import threading

from fastapi import HTTPException
from fastapi.testclient import TestClient

from rag_models.api import InferenceSlot, create_app
from rag_models.models import VectorInputError, sparse_vector


class FakeEncoder:
    signature = "fake:encoder"

    def encode(self, texts, *, dense, sparse):
        if "too many tokens" in texts:
            raise VectorInputError("Token limit exceeded")
        items = []
        for text in texts:
            item = {}
            if dense:
                item["dense"] = [float(len(text))] * 1024
            if sparse:
                item["sparse"] = sparse_vector({"11": 0.3, "2": 0.9} if text != "!" else {})
            items.append(item)
        return items


class FakeReranker:
    signature = "fake:reranker"

    def score(self, query, candidates):
        return [{"chunkId": candidate.chunkId, "score": float(query in candidate.text)} for candidate in candidates]


def test_encoder_routes_preserve_batch_order_and_projection():
    with TestClient(create_app("encoder", FakeEncoder)) as client:
        payload = {"texts": ["hi", "!"]}
        combined = client.post("/encode", json=payload).json()
        dense = client.post("/dense", json=payload).json()
        sparse = client.post("/sparse", json=payload).json()
        assert combined["modelSignature"] == client.get("/health/ready").json()["modelSignature"]
        assert combined["items"] == [a | b for a, b in zip(dense["items"], sparse["items"], strict=True)]
        assert combined["items"][0]["dense"] == [2.0] * 1024
        assert sparse["items"][0]["sparse"]["indices"] == [2, 11]
        assert sparse["items"][1]["sparse"] == {"indices": [], "values": []}


def test_invalid_encoding_requests():
    with TestClient(create_app("encoder", FakeEncoder)) as client:
        for texts in ([], [" \n"], ["ok"] * 9, ["too many tokens"]):
            assert client.post("/encode", json={"texts": texts}).status_code == 422


def test_reranker_returns_scores_keyed_by_chunk_id():
    with TestClient(create_app("reranker", FakeReranker)) as client:
        payload = {"query": "hit", "candidates": [{"chunkId": "a", "text": "a hit"}, {"chunkId": "b", "text": "miss"}]}
        assert client.post("/rerank", json=payload).json()["items"] == [
            {"chunkId": "a", "score": 1.0}, {"chunkId": "b", "score": 0.0}
        ]
        payload["candidates"][1]["chunkId"] = "a"
        assert client.post("/rerank", json=payload).status_code == 422


def test_cancellation_keeps_slot_busy_until_actual_completion():
    async def exercise():
        slot = InferenceSlot(0.05)
        entered = threading.Event()
        release = threading.Event()

        def blocked():
            entered.set()
            return release.wait(3)

        caller = asyncio.create_task(slot.run(blocked))
        assert await asyncio.to_thread(entered.wait, 1)
        caller.cancel()
        await asyncio.gather(caller, return_exceptions=True)
        try:
            await slot.run(lambda: "must wait")
        except HTTPException as exc:
            assert exc.status_code == 503
        else:
            raise AssertionError("Slot was released before the worker finished")
        finally:
            release.set()
        assert await slot.run(lambda: "done") == "done"

    asyncio.run(exercise())
