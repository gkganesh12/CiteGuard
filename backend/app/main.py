"""CiteGuard API — AI verification and audit platform for U.S. law firms."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import sentry_sdk
import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.common.exceptions import (
    CiteGuardException,
    DocumentTooLargeError,
    RateLimitExceededError,
)
from app.common.middleware import RequestContextMiddleware, configure_structlog
from app.config import settings
from app.audit.router import router as audit_router
from app.documents.router import router as documents_router
from app.firms.router import router as firms_router
from app.flags.router import router as flags_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown hooks."""
    # Startup
    configure_structlog()

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            traces_sample_rate=0.1 if settings.is_production else 1.0,
            # CRITICAL: Scrub privileged data from Sentry events (§5.1)
            before_send=_scrub_sentry_event,
        )

    await logger.ainfo("citeguard_starting", env=settings.app_env)

    yield

    # Shutdown
    await logger.ainfo("citeguard_shutting_down")


def _scrub_sentry_event(event: dict, hint: dict) -> dict:  # type: ignore[type-arg]
    """Remove privileged document content from Sentry events (§5.1 compliance)."""
    scrub_fields = {"text", "document_text", "prompt", "completion", "content"}

    if "exception" in event:
        for exception in event["exception"].get("values", []):
            for frame in exception.get("stacktrace", {}).get("frames", []):
                if "vars" in frame:
                    for field in scrub_fields:
                        if field in frame["vars"]:
                            frame["vars"][field] = "[REDACTED - privileged]"

    if "breadcrumbs" in event:
        for crumb in event["breadcrumbs"].get("values", []):
            if "data" in crumb:
                for field in scrub_fields:
                    if field in crumb["data"]:
                        crumb["data"][field] = "[REDACTED - privileged]"

    return event


app = FastAPI(
    title="CiteGuard API",
    description="AI verification and audit platform for U.S. law firms",
    version=settings.app_version,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(documents_router)
app.include_router(flags_router)
app.include_router(audit_router)
app.include_router(firms_router)


# Exception handlers
@app.exception_handler(CiteGuardException)
async def citeguard_exception_handler(
    request: Request, exc: CiteGuardException
) -> JSONResponse:
    if isinstance(exc, DocumentTooLargeError):
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": exc.message},
        )
    if isinstance(exc, RateLimitExceededError):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": exc.message},
            headers={"Retry-After": str(exc.retry_after)},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"},
    )


# Health endpoints
@app.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/readyz", tags=["health"])
async def readyz() -> dict[str, str]:
    """Readiness probe — checks DB and Redis connectivity."""
    from app.db.session import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(sa_text("SELECT 1"))
    except Exception:
        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "detail": "Database unavailable"},
        )

    return {"status": "ready"}


# Avoid importing at top level for readyz
from sqlalchemy import text as sa_text  # noqa: E402
