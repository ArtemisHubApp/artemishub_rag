from abc import ABC, abstractmethod

from artemis_rag.domain.entities import Chunk


class VectorStore(ABC):
    @abstractmethod
    def index_chunks(self, chunks: list[Chunk]) -> bool:
        pass
