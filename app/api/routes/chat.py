"""
Chat API routes.

Endpoints:
    POST /api/v1/chat         — Send a message, get a complete response.
    POST /api/v1/chat/stream  — Send a message, stream tokens as SSE.
    GET  /api/v1/models       — List models installed in Ollama.

Conversation memory comes in Phase 2.
"""

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import ChatServiceDep
from app.core.exceptions import (
    ModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnreachableError,
)
from app.core.logging import get_logger
from app.schemas.chat import ChatRequest, ChatResponse, ModelsResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a chat message and receive a complete response",
)
async def chat(request: ChatRequest, service: ChatServiceDep) -> ChatResponse:
    """
    Submit a message to the assistant and get a single complete reply.

    For long responses, prefer the streaming variant at /api/v1/chat/stream.
    """
    try:
        return await service.chat(request)
    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except OllamaUnreachableError as e:
        logger.error("ollama_unreachable", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The LLM backend is not reachable.",
        ) from e
    except OllamaTimeoutError as e:
        logger.warning("ollama_timeout", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The LLM took too long to respond.",
        ) from e


@router.post(
    "/chat/stream",
    summary="Stream a chat response token-by-token via Server-Sent Events",
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Stream of SSE events. Each `data:` line carries a JSON object.",
        },
    },
)
async def chat_stream(
    request: ChatRequest,
    service: ChatServiceDep,
) -> StreamingResponse:
    """
    Submit a message and stream tokens back as Server-Sent Events.

    The response Content-Type is `text/event-stream`. Each event has shape:

        data: {"chunk": "Hello"}

        data: {"chunk": " world"}

        data: {"done": true}

    On error during streaming, the final event will be:

        data: {"error": "...message..."}

    Note: HTTP status errors that occur BEFORE the stream starts (e.g.
    model-not-found) come back as conventional 4xx/5xx responses. Errors
    DURING the stream are reported as `error` events because the response
    headers have already been sent and the status code can no longer change.
    """

    async def sse_generator() -> AsyncIterator[bytes]:
        """
        Wrap the service's plain-text chunks in the SSE wire format.

        SSE format: `data: <json>\\n\\n`. The double newline is mandatory —
        it terminates the event. Encoding to bytes happens here because
        StreamingResponse requires bytes for streaming bodies.
        """
        try:
            async for chunk in service.chat_stream(request):
                event = json.dumps({"chunk": chunk})
                yield f"data: {event}\n\n".encode()

            # Sentinel event so clients know the stream ended cleanly.
            yield b'data: {"done": true}\n\n'

        except ModelNotFoundError as e:
            # The exception fires before any chunks if the model is missing,
            # but we surface it as an SSE error event for consistency.
            error_event = json.dumps({"error": str(e), "code": "model_not_found"})
            yield f"data: {error_event}\n\n".encode()
        except OllamaUnreachableError as e:
            logger.error("ollama_unreachable_during_stream", error=str(e))
            error_event = json.dumps({"error": "LLM backend unreachable", "code": "unreachable"})
            yield f"data: {error_event}\n\n".encode()
        except OllamaTimeoutError as e:
            logger.warning("ollama_timeout_during_stream", error=str(e))
            error_event = json.dumps({"error": "LLM timed out", "code": "timeout"})
            yield f"data: {error_event}\n\n".encode()

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            # Disable buffering on intermediate proxies (nginx etc.).
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="List models available in Ollama",
)
async def list_models(service: ChatServiceDep) -> ModelsResponse:
    """Return all models installed locally in Ollama."""
    try:
        return await service.list_models()
    except OllamaUnreachableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The LLM backend is not reachable.",
        ) from e
