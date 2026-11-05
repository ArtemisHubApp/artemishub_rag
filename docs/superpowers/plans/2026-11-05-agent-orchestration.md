# Plan: Agent Orchestration Layer

## Context
The current pipeline is a linear sequence of functions. To improve resilience, observability, and flexibility, we need an orchestration layer that coordinates the RAG pipeline stages.

## Goals
1. **Decouple Coordination from Logic**: Separate the "how to run the pipeline" from "how to ingest/index".
2. **State Management**: Track the pipeline state (PENDING, RUNNING, COMPLETED, FAILED) for each stage.
3. **Observability**: Detailed logging and reporting of each stage's outcome.
4. **Flexibility**: Allow skipping stages (e.g., `skip_index`) or partial runs without breaking the flow.

## Proposed Architecture
- **PipelineOrchestrator**: A coordinator class that:
    - Loads the source manifest.
    - Executes stages in order: Ingest $\rightarrow$ Prepare $\rightarrow$ Index.
    - Manages a `PipelineState` object to track progress.
    - Handles errors by recording the failure stage and stopping execution.
- **Stage Interface**: Define a consistent way for stages to report their status and stats.

## Success Criteria
- `pipeline.run()` uses the orchestrator.
- A `latest_run.json` report is generated with detailed stage-by-stage metrics.
- Pipeline can be run partially (e.g., just ingest and prepare) while maintaining data integrity.
