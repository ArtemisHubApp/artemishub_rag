from abc import ABC, abstractmethod
from typing import List
from src.domain.entities import Document, Chunk, PipelineState

class PipelineRepository(ABC):
    @abstractmethod
    def save_documents(self, docs: List[Document]):
        pass

    @abstractmethod
    def load_documents(self) -> List[Document]:
        pass

    @abstractmethod
    def save_chunks(self, chunks: List[Chunk]):
        pass

    @abstractmethod
    def load_chunks(self) -> List[Chunk]:
        pass

    @abstractmethod
    def update_state(self, state: PipelineState):
        pass

    @abstractmethod
    def get_state(self) -> PipelineState:
        pass
