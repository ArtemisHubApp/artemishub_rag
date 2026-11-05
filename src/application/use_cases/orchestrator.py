import logging
from datetime import datetime
from src.domain.entities import PipelineState
from src.application.ports.repository import PipelineRepository
from src.application.use_cases.pipeline_use_cases import IngestUseCase, PrepareUseCase, IndexUseCase

LOG = logging.getLogger("orchestrator")

class OrchestratePipelineUseCase:
    def __init__(self, repo: PipelineRepository, ingest: IngestUseCase, 
                 prepare: PrepareUseCase, index: IndexUseCase):
        self.repo = repo
        self.ingest = ingest
        self.prepare = prepare
        self.index = index

    def execute(self, sources):
        state = self.repo.get_state()
        LOG.info(f"Starting pipeline. Current state: {state.current_stage} ({state.status})")

        try:
            # 1. Ingest
            if state.current_stage == "INGEST" or state.status == "FAILED":
                LOG.info("Executing Ingest stage...")
                self.repo.update_state(PipelineState("INGEST", "RUNNING", datetime.now().isoformat()))
                self.ingest.execute(sources)
                self.repo.update_state(PipelineState("PREPARE", "PENDING", datetime.now().isoformat()))
                state = self.repo.get_state()

            # 2. Prepare
            if state.current_stage == "PREPARE":
                LOG.info("Executing Prepare stage...")
                self.repo.update_state(PipelineState("PREPARE", "RUNNING", datetime.now().isoformat()))
                self.prepare.execute()
                self.repo.update_state(PipelineState("INDEX", "PENDING", datetime.now().isoformat()))
                state = self.repo.get_state()

            # 3. Index
            if state.current_stage == "INDEX":
                LOG.info("Executing Index stage...")
                self.repo.update_state(PipelineState("INDEX", "RUNNING", datetime.now().isoformat()))
                chunks = self.repo.load_chunks()
                self.index.execute(chunks)
                self.repo.update_state(PipelineState("COMPLETED", "COMPLETED", datetime.now().isoformat()))
                state = self.repo.get_state()

            LOG.info("Pipeline completed successfully.")
            return state

        except Exception as e:
            LOG.exception(f"Pipeline failed at stage {state.current_stage}")
            self.repo.update_state(PipelineState(
                current_stage=state.current_stage,
                status="FAILED",
                last_updated=datetime.now().isoformat(),
                error_message=str(e)
            ))
            raise e
