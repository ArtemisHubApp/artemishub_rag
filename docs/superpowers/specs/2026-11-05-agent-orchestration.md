# Spec: Agent Orchestration Layer

## Functional Requirements
1. **Sequential Execution**: The orchestrator must execute Ingest $\rightarrow$ Prepare $\rightarrow$ Index.
2. **State Persistence**: The current stage and status must be persisted to `reports/latest_run.json`.
3. **Partial Publication**: Support `--allow-partial` to allow the pipeline to complete even if some sources fail.
4. **Index Skipping**: Support `--skip-index` to validate the dataset without generating embeddings.

## Technical Specification
- **Class `PipelineOrchestrator`**:
    - `execute(sources)`: Main entry point.
    - `_run_stage(stage_name, func, \*args)`: Wrapper to handle logging, timing, and state updates.
- **State Model**:
    - `status`: "success" | "failed" | "partial"
    - `stage`: "INGEST" | "PREPARE" | "INDEX" | "COMPLETED"
    - `duration_seconds`: float
- **Error Handling**:
    - Catch all exceptions in `_run_stage`.
    - Update state to "failed" and current stage.
    - Re-raise exception to be handled by `pipeline.run()`.

## Metrics to Track
- Number of documents collected.
- Number of chunks produced.
- Index publication status.
- Time taken per stage.
