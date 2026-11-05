import argparse
import json
import logging
import time
from pathlib import Path

from src.common import PROCESSED, ROOT
from src.ingest import collect
from src.prepare import prepare
from src.index import build_index

LOG = logging.getLogger("rag_pipeline")

def run(sources_path=None, skip_index=False, allow_partial=False):
    start = time.monotonic()
    sources_path = Path(sources_path or ROOT / "config" / "sources.json")
    sources = json.loads(sources_path.read_text(encoding="utf-8"))
    enabled = [s for s in sources if s.get("enabled", True)]
    
    stats = {
        "status": "failed",
        "stage": "START",
        "duration_seconds": 0,
        "documents": 0,
        "sources": 0,
        "chunks": 0,
        "enabled_sources": len(enabled)
    }

    try:
        # Stage 1: Ingest
        LOG.info("Stage: INGEST")
        stats["stage"] = "INGEST"
        docs = collect(sources, strict=not allow_partial, publish=True)
        
        # Stage 2: Prepare
        LOG.info("Stage: PREPARE")
        stats["stage"] = "PREPARE"
        chunks = prepare(docs)
        # Save chunks to disk to maintain compatibility with build_index and tests
        from src.common import write_jsonl
        write_jsonl(PROCESSED / "chunks.jsonl", chunks)
        
        # Stage 3: Index
        if not skip_index:
            LOG.info("Stage: INDEX")
            stats["stage"] = "INDEX"
            index_result = build_index(chunks=chunks, documents=docs, partial=allow_partial)
            stats["index_stats"] = index_result
        else:
            LOG.info("Stage: INDEX (skipped)")
            stats["status"] = "skipped_index"

        stats["status"] = "success"
        stats["stage"] = "COMPLETED"

    except Exception as e:
        LOG.error(f"Pipeline failed at stage {stats['stage']}: {e}")
        raise e
    finally:
        duration = round(time.monotonic() - start, 2)
        stats["duration_seconds"] = duration
        
        # Final stats collection
        try:
            from src.common import load_jsonl
            docs = load_jsonl(PROCESSED / "documents.jsonl") if (PROCESSED / "documents.jsonl").exists() else []
            chunks = load_jsonl(PROCESSED / "chunks.jsonl") if (PROCESSED / "chunks.jsonl").exists() else []
            stats.update({
                "documents": len(docs),
                "sources": len({d["document_id"] for d in docs}),
                "chunks": len(chunks),
            })
        except Exception as e:
            LOG.warning(f"Could not collect final stats: {e}")
        
        reports_dir = ROOT / "reports"
        reports_dir.mkdir(exist_ok=True)
        (reports_dir / "latest_run.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
        
        LOG.info(f"Pipeline finished in {duration}s. Status: {stats['status']}")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description="Document-to-index pipeline")
    parser.add_argument("--sources", help="Path to sources JSON manifest")
    parser.add_argument("--skip-index", action="store_true", help="Validate dataset without embeddings")
    parser.add_argument("--allow-partial", action="store_true", help="Allow partial index for diagnostics")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        result = run(args.sources, args.skip_index, args.allow_partial)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        raise SystemExit(0)
    except Exception:
        LOG.exception("Pipeline failure")
        raise SystemExit(1) from None

if __name__ == "__main__":
    main()
