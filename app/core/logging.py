"""
Structured logging configuration.

We use structlog to emit:
- Human-readable, colorized logs in development (easier to read while building)
- JSON logs in staging/production (parseable by log aggregators)

The same log calls work in both modes — only the renderer changes.
This keeps log statements in business code clean and consistent.
"""

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure both stdlib logging and structlog.

    Called once at application startup. Sets the level from settings.LOG_LEVEL
    and chooses the renderer based on settings.APP_ENV.
    """
    log_level = getattr(logging, settings.log_level)

    # Stdlib logging — used by uvicorn, FastAPI internals, and any third-party libs.
    # We send everything to stdout at the configured level. structlog will format it.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Shared processors run on every log call regardless of source.
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # adds context-bound vars (e.g., request_id)
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Choose the renderer based on environment.
    if settings.app_env == "development":
        # Pretty, colorized output for humans.
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # Single-line JSON for log aggregators (Loki, ELK, etc.).
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Return a structlog logger.

    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("user_login", user="michael-p", duration_ms=23)
    """
    return structlog.get_logger(name)
