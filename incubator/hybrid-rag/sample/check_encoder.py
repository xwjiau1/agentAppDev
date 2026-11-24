"""Smoke test the real encoder from inside the Compose network."""
import json
import math
import urllib.error
import urllib.request


BASE = "http://encoder:8000"


def call(route, texts=None):
    request = urllib.request.Request(BASE + route)
    if texts is not None:
        request.data = json.dumps({"texts": texts}).encode()
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def close_vectors(left, right):
    return all(math.isclose(a, b, abs_tol=2e-6) for a, b in zip(left, right, strict=True))


def main():
    texts = ["incident ticket TKT-8472", "审批通过后，退款将在五个工作日内原路退回。"]
    signature = call("/health/ready")["modelSignature"]
    combined = call("/encode", texts)
    dense = call("/dense", texts)
    sparse = call("/sparse", texts)
    assert combined["modelSignature"] == dense["modelSignature"] == sparse["modelSignature"] == signature
    assert len(combined["items"]) == len(texts)
    for both, dense_only, sparse_only in zip(combined["items"], dense["items"], sparse["items"], strict=True):
        assert len(both["dense"]) == 1024 and close_vectors(both["dense"], dense_only["dense"])
        assert math.isclose(sum(value**2 for value in both["dense"]), 1, abs_tol=2e-5)
        terms = both["sparse"]["indices"]
        assert terms and terms == sorted(set(terms)) == sparse_only["sparse"]["indices"]
        assert len(terms) == len(both["sparse"]["values"])
        assert close_vectors(both["sparse"]["values"], sparse_only["sparse"]["values"])
    try:
        call("/encode", ["test " * 1100])
    except urllib.error.HTTPError as error:
        assert error.code == 422 and "1024 tokens" in json.load(error)["detail"]
    else:
        raise AssertionError("Token overflow was accepted")
    print(f"Verified dense/sparse/encode and tokenizer limits for {signature}")


if __name__ == "__main__":
    main()
