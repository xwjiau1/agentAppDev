"""Evaluate the same labeled queries on all four retrieval paths."""
import argparse
import hashlib
import json
import math
import statistics
import time
import urllib.request
import uuid
from pathlib import Path


MODES = (("dense", "DENSE", False), ("sparse", "SPARSE", False),
         ("rrf", "HYBRID", False), ("rerank", "HYBRID", True))


def search(base_url, case, mode, rerank):
    payload = {"query": case["query"], "topK": 5, "mode": mode, "rerank": rerank}
    if "filterSources" in case:
        payload["filters"] = {"documentIds": [document_id(source) for source in case["filterSources"]]}
    request = urllib.request.Request(f"{base_url}/v1/search", json.dumps(payload).encode(),
                                     {"Content-Type": "application/json"})
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    elapsed = (time.perf_counter() - start) * 1000
    if result["rerankDegraded"]:
        raise RuntimeError(f"Reranking degraded for {case['name']}")
    hits_by_id = {hit["chunkId"]: hit for hit in result["hits"]}
    for citation in result["citations"]:
        hit = hits_by_id[citation["chunkId"]]
        for key in ("source", "page", "chunkIndex", "documentId"):
            assert citation.get(key) == hit.get(key), (citation, hit)
        assert hit["text"] in result["context"]
    if not case["expected"]:
        assert not result["hits"] and not result["context"] and not result["citations"], case["name"]
    if rerank:
        assert all(hit["scoreType"] == "reranker" for hit in result["hits"])
    return result["hits"], elapsed


def document_id(source):
    return str(uuid.UUID(bytes=hashlib.md5(source.encode(), usedforsecurity=False).digest(), version=3))


def metrics(hits, expected):
    matched = set()
    first_rank = None
    for rank, hit in enumerate(hits, 1):
        for index, location in enumerate(expected):
            if all(hit.get(key) == value for key, value in location.items()):
                matched.add(index)
                if first_rank is None:
                    first_rank = rank
    return len(matched) / len(expected), 1 / first_rank if first_rank else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8080")
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds must be positive")
    cases = json.loads(Path(__file__).with_name("queries.json").read_text(encoding="utf-8"))
    report = {}
    for name, mode, rerank in MODES:
        search(args.url, cases[0], mode, rerank)
        samples = []
        scores = {}
        for _ in range(args.rounds):
            for case in cases:
                hits, elapsed = search(args.url, case, mode, rerank)
                samples.append(elapsed)
                if case["expected"]:
                    scores[case["name"]] = metrics(hits, case["expected"])
        if name in {"rrf", "rerank"}:
            assert all(recall == 1 for recall, _ in scores.values()), scores
        report[name] = {"recall@5": round(statistics.mean(r for r, _ in scores.values()), 3),
                        "mrr@5": round(statistics.mean(m for _, m in scores.values()), 3),
                        "p95_ms": round(sorted(samples)[math.ceil(0.95 * len(samples)) - 1], 1),
                        "query_count": len(cases), "timed_requests": len(samples), "per_query": scores}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
