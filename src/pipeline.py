import argparse
import json
import logging
import time
from pathlib import Path

from src.adapters.outbound.file_repository import FileRepository
from src.adapters.outbound.vector_store_adapter import SimpleVectorStoreAdapter
from src.application.use_cases.orchestrator import OrchestratePipelineUseCase
from src.application.use_cases.pipeline_use_cases import (
    IndexUseCase,
    IngestUseCase,
    PrepareUseCase,
)
from src.common import PROCESSED, ROOT

LOG = logging.getLogger("rag_pipeline")

def run(sources_path=None, skip_index=False, allow_partial=False):
    start = time.monotonic()
    sources_path = Path(sources_path or ROOT / "config" / "sources.json")
    sources = json.loads(sources_path.read_text(encoding="utf-8"))
    enabled = [s for s in sources if s.get("enabled", True)]
    
    # Dependency Injection
    repo = FileRepository(root=ROOT, processed=PROCESSED)
    vector_store = SimpleVectorStoreAdapter()
    
    ingest_uc = IngestUseCase(repo, strict=not allow_partial)
    prepare_uc = PrepareUseCase(repo)
    index_uc = IndexUseCase(vector_store)
    
    orchestrator = OrchestratePipelineUseCase(repo, ingest_uc, prepare_uc, index_uc)
    
    stats = {
        "status": "failed",
        "stage": "UNKNOWN",
        "duration_seconds": 0,
        "documents": 0,
        "sources": 0,
        "chunks": 0,
        "enabled_sources": len(enabled)
    }

    try:
        final_state = orchestrator.execute(enabled)
        stats.update({
            "status": "success" if final_state.status == "COMPLETED" else "failed",
            "stage": final_state.current_stage,
        })
    except Exception as e:
        state = repo.get_state()
        stats["stage"] = state.current_stage
        raise e
    finally:
        duration = round(time.monotonic() - start, 2)
        stats["duration_seconds"] = duration
        
        docs = repo.load_documents()
        chunks = repo.load_chunks()
        stats.update({
            "documents": len(docs),
            "sources": len({d.document_id for d in docs}),
            "chunks": len(chunks),
        })
        
        reports_dir = ROOT / "reports"
        reports_dir.mkdir(exist_ok=True)
        (reports_dir / "latest_run.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
        
        LOG.info(f"Pipeline finished in {duration}s. Status: {stats['status']}")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description="Orchestrated document-to-index pipeline")
    parser.add_argument("--sources", help="Path to sources JSON manifest")
    parser.add_argument("--skip-index", action="store_true", help="Validate dataset without embeddings")
    parser.add_argument("--allow-partial", action="store_true", help="Diagnostic partial index (queries require explicit opt-in)")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        result = run(args.sources, args.skip_index, args.allow_partial)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["status"] == "partial":
            raise SystemExit(2)
        raise SystemExit(0)
    except (OSError, ValueError, RuntimeError):
        LOG.error("Pipeline failed; inspect reports/latest_run.json")
        raise SystemExit(1) from None
    except Exception:
        LOG.exception("Unexpected pipeline failure")
        raise SystemExit(1) from None

if __name__ == "__main__":
    main()
