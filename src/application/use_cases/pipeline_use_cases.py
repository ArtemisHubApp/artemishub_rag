import logging

from src.application.ports.repository import PipelineRepository
from src.application.ports.vector_store import VectorStore
from src.domain.entities import Chunk, Document
from src.index import build_index
from src.ingest import collect
from src.prepare import prepare

LOG = logging.getLogger("pipeline_use_cases")

class IngestUseCase:
    def __init__(self, repo: PipelineRepository, strict=True):
        self.repo = repo
        self.strict = strict

    def execute(self, sources):
        # collect returns a list of dicts in the original code
        docs_data = collect(sources, strict=self.strict, publish=False)
        
        docs = []
        for d in docs_data:
            # Separate known fields from unknown fields
            known_fields = {'document_id', 'source_url', 'title', 'content', 'content_sha256', 'organization'}
            main_args = {k: v for k, v in d.items() if k in known_fields}
            metadata = {k: v for k, v in d.items() if k not in known_fields}
            docs.append(Document(**main_args, metadata=metadata))
            
        self.repo.save_documents(docs)
        return docs

class PrepareUseCase:
    def __init__(self, repo: PipelineRepository):
        self.repo = repo

    def execute(self):
        docs = self.repo.load_documents()
        docs_data = []
        for d in docs:
            # Flatten metadata back into the dict for the original prepare function
            flat_doc = d.__dict__.copy()
            metadata = flat_doc.pop('metadata', {})
            flat_doc.update(metadata)
            docs_data.append(flat_doc)
            
        # prepare expects a list of documents (dicts)
        chunks_data = prepare(docs_data)
        
        chunks = []
        for c in chunks_data:
            known_fields = {'document_id', 'source_url', 'text', 'content_sha256', 'chunk_id'}
            main_args = {k: v for k, v in c.items() if k in known_fields}
            metadata = {k: v for k, v in c.items() if k not in known_fields}
            chunks.append(Chunk(**main_args, metadata=metadata))
            
        self.repo.save_chunks(chunks)
        return chunks

class IndexUseCase:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def execute(self, chunks: list[Chunk]):
        # build_index in original code might not take chunks as input, 
        # it might read from file. We need to adapt it.
        # For now, we call the original build_index.
        return build_index()
