"""API pública usada pelo artemishub_agents: índice local de teste, encoder determinístico, sem rede."""
import dataclasses
import json

import httpx
import numpy as np
import pytest

from artemis_rag import (
    ABSTENTION,
    CitationValidationError,
    Evidencia,
    IndiceIndisponivel,
    buscar,
    gerar,
    query,
    validar_citacoes,
)
from artemis_rag.index import INDEX_DIR_ENV, build_index
from artemis_rag.prepare import prepare
from artemis_rag.query import Retriever, generate

MODELO = "local-fixture"
PERGUNTA = "igualdade salarial"


class LocalEncoder:
    def encode(self, texts, normalize_embeddings=True):
        vectors = np.array([[text.lower().count("salarial") + 1, text.lower().count("carreira") + 1,
                             text.lower().count("transparência") + 1] for text in texts], dtype=np.float32)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    monkeypatch.setenv("EMBEDDING_MODEL", MODELO)
    monkeypatch.delenv("EMBEDDING_REVISION", raising=False)
    monkeypatch.delenv(INDEX_DIR_ENV, raising=False)
    monkeypatch.setattr(query, "load_model", lambda *args, **kwargs: LocalEncoder())


@pytest.fixture
def documento(document):
    return {**document, "page": 3, "metadata": {"page": 3, "article": "461", "publisher": "Fixture",
                                                "version": "Original", "primary_url": "https://primary.example.org",
                                                "alternative_used": True}}


def publicar(path, documento, partial=False):
    chunks = prepare([documento], chunk_size=150, overlap=20)
    build_index(chunks, [documento], path=path, model=LocalEncoder(), model_name=MODELO, partial=partial)
    return path


@pytest.fixture
def indice(tmp_path, documento):
    return publicar(tmp_path / "indice", documento)


def test_buscar_devolve_evidencias_rotuladas_na_ordem_do_ranking(indice, documento):
    evidencias = buscar(PERGUNTA, top_k=3, indice=indice)
    assert evidencias and all(isinstance(e, Evidencia) for e in evidencias)
    assert [e.id for e in evidencias] == [f"FONTE {i}" for i in range(1, len(evidencias) + 1)]
    primeira = evidencias[0]
    assert primeira.titulo == documento["title"] and primeira.url == documento["source_url"]
    assert primeira.pagina == "3" and primeira.artigo == "461"
    assert primeira.texto and isinstance(primeira.distancia, float)
    assert primeira.versao == "Original" and primeira.alternativa_usada is True


def test_buscar_reproduz_o_retriever_hibrido(indice):
    hits = Retriever(path=indice, model=LocalEncoder(), model_name=MODELO).retrieve(PERGUNTA, 3)
    evidencias = buscar(PERGUNTA, top_k=3, indice=indice)
    assert [e.texto for e in evidencias] == [h["text"] for h in hits]
    assert [e.distancia for e in evidencias] == pytest.approx([h["distance"] for h in hits])


def test_evidencia_e_imutavel(indice):
    with pytest.raises(dataclasses.FrozenInstanceError):
        buscar(PERGUNTA, indice=indice)[0].texto = "outro"


def test_pagina_ausente_vira_none(tmp_path, document):
    evidencia = buscar(PERGUNTA, indice=publicar(tmp_path / "sem_pagina", document))[0]
    assert evidencia.pagina is None and evidencia.artigo is None


def test_indice_vem_da_variavel_de_ambiente(indice, monkeypatch):
    monkeypatch.setenv(INDEX_DIR_ENV, str(indice))
    assert buscar(PERGUNTA)[0].id == "FONTE 1"


def test_parametro_explicito_vence_a_variavel(indice, tmp_path, monkeypatch):
    monkeypatch.setenv(INDEX_DIR_ENV, str(tmp_path / "vazio"))
    assert buscar(PERGUNTA, indice=indice)
    with pytest.raises(IndiceIndisponivel):
        buscar(PERGUNTA)


def test_pipeline_publica_no_diretorio_da_variavel(tmp_path, documento, monkeypatch):
    destino = tmp_path / "publicado"
    monkeypatch.setenv(INDEX_DIR_ENV, str(destino))
    build_index(prepare([documento]), [documento], model=LocalEncoder(), model_name=MODELO)
    assert (destino / "active.json").exists()


def test_sem_indice_publicado_levanta_indice_indisponivel(tmp_path):
    with pytest.raises(IndiceIndisponivel, match=r"No published index\. Run python -m artemis_rag\.pipeline first\."):
        buscar(PERGUNTA, indice=tmp_path)
    assert issubclass(IndiceIndisponivel, ValueError)


def test_indice_parcial_exige_opt_in(tmp_path, documento):
    publicar(tmp_path, documento, partial=True)
    with pytest.raises(IndiceIndisponivel, match="partial"):
        buscar(PERGUNTA, indice=tmp_path)
    assert buscar(PERGUNTA, indice=tmp_path, parcial=True)


def test_validar_citacoes(indice):
    evidencias = buscar(PERGUNTA, top_k=2, indice=indice)
    assert validar_citacoes("Afirmação [FONTE 2] [FONTE 1]", evidencias) == [1, 2]
    assert validar_citacoes(ABSTENTION, evidencias) == []
    with pytest.raises(CitationValidationError):
        validar_citacoes(f"Afirmação [FONTE {len(evidencias) + 1}]", evidencias)


def _llm_simulado(monkeypatch, enviados, resposta="Resposta simulada [FONTE 1]"):
    monkeypatch.setenv("LLM_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("LLM_MODEL", "simulated-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.org/v1")
    real_client = httpx.Client

    def handler(request):
        enviados.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": resposta}}]})

    monkeypatch.setattr(query.httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))


def test_gerar_envia_ao_llm_o_mesmo_contexto_do_generate(indice, monkeypatch):
    enviados = []
    _llm_simulado(monkeypatch, enviados)
    hits = Retriever(path=indice, model=LocalEncoder(), model_name=MODELO).retrieve(PERGUNTA, 3)
    assert generate(PERGUNTA, hits) == "Resposta simulada [FONTE 1]"
    assert gerar(PERGUNTA, buscar(PERGUNTA, top_k=3, indice=indice)) == "Resposta simulada [FONTE 1]"
    assert enviados[0] == enviados[1]


def test_gerar_sem_llm_ou_sem_evidencia(indice, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    assert gerar(PERGUNTA, buscar(PERGUNTA, indice=indice)) is None
    assert gerar(PERGUNTA, []) == ABSTENTION
