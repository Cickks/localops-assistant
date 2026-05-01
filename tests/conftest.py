"""
Shared pytest fixtures.

Anything defined here is automatically available to every test in tests/.
We keep test data factories and fakes here to avoid duplication across files.
"""

from datetime import UTC, datetime
from typing import Any

import pytest

from app.providers.ollama_provider import OllamaProvider
from app.schemas.chat import ChatRole, ModelInfo


class FakeOllamaProvider(OllamaProvider):
    """
    Test double for OllamaProvider.

    Inherits from OllamaProvider so it satisfies type checks anywhere a real
    provider is expected. Overrides every method to return canned responses
    or raise canned exceptions, controlled per-test by setting attributes
    before use.

    Usage in a test:
        fake = FakeOllamaProvider()
        fake.canned_chat_response = "Hello, world"
        result = await some_code_that_uses_provider(fake)
        assert result == "Hello, world"
    """

    def __init__(self) -> None:
        # Don't call super().__init__ — we don't want a real httpx client.
        self._base_url = "http://fake"
        self._timeout = 1.0
        self._client = None  # never used

        # Test-controllable attributes (set these in tests):
        self.canned_chat_response: str = "fake response"
        self.canned_chunks: list[str] = ["fake ", "response"]
        self.canned_models: list[ModelInfo] = []
        self.canned_health: bool = True
        self.raise_on_chat: Exception | None = None
        self.raise_on_stream: Exception | None = None
        self.raise_on_list: Exception | None = None

        # Recording — tests can inspect what was called:
        self.calls_chat: list[dict[str, Any]] = []
        self.calls_stream: list[dict[str, Any]] = []

    async def start(self) -> None:  # type: ignore[override]
        return None

    async def stop(self) -> None:  # type: ignore[override]
        return None

    async def health_check(self) -> bool:  # type: ignore[override]
        return self.canned_health

    async def list_models(self) -> list[ModelInfo]:  # type: ignore[override]
        if self.raise_on_list is not None:
            raise self.raise_on_list
        return self.canned_models

    async def chat(self, messages: list[ChatRole], model: str) -> str:  # type: ignore[override]
        self.calls_chat.append({"messages": messages, "model": model})
        if self.raise_on_chat is not None:
            raise self.raise_on_chat
        return self.canned_chat_response

    async def chat_stream(self, messages: list[ChatRole], model: str):  # type: ignore[override]
        self.calls_stream.append({"messages": messages, "model": model})
        if self.raise_on_stream is not None:
            raise self.raise_on_stream
        for chunk in self.canned_chunks:
            yield chunk


@pytest.fixture
def fake_ollama() -> FakeOllamaProvider:
    """A fresh fake provider for each test."""
    return FakeOllamaProvider()


@pytest.fixture
def sample_model_info() -> ModelInfo:
    """A sample ModelInfo for tests that need one."""
    return ModelInfo(
        name="llama3.1:8b",
        size_bytes=4_700_000_000,
        modified_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
