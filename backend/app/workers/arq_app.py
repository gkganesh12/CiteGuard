"""Arq worker configuration for background job processing."""

from arq.connections import RedisSettings

from app.config import settings


async def startup(ctx: dict) -> None:  # type: ignore[type-arg]
    """Worker startup — initialize DB session factory and services."""
    from app.db.session import async_session_factory

    ctx["db_session_factory"] = async_session_factory


async def shutdown(ctx: dict) -> None:  # type: ignore[type-arg]
    """Worker shutdown — cleanup resources."""
    pass


async def evaluator_run(ctx: dict, document_id: str, firm_id: str) -> None:  # type: ignore[type-arg]
    """Run all evaluators on a document."""
    from app.workers.tasks.evaluator_run import run_evaluators

    await run_evaluators(ctx, document_id, firm_id)


class WorkerSettings:
    """Arq worker settings."""

    functions = [evaluator_run]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5 minutes max per job
