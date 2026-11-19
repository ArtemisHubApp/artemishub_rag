"""RAG do Artemis: busca com citações sobre a base de conhecimento. Interface pública em `artemis_rag.api`."""
from artemis_rag.api import Evidencia, buscar, gerar, validar_citacoes
from artemis_rag.index import IndiceIndisponivel
from artemis_rag.query import ABSTENTION, CitationValidationError

__all__ = [
    "ABSTENTION",
    "CitationValidationError",
    "Evidencia",
    "IndiceIndisponivel",
    "buscar",
    "gerar",
    "validar_citacoes",
]
