
from artemis_rag.application.ports.vector_store import VectorStore
from artemis_rag.domain.entities import Chunk
from artemis_rag.index import build_index


class SimpleVectorStoreAdapter(VectorStore):
    def index_chunks(self, chunks: list[Chunk]) -> bool:
        # In the current project, build_index handles its own data loading.
        # We wrap it here to follow the port interface.
        return build_index() is not None
