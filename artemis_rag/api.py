"""Interface pública e estável do RAG para outros pacotes (o artemishub_agents), sem passar pela CLI."""
import json
from dataclasses import dataclass
from pathlib import Path

from artemis_rag.query import Retriever, generate, validate_citations


@dataclass(frozen=True)
class Evidencia:
    """Trecho recuperado; `id` é "FONTE N" na ordem do ranking, o rótulo que a resposta cita."""

    id: str
    titulo: str
    url: str
    pagina: str | None
    artigo: str | None
    texto: str
    distancia: float
    # Procedência que o `generate` já envia ao LLM; opcional para quem monta Evidencia à mão.
    publicador: str | None = None
    versao: str | None = None
    url_primaria: str | None = None
    alternativa_usada: bool = False


def buscar(pergunta: str, top_k: int = 5, indice: Path | None = None, parcial: bool = False) -> list[Evidencia]:
    """Busca híbrida (vetorial + BM25) no índice publicado, sem LLM.

    O índice vem de `indice`, senão de $ARTEMIS_RAG_INDEX_DIR, senão do `.chroma` do repo.
    Levanta `IndiceIndisponivel` se não houver índice publicado (ou só um parcial sem `parcial=True`).
    """
    hits = Retriever(path=indice, allow_partial=parcial).retrieve(pergunta, top_k)
    return [_evidencia(posicao, hit) for posicao, hit in enumerate(hits, 1)]


def validar_citacoes(resposta: str, evidencias: list[Evidencia]) -> list[int]:
    """Números de FONTE citados (ordenados, sem repetição); `[]` para a abstenção.

    Confere só a validade referencial. Levanta `CitationValidationError` se a resposta citar fonte
    inexistente, tiver rótulo malformado ou parágrafo sem citação.
    """
    return validate_citations(resposta, evidencias)


def gerar(pergunta: str, evidencias: list[Evidencia]) -> str | None:
    """Resposta do LLM com citações já validadas; `ABSTENTION` sem evidências; `None` sem LLM configurado.

    Usa LLM_API_KEY, LLM_MODEL e LLM_BASE_URL do ambiente. Pode levantar `CitationValidationError`
    e erros de `httpx`.
    """
    return generate(pergunta, [_hit(evidencia) for evidencia in evidencias])


def _evidencia(posicao: int, hit: dict) -> Evidencia:
    meta = hit["metadata"]
    procedencia = meta.get("metadata") or {}
    if isinstance(procedencia, str):
        procedencia = json.loads(procedencia)
    return Evidencia(
        id=f"FONTE {posicao}", titulo=meta.get("title"), url=meta.get("source_url"),
        pagina=meta.get("page") or None, artigo=procedencia.get("article"), texto=hit["text"],
        distancia=float(hit["distance"]), publicador=procedencia.get("publisher"),
        versao=procedencia.get("version"), url_primaria=procedencia.get("primary_url"),
        alternativa_usada=procedencia.get("alternative_used", False),
    )


def _hit(evidencia: Evidencia) -> dict:
    """Volta ao formato do Retriever para que o contexto enviado ao LLM seja o mesmo da CLI."""
    procedencia = {"article": evidencia.artigo, "publisher": evidencia.publicador, "version": evidencia.versao,
                   "primary_url": evidencia.url_primaria, "alternative_used": evidencia.alternativa_usada}
    # O Chroma guarda página ausente como "", e é isso que a CLI envia ao LLM.
    metadata = {"title": evidencia.titulo, "source_url": evidencia.url, "page": evidencia.pagina or "",
                "metadata": procedencia}
    return {"text": evidencia.texto, "metadata": metadata, "distance": evidencia.distancia}
