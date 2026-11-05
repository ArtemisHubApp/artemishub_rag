"""Lightweight EDA with no notebook dependency."""
from collections import Counter
from statistics import median

from src.common import PROCESSED, load_jsonl


def main():
    documents = load_jsonl(PROCESSED / "documents.jsonl")
    chunks = load_jsonl(PROCESSED / "chunks.jsonl")
    print(f"Document sections: {len(documents)}")
    print(f"Unique sources: {len({x['document_id'] for x in documents})}")
    print(f"Chunks: {len(chunks)}")
    print("Chunks per source:", dict(Counter(x["document_id"] for x in chunks)))
    print("Chunks per topic:", dict(Counter(x["topic"] for x in chunks)))
    print("Empty extracted sections:", sum(not x["content"].strip() for x in documents))
    print("Duplicate section hashes:", len(documents) - len({x["content_sha256"] for x in documents}))
    if chunks:
        lengths = [len(x["text"]) for x in chunks]
        print(f"Chunk length (characters): min={min(lengths)} median={median(lengths)} max={max(lengths)}")


if __name__ == "__main__":
    main()
