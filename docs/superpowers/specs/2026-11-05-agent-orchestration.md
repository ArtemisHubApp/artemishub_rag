# Spec: Agent Orchestration Layer

## 1. Domain Entities
- **Document**: dataclass (id, url, title, content, sha256)
- **Chunk**: dataclass (doc_id, content, embedding_id, metadata)
- **PipelineState**: dataclass (current_stage, last_successful_stage, timestamp, status)

## 2. Application Ports (Interfaces)
- **Repository Interface**:
    - `save_documents(docs: List[Document])`
    - `load_documents() -> List[Document]`
    - `save_chunks(chunks: List[Chunk])`
    - `load_chunks() -> List[Chunk]`
    - `update_state(state: PipelineState)`
    - `get_state() -> PipelineState`
- **VectorStore Interface**:
    - `index_chunks(chunks: List[Chunk]) -> bool`
- **PipelineStage Interface**:
    - `execute(input_data) -> output_data`

## 3. Application Use Cases
- **IngestUseCase**:
    - Inputs: Sources manifest
    - Logic: `collect()` -> `Repository.save_documents()`
- **PrepareUseCase**:
    - Inputs: `Repository.load_documents()`
    - Logic: `prepare()` -> `Repository.save_chunks()`
- **IndexUseCase**:
    - Inputs: `Repository.load_chunks()`
    - Logic: `VectorStore.index_chunks()`
- **OrchestratePipelineUseCase**:
    - Logic:
        1. Load `PipelineState`.
        2. If state is 'IDLE' or 'FAILED' at INGEST -> Run `IngestUseCase`.
        3. If state is 'INGESTED' -> Run `PrepareUseCase`.
        4. If state is 'PREPARED' -> Run `IndexUseCase`.
        5. Update state to 'COMPLETED'.
        6. Handle exceptions by marking state as 'FAILED'.

## 4. Adapters
- **FileRepository**: Implements Repository Interface using JSONL and `reports/state.json`.
- **ChromaDBAdapter** (or similar): Implements VectorStore Interface.
- **CLIRunner**: Implements the main entry point.
