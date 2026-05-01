"""
Health check endpoints.

- /health → Liveness. "Is the process up?"
- /ready  → Readiness. "Can I serve traffic right now?"
            Now actually checks that Ollama is reachable.
"""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app.api.dependencies import OllamaProviderDep
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response shape for the /health endpoint."""

    status: str
    app_name: str
    app_env: str
    version: str


class ReadyResponse(BaseModel):
    """Response shape for the /ready endpoint."""

    status: str
    ollama_reachable: bool


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    status_code=status.HTTP_200_OK,
)
async def health() -> HealthResponse:
    """Returns 200 if the process is alive."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_env=settings.app_env,
        version="0.1.0",
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Readiness check (verifies Ollama is reachable)",
)
async def ready(ollama: OllamaProviderDep, response: Response) -> ReadyResponse:
    """
    Returns 200 if Ollama is reachable, 503 otherwise.

    Used by load balancers and orchestrators to decide whether
    to send traffic to this instance.
    """
    reachable = await ollama.health_check()
    if not reachable:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.warning("readiness_check_failed", ollama_reachable=False)
        return ReadyResponse(status="not_ready", ollama_reachable=False)
    return ReadyResponse(status="ready", ollama_reachable=True)
