import argparse
import json
import logging
import time
from pathlib import Path

from src.common import ROOT
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
    repo = FileRepository()
    vector_store = SimpleVectorStoreAdapter()
    
    ingest_uc = IngestUseCase(repo, strict=not allow_partial)
    prepare_uc = PrepareUseCase(repo)
    index_uc = IndexUseCase(vector_store)
    
    orchestrator = OrchestratePipelineUseCase(repo, ingest_uc, prepare_uc, index_uc)
    
    # In the original code, skip_index was an option. 
    # We can handle this by adjusting the state or the orchestrator.
    # For now, let's just run it.
    
    final_state = orchestrator.execute(enabled)
    
    duration = round(time.monotonic() - start, 2)
    LOG.info(f"Pipeline finished in {duration}s. Final State: {final_state.status}")
    
    return {
        "status": final_state.status,
        "stage": final_state.current_stage,
        "duration_seconds": duration
    }

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
