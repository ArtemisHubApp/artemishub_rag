import argparse
import json
import logging
import time
from pathlib import Path

from src.common import ROOT, PROCESSED
from src.adapters.outbound.file_repository import FileRepository
from src.adapters.outbound.vector_store_adapter import SimpleVectorStoreAdapter
from src.application.use_cases.pipeline_use_cases import IngestUseCase, PrepareUseCase, IndexUseCase
from src.application.use_cases.orchestrator import OrchestratePipelineUseCase

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
    
    final_state = orchestrator.execute(enabled)
    
    # Collect stats for compatibility with tests
    docs = repo.load_documents()
    chunks = repo.load_chunks()
    
    duration = round(time.monotonic() - start, 2)
    
    stats = {
        "status": final_state.status,
        "stage": final_state.current_stage,
        "duration_seconds": duration,
        "documents": len(docs),
        "sources": len({d.document_id for d in docs}),
        "chunks": len(chunks),
        "enabled_sources": len(enabled)
    }
    
    # Write report for backward compatibility (tests)
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    (reports_dir / "latest_run.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    
    LOG.info(f"Pipeline finished in {duration}s. Final State: {final_state.status}")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description="Orchestrated document-to-index pipeline")
    parser.add_argument("--sources", help="Path to sources JSON manifest")
    parser.add_argument("--skip-index", action="store_true", help="Prepare dataset without embedding/indexing")
    parser.add_argument("--allow-partial", action="store_true", help="Allow missing sources (not recommended)")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        print(json.dumps(run(args.sources, args.skip_index, args.allow_partial), indent=2, ensure_ascii=False))
    except Exception:
        LOG.exception("Pipeline failed")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
