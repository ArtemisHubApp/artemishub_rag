"""Prompts de LLM guardados no Langfuse. O texto não fica no repositório, que é público."""
import os
import re
from functools import lru_cache
from urllib.parse import quote

import httpx

_VARIAVEL = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class PromptIndisponivel(RuntimeError):
    """Langfuse sem configuração, fora do ar ou sem o prompt pedido."""


def langfuse_configurado() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def obter_prompt(nome: str, **variaveis: str) -> str:
    """Prompt de texto pelo label `LANGFUSE_PROMPT_LABEL` (padrão `production`), com as variáveis trocadas."""
    if not langfuse_configurado():
        raise PromptIndisponivel("Defina LANGFUSE_PUBLIC_KEY e LANGFUSE_SECRET_KEY no .env.")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
    if not base_url.startswith("https://"):
        raise PromptIndisponivel("LANGFUSE_BASE_URL precisa usar HTTPS.")
    texto = _baixar(nome, os.getenv("LANGFUSE_PROMPT_LABEL") or "production", base_url)
    faltando = set(_VARIAVEL.findall(texto)) - variaveis.keys()
    if faltando:
        raise PromptIndisponivel(f"Prompt {nome}: variáveis sem valor: {', '.join(sorted(faltando))}.")
    return _VARIAVEL.sub(lambda achado: variaveis[achado.group(1)], texto)


@lru_cache(maxsize=16)
def _baixar(nome: str, label: str, base_url: str) -> str:
    try:
        resposta = httpx.get(f"{base_url}/api/public/v2/prompts/{quote(nome, safe='')}", params={"label": label},
                             auth=(os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"]), timeout=20)
        resposta.raise_for_status()
        dados = resposta.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise PromptIndisponivel(f"Prompt {nome} indisponível no Langfuse ({type(exc).__name__}).") from exc
    if dados.get("type") != "text" or not isinstance(dados.get("prompt"), str):
        raise PromptIndisponivel(f"Prompt {nome} não é do tipo text.")
    return dados["prompt"]
