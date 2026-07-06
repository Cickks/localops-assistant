"""
Unit tests for ChatService.

Tests the service in isolation against a fake provider. No HTTP, no Ollama,
no FastAPI. Just verifying the service does what it's supposed to:
- Resolves model from request override → settings default
- Builds the message list correctly (with/without system prompt)
- Times the request
- Propagates provider exceptions cleanly
"""

import pytest

from app.core.exceptions import (
    ModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnreachableError,
)
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService
from tests.conftest import FakeOllamaProvider


class TestChatServiceNonStreaming:
    """Tests for ChatService.chat()."""

    async def test_returns_response_with_provider_reply(
        self, fake_ollama: FakeOllamaProvider
    ) -> None:
        fake_ollama.canned_chat_response = "Hello, LocalOps"
        service = ChatService(ollama=fake_ollama)

        result = await service.chat(ChatRequest(message="hi"))

        assert result.message == "Hello, LocalOps"
        assert result.duration_ms >= 0
        assert result.conversation_id is None  # Phase 2 will set this

    async def test_uses_default_model_when_request_omits_it(
        self, fake_ollama: FakeOllamaProvider
    ) -> None:
        service = ChatService(ollama=fake_ollama)

        await service.chat(ChatRequest(message="hi"))

        # The provider was called with the default model from settings
        called_with = fake_ollama.calls_chat[0]
        assert called_with["model"] == "llama3.1:8b"

    async def test_uses_request_model_override(self, fake_ollama: FakeOllamaProvider) -> None:
        service = ChatService(ollama=fake_ollama)

        await service.chat(ChatRequest(message="hi", model="qwen2.5:7b"))

        called_with = fake_ollama.calls_chat[0]
        assert called_with["model"] == "qwen2.5:7b"

    async def test_includes_system_prompt_when_provided(
        self, fake_ollama: FakeOllamaProvider
    ) -> None:
        service = ChatService(ollama=fake_ollama)

        await service.chat(ChatRequest(message="hi", system_prompt="You are a helpful assistant."))

        messages = fake_ollama.calls_chat[0]["messages"]
        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[0].content == "You are a helpful assistant."
        assert messages[1].role == "user"
        assert messages[1].content == "hi"

    async def test_omits_system_prompt_when_not_provided(
        self, fake_ollama: FakeOllamaProvider
    ) -> None:
        service = ChatService(ollama=fake_ollama)

        await service.chat(ChatRequest(message="hi"))

        messages = fake_ollama.calls_chat[0]["messages"]
        assert len(messages) == 1
        assert messages[0].role == "user"

    async def test_propagates_model_not_found(self, fake_ollama: FakeOllamaProvider) -> None:
        fake_ollama.raise_on_chat = ModelNotFoundError("nonexistent:model")
        service = ChatService(ollama=fake_ollama)

        with pytest.raises(ModelNotFoundError) as exc_info:
            await service.chat(ChatRequest(message="hi", model="nonexistent:model"))

        assert "nonexistent:model" in str(exc_info.value)

    async def test_propagates_unreachable(self, fake_ollama: FakeOllamaProvider) -> None:
        fake_ollama.raise_on_chat = OllamaUnreachableError("Connection refused")
        service = ChatService(ollama=fake_ollama)

        with pytest.raises(OllamaUnreachableError):
            await service.chat(ChatRequest(message="hi"))

    async def test_propagates_timeout(self, fake_ollama: FakeOllamaProvider) -> None:
        fake_ollama.raise_on_chat = OllamaTimeoutError("Took too long")
        service = ChatService(ollama=fake_ollama)

        with pytest.raises(OllamaTimeoutError):
            await service.chat(ChatRequest(message="hi"))


class TestChatServiceStreaming:
    """Tests for ChatService.chat_stream()."""

    async def test_yields_all_chunks_from_provider(self, fake_ollama: FakeOllamaProvider) -> None:
        fake_ollama.canned_chunks = ["Hello", " ", "world", "!"]
        service = ChatService(ollama=fake_ollama)

        chunks = [c async for c in service.chat_stream(ChatRequest(message="hi"))]

        assert chunks == ["Hello", " ", "world", "!"]

    async def test_uses_request_model_override_in_stream(
        self, fake_ollama: FakeOllamaProvider
    ) -> None:
        service = ChatService(ollama=fake_ollama)

        async for _ in service.chat_stream(ChatRequest(message="hi", model="qwen2.5:7b")):
            pass

        assert fake_ollama.calls_stream[0]["model"] == "qwen2.5:7b"

    async def test_propagates_model_not_found_in_stream(
        self, fake_ollama: FakeOllamaProvider
    ) -> None:
        fake_ollama.raise_on_stream = ModelNotFoundError("missing:model")
        service = ChatService(ollama=fake_ollama)

        with pytest.raises(ModelNotFoundError):
            async for _ in service.chat_stream(ChatRequest(message="hi")):
                pass
