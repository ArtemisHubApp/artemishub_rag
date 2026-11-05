"""Dataset contracts and referential integrity; lengths are character counts."""
from collections import Counter
from datetime import datetime
from urllib.parse import urlparse

from src.common import digest

DOCUMENT_FIELDS = ("document_id", "title", "source", "source_url", "document_type",
                   "collected_at", "content", "content_hash", "metadata")


def validate_documents(documents, minimum_chars=1, maximum_chars=2_000_000):
    if not documents:
        raise ValueError("No documents extracted")
    seen = set()
    for doc in documents:
        for key in DOCUMENT_FIELDS:
            if key not in doc or doc[key] is None or doc[key] == "":
                raise ValueError(f"Missing {key} in document {doc.get('document_id')}")
            if key != "metadata" and (not isinstance(doc[key], str) or not doc[key].strip()):
                raise ValueError(f"Invalid document {key}")
        if not isinstance(doc["metadata"], dict):
            raise TypeError("Document metadata must be an object")
        if doc["document_type"] not in ("html", "pdf"):
            raise ValueError("Invalid document_type")
        if datetime.fromisoformat(doc["collected_at"]).tzinfo is None:
            raise ValueError("collected_at requires timezone")
        if doc["metadata"].get("page") != doc.get("page"):
            raise ValueError("Inconsistent page metadata")
        url = urlparse(doc["source_url"])
        if url.scheme not in ("https", "http") or not url.hostname or url.username or url.password:
            raise ValueError("Invalid source_url")
        if not isinstance(doc["content"], str) or len(doc["content"].strip()) < minimum_chars:
            raise ValueError(f"Document section too short: {doc['document_id']}")
        if len(doc["content"]) > maximum_chars:
            raise ValueError("Document section too large")
        if doc["content_hash"] != digest(doc["content"]):
            raise ValueError("Invalid content_hash")
        if doc.get("content_sha256", doc["content_hash"]) != doc["content_hash"]:
            raise ValueError("Inconsistent content_sha256")
        locator = (doc["document_id"], doc.get("page"), doc["metadata"].get("article"))
        if locator in seen:
            raise ValueError("Duplicate document locator")
        seen.add(locator)
    return {"documents": len(documents), "sources": len({d['document_id'] for d in documents})}


def validate_chunks(documents, chunks, max_chars=1200):
    if not chunks:
        raise ValueError("No chunks produced")
    lookup = {(d["document_id"], d.get("page")): d for d in documents}
    seen, indices = set(), set()
    counts = Counter()
    for chunk in chunks:
        for field in ("chunk_id", "document_id", "text", "chunk_index", "source_url", "metadata"):
            if field not in chunk:
                raise ValueError(f"Missing chunk {field}")
        key = (chunk["document_id"], chunk.get("page"))
        doc = lookup.get(key)
        if doc is None or doc["source_url"] != chunk["source_url"]:
            raise ValueError("Invalid chunk reference")
        if not isinstance(chunk["text"], str) or not 0 < len(chunk["text"].strip()) <= max_chars:
            raise ValueError("Invalid chunk size")
        if not isinstance(chunk["metadata"], dict) or chunk["text"] not in doc["content"]:
            raise ValueError("Chunk content or metadata mismatch")
        if chunk["metadata"].get("page") != chunk.get("page"):
            raise ValueError("Inconsistent chunk page metadata")
        if chunk.get("content_sha256") != digest(chunk["text"]):
            raise ValueError("Invalid chunk hash")
        index = chunk["chunk_index"]
        if not isinstance(index, int) or index < 0 or (*key, index) in indices:
            raise ValueError("Invalid chunk_index")
        if not chunk["chunk_id"] or chunk["chunk_id"] in seen:
            raise ValueError("Duplicate chunk_id")
        seen.add(chunk["chunk_id"])
        indices.add((*key, index))
        counts[key] += 1
    if set(lookup) != set(counts):
        raise ValueError("Documents without chunks")
    return {"chunks": len(chunks), "chunks_per_document": {
        f"{key[0]}:page={key[1]}": count for key, count in sorted(counts.items(), key=str)
    }}
