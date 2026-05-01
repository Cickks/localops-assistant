"""
AISteve — FastAPI application entry point.

Run locally:
    uv run uvicorn app.main:app --reload

The --reload flag auto-restarts on code changes. Don't use it in production.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import health
from app.core.config import settings
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Code before `yield` runs at startup.
    Code after `yield` runs at shutdown.

    This replaces the older @app.on_event("startup")/("shutdown") pattern,
    which was deprecated in FastAPI in favor of lifespan context managers.
    """
    # --- startup ---
    configure_logging()
    logger = get_logger("aisteve.startup")
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        app_env=settings.app_env,
        host=settings.host,
        port=settings.port,
        ollama_base_url=settings.ollama_base_url,
    )

    yield  # <-- application runs here

    # --- shutdown ---
    logger.info("application_stopping")


app = FastAPI(
    title="AISteve",
    description="Local AI Homelab Assistant (Jarvis-inspired)",
    version="0.1.0",
    lifespan=lifespan,
)

# Register route modules.
# As we add new endpoint groups (chat, voice, system, etc.), they get added here.
app.include_router(health.router)
