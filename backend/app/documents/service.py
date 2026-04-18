"""Document ingestion service — single entry point for SDK and proxy submissions."""

import uuid

import structlog
from arq.connections import ArqRedis, create_pool
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import audit_log_service
from app.config import settings
from app.documents.repository import document_repository
from app.documents.schemas import DocumentCreate
from app.models.document import Document
from app.models.enums import AuditEventType

logger = structlog.get_logger()

_arq_pool: ArqRedis | None = None


async def _get_arq_pool() -> ArqRedis:
    """Get or create the Arq Redis connection pool for job enqueuing."""
    global _arq_pool
    if _arq_pool is None:
        from arq.connections import RedisSettings
        _arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    return _arq_pool


class DocumentIngestionService:
    """Handles document submission, validation, and audit logging.

    This is the single ingestion path for both SDK and proxy submissions.
    """

    async def submit_document(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        user_id: uuid.UUID,
        data: DocumentCreate,
        idempotency_key: str | None = None,
    ) -> Document:
        """Submit a document for verification.

        Creates the document and writes an audit log entry in the SAME transaction.
        """
        # Check idempotency
        if idempotency_key:
            existing = await document_repository.get_by_idempotency_key(
                session, firm_id, idempotency_key
            )
            if existing:
                return existing

        # Validate document size (200KB text limit)
        text_size = len(data.text.encode("utf-8"))
        if text_size > 204800:
            from app.common.exceptions import DocumentTooLargeError

            raise DocumentTooLargeError()

        # Create document
        doc = await document_repository.create(
            session,
            firm_id=firm_id,
            submitter_user_id=user_id,
            text=data.text,
            document_type=data.document_type,
            llm_provider=data.llm_provider,
            llm_model=data.llm_model,
            prompt=data.prompt,
            metadata_json=data.metadata,
            idempotency_key=idempotency_key,
        )

        # Write audit log entry in the same transaction
        await audit_log_service.append(
            session=session,
            firm_id=firm_id,
            event_type=AuditEventType.DOCUMENT_SUBMITTED,
            actor_user_id=user_id,
            document_id=doc.id,
            payload={
                "document_id": str(doc.id),
                "document_type": data.document_type.value,
                "llm_provider": data.llm_provider,
                "llm_model": data.llm_model,
            },
        )

        await logger.ainfo(
            "document_submitted",
            document_id=str(doc.id),
            firm_id=str(firm_id),
            document_type=data.document_type.value,
        )

        # Enqueue evaluator pipeline (runs asynchronously in Arq worker)
        try:
            pool = await _get_arq_pool()
            await pool.enqueue_job(
                "evaluator_run",
                str(doc.id),
                str(firm_id),
            )
        except Exception as exc:
            # Don't fail submission if enqueue fails — document is saved
            await logger.aerror(
                "evaluator_enqueue_failed",
                document_id=str(doc.id),
                error=str(exc),
            )

        return doc


document_ingestion_service = DocumentIngestionService()
