from abc import ABC, abstractmethod

from src.domain.entities import Chunk, Document, PipelineState


class PipelineRepository(ABC):
    @abstractmethod
    def save_documents(self, docs: list[Document]):
        pass

    @abstractmethod
    def load_documents(self) -> list[Document]:
        pass

    @abstractmethod
    def save_chunks(self, chunks: list[Chunk]):
        pass

    @abstractmethod
    def load_chunks(self) -> list[Chunk]:
        pass

    @abstractmethod
    def update_state(self, state: PipelineState):
        pass

    @abstractmethod
    def get_state(self) -> PipelineState:
        pass
