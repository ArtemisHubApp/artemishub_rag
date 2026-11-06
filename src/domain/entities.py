from dataclasses import dataclass, field


@dataclass
class Document:
    document_id: str
    source_url: str
    title: str
    content: str
    content_sha256: str
    organization: str | None = None
    metadata: dict = field(default_factory=dict)

@dataclass
class Chunk:
    document_id: str
    source_url: str
    text: str
    content_sha256: str
    chunk_id: str | None = None
    metadata: dict = field(default_factory=dict)

@dataclass
class PipelineState:
    current_stage: str  # 'INGEST', 'PREPARE', 'INDEX'
    status: str         # 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED'
    last_updated: str
    error_message: str | None = None
