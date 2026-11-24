"""Prompts de LLM só no Langfuse: busca, variáveis, falhas e nenhum texto no código."""
import re

import httpx
import pytest

from artemis_rag import prompts
from artemis_rag.common import ROOT
from artemis_rag.prompts import PromptIndisponivel, langfuse_configurado, obter_prompt


@pytest.fixture(autouse=True)
def langfuse(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-teste")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-teste")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://langfuse.example.org")
    monkeypatch.delenv("LANGFUSE_PROMPT_LABEL", raising=False)
    prompts._baixar.cache_clear()
    yield
    prompts._baixar.cache_clear()


def _servidor(monkeypatch, status=200, corpo=None, erro=None):
    pedidos = []

    def get(url, **opcoes):
        pedidos.append((url, opcoes))
        if erro:
            raise erro
        return httpx.Response(status, json=corpo, request=httpx.Request("GET", url))

    monkeypatch.setattr(prompts.httpx, "get", get)
    return pedidos


def test_busca_pelo_label_e_troca_as_variaveis(monkeypatch):
    pedidos = _servidor(monkeypatch, corpo={"type": "text", "prompt": 'Use {{ frase }}. JSON: {"a": 1}'})
    assert obter_prompt("artemis-rag/resposta", frase="X") == 'Use X. JSON: {"a": 1}'
    url, opcoes = pedidos[0]
    assert url == "https://langfuse.example.org/api/public/v2/prompts/artemis-rag%2Fresposta"
    assert opcoes["params"] == {"label": "production"} and opcoes["auth"] == ("pk-teste", "sk-teste")


def test_guarda_em_cache(monkeypatch):
    pedidos = _servidor(monkeypatch, corpo={"type": "text", "prompt": "P"})
    obter_prompt("a")
    obter_prompt("a")
    assert len(pedidos) == 1


@pytest.mark.parametrize("opcoes", [
    {"status": 404, "corpo": {}},
    {"erro": httpx.ConnectError("sem rede")},
    {"corpo": {"type": "chat", "prompt": []}},
    {"corpo": {"type": "text", "prompt": "falta {{variavel}}"}},
])
def test_falha_vira_prompt_indisponivel(monkeypatch, opcoes):
    _servidor(monkeypatch, **opcoes)
    with pytest.raises(PromptIndisponivel):
        obter_prompt("a")


def test_sem_chaves_nao_esta_configurado(monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY")
    assert langfuse_configurado() is False
    with pytest.raises(PromptIndisponivel, match="LANGFUSE"):
        obter_prompt("a")


def test_base_url_precisa_de_https(monkeypatch):
    monkeypatch.setenv("LANGFUSE_BASE_URL", "http://langfuse.example.org")
    with pytest.raises(PromptIndisponivel, match="HTTPS"):
        obter_prompt("a")


def test_nenhum_texto_de_prompt_no_codigo():
    padrao = re.compile(r"Você orienta|avaliador rigoroso|usando SOMENTE o contexto|raciocine passo a passo\.")
    for pasta in ("artemis_rag", "scripts"):
        for arquivo in (ROOT / pasta).rglob("*.py"):
            assert not padrao.search(arquivo.read_text(encoding="utf-8")), arquivo.name
