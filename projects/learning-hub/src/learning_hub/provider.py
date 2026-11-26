"""Official SDK transport; defaults cannot spend money or send to a remote host."""

import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import httpx
from openai import AsyncOpenAI


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    base_url: str
    model: str
    api_key: str = field(repr=False)

    @classmethod
    def from_env(cls):
        provider = os.getenv("AI_PROVIDER", "ollama")
        if provider == "ollama":
            url = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
            if urlparse(url).hostname not in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("Локальный профиль допускает только loopback")
            return cls(provider, url, os.getenv("LLM_MODEL", "qwen2.5-coder:7b"), "ollama")
        if provider != "openai" or os.getenv("AI_ALLOW_CLOUD") != "1":
            raise ValueError("Облачный профиль требует AI_ALLOW_CLOUD=1 и согласованного бюджета")
        try:
            budget = Decimal(os.getenv("AI_PAID_BUDGET_USD", "0"))
        except InvalidOperation as exc:
            raise ValueError("Нужен согласованный числовой бюджет AI_PAID_BUDGET_USD") from exc
        if not budget.is_finite() or budget <= 0:
            raise ValueError("Нужен согласованный положительный бюджет AI_PAID_BUDGET_USD")
        key, model = os.getenv("OPENAI_API_KEY"), os.getenv("LLM_MODEL")
        if not key or not model:
            raise ValueError("Нужны OPENAI_API_KEY и явно выбранная LLM_MODEL")
        url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        if urlparse(url).scheme != "https" or urlparse(url).hostname != "api.openai.com":
            raise ValueError("OpenAI-профиль допускает только официальный HTTPS endpoint")
        return cls(provider, url, model, key)


async def provider_smoke(config: ProviderConfig, http_client=None) -> dict:
    # No redirects/proxy inheritance can silently turn local inference into remote traffic.
    transport = http_client or httpx.AsyncClient(follow_redirects=False, trust_env=False, timeout=60)
    transport.follow_redirects = False
    async with AsyncOpenAI(
        api_key=config.api_key, base_url=config.base_url, timeout=60, max_retries=0, http_client=transport
    ) as client:
        response = await client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": "Reply with the single word OK."}],
            max_tokens=8,
            temperature=0,
        )
    if not response.choices or response.choices[0].message.content is None:
        raise ValueError("Нет текстового ответа провайдера")
    return {
        "provider": config.provider,
        "model": response.model,
        "text": response.choices[0].message.content,
        "usage": response.usage.model_dump() if response.usage else None,
        "learner_evidence": False,
    }
