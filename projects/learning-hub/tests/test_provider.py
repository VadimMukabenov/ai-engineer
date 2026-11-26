import httpx
import pytest

from learning_hub.provider import ProviderConfig, provider_smoke


def test_local_profile_defaults_to_installed_ollama_model(monkeypatch):
    for name in ["AI_PROVIDER", "LLM_BASE_URL", "LLM_MODEL", "AI_ALLOW_CLOUD"]:
        monkeypatch.delenv(name, raising=False)
    c = ProviderConfig.from_env()
    assert c.base_url == "http://127.0.0.1:11434/v1"
    assert c.model == "qwen2.5-coder:7b"


def test_cloud_requires_explicit_opt_in_and_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.delenv("AI_ALLOW_CLOUD", raising=False)
    with pytest.raises(ValueError):
        ProviderConfig.from_env()
    monkeypatch.setenv("AI_ALLOW_CLOUD", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ProviderConfig.from_env()


@pytest.mark.asyncio
async def test_official_sdk_reads_openai_compatible_response():
    def endpoint(request):
        return httpx.Response(
            200,
            json={
                "id": "test",
                "object": "chat.completion",
                "created": 0,
                "model": "local-test",
                "choices": [
                    {"index": 0, "message": {"role": "assistant", "content": "OK"}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(endpoint)) as transport:
        result = await provider_smoke(
            ProviderConfig("ollama", "http://127.0.0.1:11434/v1", "local-test", "ollama"), transport
        )
    assert result["text"] == "OK"
    assert result["usage"]["total_tokens"] == 4


def test_local_profile_cannot_silently_send_to_remote(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    with pytest.raises(ValueError):
        ProviderConfig.from_env()


@pytest.mark.asyncio
async def test_local_sdk_never_follows_redirect_to_remote():
    contacted = []

    def endpoint(request):
        contacted.append(request.url.host)
        return httpx.Response(307, headers={"location": "https://remote.example/v1/chat/completions"})

    from openai import APIStatusError

    async with httpx.AsyncClient(transport=httpx.MockTransport(endpoint), follow_redirects=True) as transport:
        with pytest.raises(APIStatusError):
            await provider_smoke(
                ProviderConfig("ollama", "http://127.0.0.1:11434/v1", "test", "ollama"), transport
            )
    assert contacted == ["127.0.0.1"]


def test_cloud_key_and_flag_without_budget_still_cannot_spend(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_ALLOW_CLOUD", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-placeholder")
    monkeypatch.setenv("LLM_MODEL", "explicit-cloud-model")
    monkeypatch.delenv("AI_PAID_BUDGET_USD", raising=False)
    with pytest.raises(ValueError, match="бюджет"):
        ProviderConfig.from_env()
    monkeypatch.setenv("AI_PAID_BUDGET_USD", "5")
    assert ProviderConfig.from_env().provider == "openai"
