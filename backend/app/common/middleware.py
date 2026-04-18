import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

# Fields that must NEVER appear in logs (privileged data protection - §5.1)
SCRUBBED_FIELDS = frozenset({
    "text",
    "document_text",
    "prompt",
    "completion",
    "content",
    "original_text",
})


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds request_id to every request and logs request metadata (never document content)."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        await logger.ainfo(
            "request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response


def configure_structlog() -> None:
    """Configure structlog with JSON output and privilege-safe processors."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _scrub_privileged_data,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _scrub_privileged_data(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Remove any privileged document content from log entries (§5.1 compliance)."""
    for field in SCRUBBED_FIELDS:
        if field in event_dict:
            event_dict[field] = "[REDACTED - privileged]"
    return event_dict
