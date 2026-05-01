"""
Unit tests for OllamaProvider.

These tests use httpx.MockTransport to intercept HTTP calls inside the
httpx client itself. The provider's real code paths run end-to-end —
request building, header handling, response parsing, NDJSON streaming —
but no real network is involved. Fast, deterministic, no Ollama needed.

Each test installs its own mock transport with a handler that returns
canned responses. The handler can also assert on outgoing request shape
to verify the provider sends Ollama what it expects.
"""

import json

import httpx
import pytest

from app.core.exceptions import (
    ModelNotFoundError,
    OllamaError,
    OllamaTimeoutError,
    OllamaUnreachableError,
)
from app.providers.ollama_provider import OllamaProvider
from app.schemas.chat import ChatRole


def _install_mock_transport(
    provider: OllamaProvider,
    handler,
) -> None:
    """
    Replace the provider's internal httpx client with one using MockTransport.

    Tests should call this AFTER awaiting provider.start() so we know the
    real client exists and we replace it cleanly.
    """
    provider._client = httpx.AsyncClient(
        base_url=provider._base_url,
        transport=httpx.MockTransport(handler),
    )


# ---------------------------------------------------------------------------
# health_check()
# ---------------------------------------------------------------------------


class TestHealthCheck:
    async def test_returns_true_when_ollama_responds_200(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/version"
            return httpx.Response(200, json={"version": "0.3.0"})

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        assert await provider.health_check() is True

    async def test_returns_false_when_ollama_is_unreachable(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        assert await provider.health_check() is False

    async def test_returns_false_on_timeout(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow")

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        assert await provider.health_check() is False


# ---------------------------------------------------------------------------
# chat() — non-streaming
# ---------------------------------------------------------------------------


class TestChat:
    async def test_returns_assistant_content(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/chat"
            body = json.loads(request.content)
            assert body["model"] == "llama3.1:8b"
            assert body["stream"] is False
            assert body["messages"] == [{"role": "user", "content": "hi"}]
            return httpx.Response(
                200,
                json={
                    "message": {"role": "assistant", "content": "Hello there"},
                    "done": True,
                },
            )

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        result = await provider.chat(
            messages=[ChatRole(role="user", content="hi")],
            model="llama3.1:8b",
        )
        assert result == "Hello there"

    async def test_404_raises_model_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"error": "model 'foo' not found"})

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        with pytest.raises(ModelNotFoundError) as exc:
            await provider.chat(
                messages=[ChatRole(role="user", content="hi")],
                model="missing:model",
            )
        assert exc.value.model_name == "missing:model"

    async def test_500_raises_ollama_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="internal error")

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        with pytest.raises(OllamaError):
            await provider.chat(
                messages=[ChatRole(role="user", content="hi")],
                model="llama3.1:8b",
            )

    async def test_connection_error_raises_unreachable(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        with pytest.raises(OllamaUnreachableError):
            await provider.chat(
                messages=[ChatRole(role="user", content="hi")],
                model="llama3.1:8b",
            )

    async def test_read_timeout_raises_timeout(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow")

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        with pytest.raises(OllamaTimeoutError):
            await provider.chat(
                messages=[ChatRole(role="user", content="hi")],
                model="llama3.1:8b",
            )


# ---------------------------------------------------------------------------
# chat_stream() — streaming NDJSON parsing
# ---------------------------------------------------------------------------


def _ndjson_response(chunks: list[dict]) -> httpx.Response:
    """Build an httpx.Response simulating Ollama's NDJSON stream."""
    body = "\n".join(json.dumps(chunk) for chunk in chunks).encode()
    return httpx.Response(200, content=body)


class TestChatStream:
    async def test_yields_chunks_in_order(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/chat"
            body = json.loads(request.content)
            assert body["stream"] is True
            return _ndjson_response(
                [
                    {"message": {"role": "assistant", "content": "Hello"}, "done": False},
                    {"message": {"role": "assistant", "content": " "}, "done": False},
                    {"message": {"role": "assistant", "content": "world"}, "done": False},
                    {"message": {"role": "assistant", "content": ""}, "done": True},
                ]
            )

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        chunks = [
            c
            async for c in provider.chat_stream(
                messages=[ChatRole(role="user", content="hi")],
                model="llama3.1:8b",
            )
        ]

        assert chunks == ["Hello", " ", "world"]

    async def test_skips_malformed_lines(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            # Mix valid JSON with garbage to verify resilience.
            body = (
                json.dumps({"message": {"role": "assistant", "content": "good"}, "done": False})
                + "\n"
                + "this is not json\n"
                + json.dumps({"message": {"role": "assistant", "content": "more"}, "done": True})
            ).encode()
            return httpx.Response(200, content=body)

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        chunks = [
            c
            async for c in provider.chat_stream(
                messages=[ChatRole(role="user", content="hi")],
                model="llama3.1:8b",
            )
        ]

        # Malformed line is skipped; valid lines yield content.
        assert chunks == ["good", "more"]

    async def test_404_raises_model_not_found_before_streaming(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"error": "model 'x' not found"})

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        with pytest.raises(ModelNotFoundError):
            async for _ in provider.chat_stream(
                messages=[ChatRole(role="user", content="hi")],
                model="missing:model",
            ):
                pass

    async def test_connection_error_raises_unreachable(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        with pytest.raises(OllamaUnreachableError):
            async for _ in provider.chat_stream(
                messages=[ChatRole(role="user", content="hi")],
                model="llama3.1:8b",
            ):
                pass


# ---------------------------------------------------------------------------
# list_models()
# ---------------------------------------------------------------------------


class TestListModels:
    async def test_parses_model_list(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/tags"
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": "llama3.1:8b",
                            "size": 4_700_000_000,
                            "modified_at": "2026-01-01T12:34:56.123456789Z",
                        },
                        {
                            "name": "qwen2.5:7b",
                            "size": 4_400_000_000,
                            "modified_at": "2026-02-01T00:00:00.000000000Z",
                        },
                    ]
                },
            )

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        models = await provider.list_models()

        assert len(models) == 2
        assert models[0].name == "llama3.1:8b"
        assert models[0].size_bytes == 4_700_000_000
        assert models[1].name == "qwen2.5:7b"

    async def test_handles_empty_model_list(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": []})

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        assert await provider.list_models() == []

    async def test_unreachable_raises(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        provider = OllamaProvider(base_url="http://test", timeout_seconds=1.0)
        await provider.start()
        _install_mock_transport(provider, handler)

        with pytest.raises(OllamaUnreachableError):
            await provider.list_models()
