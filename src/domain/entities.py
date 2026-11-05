from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Document:
    document_id: str
    source_url: str
    title: str
    content: str
    content_sha256: str
    organization: Optional[str] = None
    metadata: dict = field(default_factory=dict)

@dataclass
class Chunk:
    document_id: str
    source_url: str
    text: str
    content_sha256: str
    chunk_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

@dataclass
class PipelineState:
    current_stage: str  # 'INGEST', 'PREPARE', 'INDEX'
    status: str         # 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED'
    last_updated: str
    error_message: Optional[str] = None
