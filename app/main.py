"""
AISteve — FastAPI application entry point.

Run locally:
    uv run uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import chat, health
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.providers.ollama_provider import OllamaProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — owns long-lived resources."""
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

    ollama = OllamaProvider(
        base_url=settings.ollama_base_url,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    await ollama.start()
    app.state.ollama = ollama

    yield

    # --- shutdown ---
    logger.info("application_stopping")
    await ollama.stop()


app = FastAPI(
    title="AISteve",
    description="Local AI Homelab Assistant (Jarvis-inspired)",
    version="0.1.0",
    lifespan=lifespan,
)

# Register all route modules. Each new endpoint group adds one line here.
app.include_router(health.router)
app.include_router(chat.router)
