import httpx
import pytest

from src import llm_client
from src.llm_client import chamar_chat, configuracao_llm


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "chave")
    monkeypatch.setenv("LLM_MODEL", "modelo")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.setattr(llm_client.time, "sleep", lambda s: None)


def resposta(status, texto="ok"):
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return httpx.Response(status, request=req, json={"choices": [{"message": {"content": texto}}]})


def sequencia(*itens):
    itens = list(itens)
    chamadas = []

    def post(*args, **kwargs):
        chamadas.append(kwargs)
        item = itens.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
    return post, chamadas


def test_sem_base_url_usa_openai_por_padrao():
    assert configuracao_llm()[0] == "https://api.openai.com/v1"


def test_sem_chave_falha_com_mensagem_clara(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY")
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        configuracao_llm()


def test_modelo_explicito_tem_prioridade():
    assert configuracao_llm("juiz")[2] == "juiz"


@pytest.mark.parametrize("falha", [
    resposta(429), resposta(503), httpx.ConnectError("caiu"), httpx.ReadTimeout("lento"),
])
def test_tenta_de_novo_em_falha_temporaria(falha):
    post, chamadas = sequencia(falha, resposta(200, "deu certo"))
    assert chamar_chat("s", "u", post=post) == "deu certo"
    assert len(chamadas) == 2


def test_nao_repete_erro_definitivo():
    post, chamadas = sequencia(resposta(401), resposta(200))
    with pytest.raises(httpx.HTTPStatusError):
        chamar_chat("s", "u", post=post)
    assert len(chamadas) == 1


def test_desiste_depois_das_tentativas():
    post, chamadas = sequencia(resposta(500), resposta(500), resposta(500))
    with pytest.raises(httpx.HTTPStatusError):
        chamar_chat("s", "u", post=post, tentativas=3)
    assert len(chamadas) == 3
