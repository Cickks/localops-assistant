"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.middleware import request_id_middleware
from app.api.routes import chat, health
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.providers.ollama_provider import OllamaProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — owns long-lived resources."""
    # --- startup ---
    configure_logging()
    logger = get_logger("localops_assistant.startup")
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
    title="LocalOps Assistant",
    description="Local-first operations assistant API backed by Ollama",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware order matters. Middleware added LAST runs FIRST on the request
# (and LAST on the response). We want the request_id middleware to run as
# early as possible so its context is available to everything downstream,
# including CORS preflight responses and any errors.
app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)

# CORS allows approved browser clients to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route modules. Each new endpoint group adds one line here.
app.include_router(health.router)
app.include_router(chat.router)
