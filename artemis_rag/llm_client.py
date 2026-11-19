"""Cliente mínimo de Chat Completions usado pelos scripts de comparação e do juiz."""
import os
import time

import httpx

# Falhas transitórias: vale esperar e tentar de novo em vez de registrar erro.
ERROS_DE_REDE = (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError)


def configuracao_llm(modelo=None):
    """Lê e valida as variáveis do .env. Chame no início do script para falhar cedo."""
    chave = os.getenv("LLM_API_KEY")
    modelo = modelo or os.getenv("LLM_MODEL")
    if not chave or not modelo:
        raise RuntimeError("Defina LLM_API_KEY e LLM_MODEL no .env.")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    if not base_url.startswith("https://"):
        raise ValueError("LLM_BASE_URL precisa usar HTTPS.")
    return base_url, chave, modelo


def temporaria(exc):
    """429, 5xx e erros de rede são temporários; o resto (400, 401...) não adianta repetir."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status == 429 or status >= 500
    return isinstance(exc, ERROS_DE_REDE)


def chamar_chat(sistema, usuario, modelo=None, tentativas=3, espera=10, post=None):
    """Chama o endpoint e devolve o texto da resposta, tentando de novo nas falhas temporárias."""
    base_url, chave, modelo = configuracao_llm(modelo)
    payload = {"model": modelo, "temperature": 0, "messages": [
        {"role": "system", "content": sistema},
        {"role": "user", "content": usuario},
    ]}
    post = post or httpx.post
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = post(f"{base_url}/chat/completions", json=payload,
                            headers={"Authorization": f"Bearer {chave}"}, timeout=90)
            resposta.raise_for_status()
            return resposta.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPStatusError, *ERROS_DE_REDE) as exc:
            if not temporaria(exc) or tentativa == tentativas:
                raise
            time.sleep(espera * tentativa)
