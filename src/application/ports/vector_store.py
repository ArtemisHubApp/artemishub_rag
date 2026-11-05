from abc import ABC, abstractmethod
from typing import List
from src.domain.entities import Chunk

class VectorStore(ABC):
    @abstractmethod
    def index_chunks(self, chunks: List[Chunk]) -> bool:
        pass
