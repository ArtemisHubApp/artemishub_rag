# Plan: Agent Orchestration Layer for Projeto Artemis

## Goal
Transform the linear RAG pipeline into an orchestrated system of agents/use-cases, adapting the architecture from `checa-ai`.

## Proposed Architecture (Hexagonal)
- **Domain**: Define `Document`, `Chunk`, and `PipelineState` entities.
- **Application**:
    - `IngestUseCase`: Wraps `src.ingest.collect`.
    - `PrepareUseCase`: Wraps `src.prepare.prepare`.
    - `IndexUseCase`: Wraps `src.index.build_index`.
    - `OrchestratePipelineUseCase`: The "Brain" that coordinates the flow, handles checkpoints, and manages failures.
- **Adapters**:
    - `FileRepository`: Handles reading/writing JSONL and reports.
    - `VectorStoreAdapter`: Wraps the indexing logic.
    - `CLIAdapter`: The entry point (`main.py`).

## SDD Phases
1. **Spec**: Define the interfaces for the UseCases and the Orchestrator.
2. **Domain**: Implement core entities.
3. **Adapters**: Create the repository and store adapters.
4. **Application**: Implement the UseCases and the Orchestrator.
5. **Integration**: Replace the current `src/pipeline.py` logic with the new Orchestrator.
6. **Verification**: Run tests to ensure parity with the original linear pipeline.

## Success Criteria
- Pipeline can resume from a failed stage using checkpoints.
- Code follows hexagonal architecture (separation of concerns).
- `src/pipeline.py` becomes a thin wrapper around the Orchestrator.
