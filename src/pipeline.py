"""Run ingestion, validation, chunking and incremental vector indexing in one command.

A failed source blocks publication of a partial dataset by default.
"""
import argparse
import datetime as dt
import json
import logging
import time
from pathlib import Path

from src.common import PROCESSED, ROOT, digest, write_jsonl
from src.ingest import collect
from src.prepare import prepare

LOG = logging.getLogger("rag_pipeline")


def validate_documents(documents, minimum_chars=100):
    if not documents:
        raise ValueError("No documents extracted")
    for doc in documents:
        for key in ("document_id", "source_url", "title", "content", "content_sha256"):
            if not doc.get(key):
                raise ValueError(f"Missing {key} in document {doc.get('document_id')}")
        if len(doc["content"].strip()) < minimum_chars:
            raise ValueError(f"Document section too short: {doc['document_id']} page {doc.get('page')}")
    return {"documents": len(documents), "sources": len({d['document_id'] for d in documents})}


def run(sources_path=None, skip_index=False, allow_partial=False):
    start = time.monotonic()
    sources_path = Path(sources_path or ROOT / "config" / "sources.json")
    sources = json.loads(sources_path.read_text(encoding="utf-8"))
    enabled = [s for s in sources if s.get("enabled", True)]
    if not enabled:
        raise ValueError("No enabled sources")
    # Do not publish a partial dataset if any enabled source fails.
    documents = collect(sources, strict=not allow_partial, publish=False)
    stats = validate_documents(documents)
    chunks = prepare(documents)
    if not chunks:
        raise ValueError("No chunks produced")
    write_jsonl(PROCESSED / "documents.jsonl", documents)
    write_jsonl(PROCESSED / "chunks.jsonl", chunks)
    stats["chunks"] = len(chunks)
    stats["enabled_sources"] = len(enabled)
    stats["chunk_dataset_sha256"] = digest(json.dumps(chunks, sort_keys=True, ensure_ascii=False))
    if not skip_index:
        from src.index import build_index
        stats["index"] = build_index()
    stats["duration_seconds"] = round(time.monotonic() - start, 2)
    stats["finished_at_utc"] = dt.datetime.now(dt.UTC).isoformat()
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "latest_run.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    LOG.info("Pipeline complete: %s", stats)
    return stats


def main():
    parser = argparse.ArgumentParser(description="End-to-end document-to-index pipeline")
    parser.add_argument("--sources", help="Path to sources JSON manifest")
    parser.add_argument("--skip-index", action="store_true", help="Prepare dataset without embedding/indexing")
    parser.add_argument("--allow-partial", action="store_true", help="Allow missing sources (not recommended)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        print(json.dumps(run(args.sources, args.skip_index, args.allow_partial), indent=2, ensure_ascii=False))
    except Exception:
        LOG.exception("Pipeline failed; previous published data may be preserved")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
