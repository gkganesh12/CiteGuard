"""Flag repository — queries scoped by firm_id via document relationship."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.flag import Flag
from app.models.reviewer_action import ReviewerAction


class FlagRepository:

    async def get_by_id_with_tenant_check(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        flag_id: uuid.UUID,
    ) -> Flag | None:
        """Get flag by ID, verifying it belongs to a document owned by firm_id."""
        stmt = (
            select(Flag)
            .join(Document, Flag.document_id == Document.id)
            .where(Flag.id == flag_id, Document.firm_id == firm_id)
            .options(selectinload(Flag.reviewer_actions))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_flags_for_document(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> list[Flag]:
        """Get all flags for a document, scoped to firm_id."""
        stmt = (
            select(Flag)
            .join(Document, Flag.document_id == Document.id)
            .where(
                Flag.document_id == document_id,
                Document.firm_id == firm_id,
            )
            .options(selectinload(Flag.reviewer_actions))
            .order_by(Flag.severity, Flag.created_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_flag(
        self,
        session: AsyncSession,
        **kwargs: object,
    ) -> Flag:
        flag = Flag(**kwargs)
        session.add(flag)
        await session.flush()
        return flag

    async def create_reviewer_action(
        self,
        session: AsyncSession,
        **kwargs: object,
    ) -> ReviewerAction:
        action = ReviewerAction(**kwargs)
        session.add(action)
        await session.flush()
        return action

    async def has_unresolved_flags(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> bool:
        """Check if a document has any flags without reviewer actions."""
        stmt = (
            select(Flag.id)
            .join(Document, Flag.document_id == Document.id)
            .outerjoin(ReviewerAction, ReviewerAction.flag_id == Flag.id)
            .where(
                Flag.document_id == document_id,
                Document.firm_id == firm_id,
                ReviewerAction.id.is_(None),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None


flag_repository = FlagRepository()
