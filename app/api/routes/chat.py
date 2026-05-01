"""
Chat API routes.

Endpoints:
    POST /api/v1/chat     — Send a message, get a complete response.
    GET  /api/v1/models   — List models installed in Ollama.

Streaming and conversation memory come in later phases.
"""

from fastapi import APIRouter, HTTPException, status

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

    For long responses, prefer the streaming variant (Phase 1 Part 3).
    """
    try:
        return await service.chat(request)
    except ModelNotFoundError as e:
        # Client asked for a model that isn't installed.
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
