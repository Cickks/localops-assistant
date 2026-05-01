"""
Health check endpoints.

We expose two distinct endpoints because they answer different questions:

- /health  → "Is the process up?"  (liveness)
              Used by Docker/systemd/Kubernetes to decide whether to restart us.

- /ready   → "Can I serve traffic?" (readiness)
              Used by load balancers to decide whether to route requests here.
              Returns 503 if dependencies (Ollama) are unreachable.

Splitting these is the production standard — restarting an app because Ollama
is down is wrong (we'll come back when it's back), but routing traffic to it
in that state is also wrong.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

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


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    status_code=status.HTTP_200_OK,
)
async def health() -> HealthResponse:
    """
    Liveness probe.

    Returns 200 if the process is alive and configured. Does NOT check
    downstream dependencies — that's what /ready is for.
    """
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_env=settings.app_env,
        version="0.1.0",
    )


@router.get(
    "/ready",
    summary="Readiness check",
    status_code=status.HTTP_200_OK,
)
async def ready() -> dict[str, str]:
    """
    Readiness probe.

    In Phase 1 we don't yet check Ollama — the provider doesn't exist.
    When we add OllamaProvider in Phase 1.x, this endpoint will ping
    Ollama's /api/version and return 503 if it's unreachable.
    """
    return {"status": "ready"}
