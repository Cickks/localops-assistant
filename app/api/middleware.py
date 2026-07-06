"""
HTTP middleware for LocalOps Assistant.

Middleware runs on every request before it reaches a route handler, and on
every response before it's sent to the client. It's the right place for
cross-cutting concerns: logging, request tracing, authentication, etc.
"""

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response

from app.core.logging import get_logger

logger = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Assign a unique ID to every request and propagate it through logs and the response.

    Behavior:
    - If the client sends an X-Request-ID header, we honor it (useful for distributed
      tracing — a frontend can generate an ID and we'll log against the same one).
    - Otherwise we generate a UUIDv4.
    - The ID is bound to structlog's contextvars, so every log line emitted during
      this request automatically includes `request_id` without manual threading.
    - The ID is echoed back in the X-Request-ID response header so clients can
      reference it when reporting issues.
    - We also emit a structured access log line with method, path, status, and duration.

    This middleware is the foundation of operational observability: when something
    fails in production, you grep one ID and see the entire request lifecycle.
    """
    # Honor an incoming request ID if the client provided one; otherwise generate.
    incoming_id = request.headers.get(REQUEST_ID_HEADER)
    request_id = incoming_id or str(uuid.uuid4())

    # Bind to structlog's contextvars. Every log call during this request inherits it.
    # clear_contextvars first defends against leaks if a previous request didn't clean up.
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        # Log unhandled exceptions with full traceback before re-raising.
        # FastAPI's exception handlers will turn this into a 500 response.
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.exception(
            "request_failed_unhandled",
            duration_ms=duration_ms,
        )
        raise

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    # Echo the request ID in the response so clients can reference it.
    response.headers[REQUEST_ID_HEADER] = request_id

    logger.info(
        "request_completed",
        status_code=response.status_code,
        duration_ms=duration_ms,
    )

    return response
