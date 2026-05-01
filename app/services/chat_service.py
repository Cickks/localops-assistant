"""
Chat service — the business logic layer for chat operations.

Responsibilities:
    - Decide which model to use (request override → default)
    - Build the message list (system prompt + user message)
    - Time the request
    - Delegate the actual LLM call to OllamaProvider

This layer does NOT know about HTTP, FastAPI, or Pydantic schemas
beyond the chat domain. It could be invoked from a CLI, a queue
worker, or a test — and it would still work.
"""

import time
from collections.abc import AsyncIterator

import structlog

from app.core.config import settings
from app.providers.ollama_provider import OllamaProvider
from app.schemas.chat import ChatRequest, ChatResponse, ChatRole, ModelsResponse

logger = structlog.get_logger(__name__)


class ChatService:
    """Orchestrates chat interactions between clients and Ollama."""

    def __init__(self, ollama: OllamaProvider) -> None:
        self._ollama = ollama

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Handle a single non-streaming chat request.

        Resolves the model, builds the message list, calls Ollama,
        and packages the response with timing info.
        """
        model = request.model or settings.ollama_default_model
        messages = self._build_messages(request)

        logger.info(
            "chat_request_received",
            model=model,
            has_system_prompt=request.system_prompt is not None,
            message_length=len(request.message),
        )

        start = time.perf_counter()
        reply = await self._ollama.chat(messages=messages, model=model)
        duration_ms = int((time.perf_counter() - start) * 1000)

        logger.info(
            "chat_request_completed",
            model=model,
            duration_ms=duration_ms,
            reply_length=len(reply),
        )

        return ChatResponse(
            conversation_id=None,  # Phase 2 will populate this
            message=reply,
            model=model,
            duration_ms=duration_ms,
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """
        Handle a streaming chat request, yielding text chunks as they arrive.

        Returns an async iterator of plain text chunks. The route layer is
        responsible for wrapping these chunks in the SSE wire format —
        keeping protocol concerns out of the service layer.

        Token timing is logged at start and end. Per-chunk logging is
        deliberately omitted (would be too noisy at INFO level).
        """
        model = request.model or settings.ollama_default_model
        messages = self._build_messages(request)

        logger.info(
            "chat_stream_request_received",
            model=model,
            has_system_prompt=request.system_prompt is not None,
            message_length=len(request.message),
        )

        start = time.perf_counter()
        chunk_count = 0
        total_chars = 0

        async for chunk in self._ollama.chat_stream(messages=messages, model=model):
            chunk_count += 1
            total_chars += len(chunk)
            yield chunk

        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "chat_stream_request_completed",
            model=model,
            duration_ms=duration_ms,
            chunk_count=chunk_count,
            reply_length=total_chars,
        )

    async def list_models(self) -> ModelsResponse:
        """Return the list of models available in Ollama."""
        models = await self._ollama.list_models()
        return ModelsResponse(models=models)

    def _build_messages(self, request: ChatRequest) -> list[ChatRole]:
        """
        Construct the message list sent to Ollama.

        Applies a system prompt if provided. In future phases this is where
        retrieved RAG context will be injected.
        """
        messages: list[ChatRole] = []
        if request.system_prompt is not None:
            messages.append(ChatRole(role="system", content=request.system_prompt))
        messages.append(ChatRole(role="user", content=request.message))
        return messages
