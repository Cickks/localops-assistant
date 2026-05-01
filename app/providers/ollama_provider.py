"""
Ollama HTTP provider.

This is the ONLY module that talks to Ollama. The rest of the codebase
goes through this class. If we ever swap LLM backends (vLLM, OpenAI,
local llama.cpp), only this file changes.

Async HTTP via httpx. Errors are translated to typed exceptions so the
service layer can handle them cleanly.
"""

from datetime import datetime
from typing import Any

import httpx
import structlog

from app.core.exceptions import (
    ModelNotFoundError,
    OllamaError,
    OllamaTimeoutError,
    OllamaUnreachableError,
)
from app.schemas.chat import ChatRole, ModelInfo

logger = structlog.get_logger(__name__)


class OllamaProvider:
    """
    Async client for the Ollama HTTP API.

    Lifecycle:
        Created once at app startup, used across requests, closed at shutdown.
        Reusing one httpx.AsyncClient is critical for connection pooling —
        creating a new client per request kills performance.
    """

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Open the underlying HTTP client. Call once at app startup."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        )
        logger.info("ollama_provider_started", base_url=self._base_url)

    async def stop(self) -> None:
        """Close the underlying HTTP client. Call once at app shutdown."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("ollama_provider_stopped")

    @property
    def _http(self) -> httpx.AsyncClient:
        """Internal accessor that asserts the client is started."""
        if self._client is None:
            raise OllamaError("OllamaProvider used before start() was called")
        return self._client

    async def health_check(self) -> bool:
        """
        Lightweight check that Ollama is reachable.

        Returns True if Ollama responds to /api/version, False otherwise.
        Used by the /ready endpoint.
        """
        try:
            response = await self._http.get("/api/version", timeout=5.0)
            return response.status_code == 200
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
            return False

    async def list_models(self) -> list[ModelInfo]:
        """
        List models installed in Ollama.

        Calls Ollama's /api/tags endpoint.
        """
        try:
            response = await self._http.get("/api/tags")
            response.raise_for_status()
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise OllamaUnreachableError(f"Cannot reach Ollama at {self._base_url}") from e
        except httpx.ReadTimeout as e:
            raise OllamaTimeoutError("Ollama timed out listing models") from e
        except httpx.HTTPStatusError as e:
            raise OllamaError(f"Ollama returned {e.response.status_code}") from e

        payload = response.json()
        models: list[ModelInfo] = []
        for raw in payload.get("models", []):
            models.append(
                ModelInfo(
                    name=raw["name"],
                    size_bytes=raw.get("size", 0),
                    modified_at=_parse_ollama_timestamp(raw["modified_at"]),
                )
            )
        return models

    async def chat(
        self,
        messages: list[ChatRole],
        model: str,
    ) -> str:
        """
        Send a chat-style request to Ollama and return the assistant's reply.

        Uses Ollama's /api/chat endpoint, which supports system/user/assistant
        message lists. We use stream=False here for simplicity; streaming
        will be a separate method added in Phase 1 Part 3.
        """
        body: dict[str, Any] = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
        }

        logger.debug("ollama_chat_request", model=model, message_count=len(messages))

        try:
            response = await self._http.post("/api/chat", json=body)
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise OllamaUnreachableError(f"Cannot reach Ollama at {self._base_url}") from e
        except httpx.ReadTimeout as e:
            raise OllamaTimeoutError(
                f"Ollama timed out (>{self._timeout}s). "
                f"Try a smaller model or raise OLLAMA_TIMEOUT_SECONDS."
            ) from e

        if response.status_code == 404:
            # Ollama returns 404 with a body like {"error": "model 'foo' not found"}
            raise ModelNotFoundError(model)
        if response.status_code >= 400:
            raise OllamaError(f"Ollama returned {response.status_code}: {response.text[:300]}")

        payload = response.json()
        # /api/chat response shape: {"message": {"role": "assistant", "content": "..."}, ...}
        return payload["message"]["content"]


def _parse_ollama_timestamp(raw: str) -> datetime:
    """
    Parse Ollama's RFC 3339 timestamp.

    Ollama returns timestamps with nanosecond precision and timezone offset,
    e.g., "2026-04-30T22:45:01.123456789Z". Python's fromisoformat handles
    most of this in 3.11+, but truncate nanoseconds to microseconds first.
    """
    # Replace trailing 'Z' with '+00:00' for fromisoformat
    cleaned = raw.replace("Z", "+00:00")
    # Truncate fractional seconds beyond microsecond precision
    if "." in cleaned:
        head, tail = cleaned.split(".", 1)
        # tail looks like "123456789+00:00" — keep first 6 digits of fraction
        frac, _, tz = tail.partition("+")
        cleaned = f"{head}.{frac[:6]}+{tz}"
    return datetime.fromisoformat(cleaned)
