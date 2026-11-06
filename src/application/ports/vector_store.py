from abc import ABC, abstractmethod

from src.domain.entities import Chunk


class VectorStore(ABC):
    @abstractmethod
    def index_chunks(self, chunks: list[Chunk]) -> bool:
        pass
