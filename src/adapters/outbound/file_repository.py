import json
import os
from pathlib import Path
from typing import List
from datetime import datetime
from src.application.ports.repository import PipelineRepository
from src.domain.entities import Document, Chunk, PipelineState
from src.common import PROCESSED, ROOT

class FileRepository(PipelineRepository):
    def __init__(self, root=ROOT, processed=PROCESSED):
        self.root = root
        self.processed = processed
        self.processed.mkdir(parents=True, exist_ok=True)
        self.docs_path = self.processed / "documents.jsonl"
        self.chunks_path = self.processed / "chunks.jsonl"
        self.state_path = self.root / "reports" / "state.json"
        self.root.joinpath("reports").mkdir(parents=True, exist_ok=True)

    def save_documents(self, docs: List[Document]):
        with open(self.docs_path, "w", encoding="utf-8") as f:
            for doc in docs:
                f.write(json.dumps(doc.__dict__, ensure_ascii=False) + "\n")

    def load_documents(self) -> List[Document]:
        if not self.docs_path.exists():
            return []
        docs = []
        with open(self.docs_path, "r", encoding="utf-8") as f:
            for line in f:
                docs.append(Document(**json.loads(line)))
        return docs

    def save_chunks(self, chunks: List[Chunk]):
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk.__dict__, ensure_ascii=False) + "\n")

    def load_chunks(self) -> List[Chunk]:
        if not self.chunks_path.exists():
            return []
        chunks = []
        with open(self.chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(Chunk(**json.loads(line)))
        return chunks

    def update_state(self, state: PipelineState):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state.__dict__, f, indent=2, ensure_ascii=False)

    def get_state(self) -> PipelineState:
        if not self.state_path.exists():
            return PipelineState(current_stage="INGEST", status="PENDING", last_updated=datetime.now().isoformat())
        with open(self.state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return PipelineState(**data)
