"""Collect, validate, profile and safely publish a document/index generation."""
import argparse
import datetime as dt
import json
import logging
import time
from pathlib import Path

from src.common import PROCESSED, ROOT, digest, write_json, write_jsonl
from src.eda import analyze
from src.ingest import collect
from src.prepare import prepare
from src.quality import validate_chunks, validate_documents

LOG = logging.getLogger("rag_pipeline")


def run(sources_path=None, skip_index=False, allow_partial=False):
    start = time.monotonic()
    stats = {"status": "failed", "source_outcomes": [], "index_published": False}
    documents, chunks = [], []
    reports = ROOT / "reports"
    try:
        sources_path = Path(sources_path or ROOT / "config" / "sources.json")
        sources = json.loads(sources_path.read_text(encoding="utf-8"))
        enabled = [s for s in sources if s.get("enabled", True)]
        if not enabled:
            raise ValueError("No enabled sources")
        if len({s['id'] for s in sources}) != len(sources):
            raise ValueError("Duplicate source id")
        stats["enabled_sources"] = len(enabled)
        documents = collect(sources, publish=False, outcomes=stats["source_outcomes"])
        stats["collected_documents"] = len(documents)
        failures = [o for o in stats["source_outcomes"] if o["status"] == "failed"]
        partial = bool(failures)
        if partial and not allow_partial:
            raise RuntimeError("Source collection failed; refusing partial publication")
        stats.update(validate_documents(documents))
        chunks = prepare(documents)
        stats.update(validate_chunks(documents, chunks))
        stats["chunk_dataset_sha256"] = digest(json.dumps(chunks, sort_keys=True, ensure_ascii=False))
        if not skip_index:
            from src.index import build_index
            stats["index"] = build_index(chunks, documents, partial=partial)
            stats["index_published"] = True
        # Convenience exports; queries always use the atomically published index snapshot.
        write_jsonl(PROCESSED / "documents.jsonl", documents)
        write_jsonl(PROCESSED / "chunks.jsonl", chunks)
        stats["status"] = "partial" if partial else "success"
        return stats
    except Exception as exc:
        stats["error_type"] = type(exc).__name__
        if isinstance(exc, (ValueError, RuntimeError)):
            stats["reason"] = str(exc)
        raise
    finally:
        stats["duration_seconds"] = round(time.monotonic() - start, 2)
        stats["finished_at_utc"] = dt.datetime.now(dt.UTC).isoformat()
        write_json(reports / "latest_run.json", stats)
        write_json(reports / "eda.json", analyze(documents, chunks, stats["source_outcomes"]))
        LOG.info("pipeline_result %s", json.dumps(stats, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="End-to-end document-to-index pipeline")
    parser.add_argument("--sources", help="Path to sources JSON manifest")
    parser.add_argument("--skip-index", action="store_true", help="Validate dataset without embeddings")
    parser.add_argument("--allow-partial", action="store_true", help="Diagnostic partial index (queries require explicit opt-in)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        result = run(args.sources, args.skip_index, args.allow_partial)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        raise SystemExit(2 if result["status"] == "partial" else 0)
    except (OSError, ValueError, RuntimeError):
        LOG.error("Pipeline failed; inspect reports/latest_run.json")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
