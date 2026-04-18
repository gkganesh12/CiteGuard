"""Document repository — all queries scoped by firm_id (tenant isolation)."""

import uuid
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.enums import DocumentStatus, DocumentType, Severity
from app.models.flag import Flag


class DocumentRepository:
    """Repository for document CRUD operations.

    CRITICAL: Every query method requires firm_id for tenant isolation.
    firm_id comes from the authenticated session — NEVER from the request body.
    """

    async def create(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        **kwargs: object,
    ) -> Document:
        doc = Document(firm_id=firm_id, **kwargs)
        session.add(doc)
        await session.flush()
        return doc

    async def get_by_id(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> Document | None:
        """Get document by ID, scoped to firm. Returns None if not found or wrong firm."""
        stmt = select(Document).where(
            Document.id == document_id,
            Document.firm_id == firm_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        idempotency_key: str,
    ) -> Document | None:
        stmt = select(Document).where(
            Document.idempotency_key == idempotency_key,
            Document.firm_id == firm_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


    async def list_documents(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        status: DocumentStatus | None = None,
        document_type: DocumentType | None = None,
        submitter_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        cursor: uuid.UUID | None = None,
        limit: int = 25,
    ) -> list[Document]:
        """List documents with filters, scoped to firm.

        Default sort: severity DESC (by worst flag), then submitted_at ASC.
        """
        stmt = (
            select(Document)
            .where(Document.firm_id == firm_id)
            .options(selectinload(Document.flags))
        )

        if status:
            stmt = stmt.where(Document.status == status)
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if submitter_id:
            stmt = stmt.where(Document.submitter_user_id == submitter_id)
        if date_from:
            stmt = stmt.where(Document.submitted_at >= date_from)
        if date_to:
            stmt = stmt.where(Document.submitted_at <= date_to)
        if cursor:
            # Simple cursor — documents submitted after cursor doc
            cursor_doc = await self.get_by_id(session, firm_id, cursor)
            if cursor_doc:
                stmt = stmt.where(Document.submitted_at > cursor_doc.submitted_at)

        # Sort by submitted_at ascending (severity sort done in application layer
        # since it depends on flags relationship)
        stmt = stmt.order_by(Document.submitted_at.asc()).limit(limit + 1)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        document_id: uuid.UUID,
        new_status: DocumentStatus,
    ) -> Document | None:
        """Update document status, scoped to firm."""
        doc = await self.get_by_id(session, firm_id, document_id)
        if not doc:
            return None

        doc.status = new_status
        if new_status == DocumentStatus.RESOLVED:
            doc.resolved_at = func.now()
        elif new_status == DocumentStatus.IN_REVIEW:
            doc.resolved_at = None

        await session.flush()
        return doc


document_repository = DocumentRepository()
