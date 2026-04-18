"""AuditLogService — the SOLE write path for the audit_log table.

CRITICAL: No other code should write to audit_log directly.
Every state-changing action must write an audit entry through this service,
in the SAME database transaction as the state change.
"""

import hashlib
import uuid
from typing import Any

import orjson
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLogEntry
from app.models.enums import AuditEventType


def _canonical_json(payload: dict[str, Any]) -> bytes:
    """Produce deterministic JSON for hash chain integrity.

    Rules:
    - Keys sorted alphabetically
    - No trailing whitespace
    - Stable numeric representation
    - UTF-8 NFC normalized (orjson handles this)
    """
    return orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)


def _compute_hash(prior_hash: str, payload: dict[str, Any]) -> str:
    """Compute SHA-256 hash: sha256(prior_hash || canonical_json(payload))."""
    canonical = _canonical_json(payload)
    data = prior_hash.encode("utf-8") + canonical
    return hashlib.sha256(data).hexdigest()


GENESIS_HASH = hashlib.sha256(b"").hexdigest()


class AuditLogService:
    """Append-only audit log with SHA-256 hash chain.

    Usage:
        async with db_session.begin():
            # ... perform state-changing operation ...
            await audit_service.append(
                session=db_session,
                firm_id=firm_id,
                event_type=AuditEventType.DOCUMENT_SUBMITTED,
                actor_user_id=user_id,
                payload={"document_id": str(doc.id)},
                document_id=doc.id,
            )
    """

    async def append(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        event_type: AuditEventType,
        payload: dict[str, Any],
        actor_user_id: uuid.UUID | None = None,
        document_id: uuid.UUID | None = None,
    ) -> AuditLogEntry:
        """Append a new entry to the audit log with hash chain integrity."""
        # Get the most recent hash for this firm's chain
        prior_hash = await self._get_prior_hash(session, firm_id)

        # Compute this entry's hash
        this_hash = _compute_hash(prior_hash, payload)

        entry = AuditLogEntry(
            firm_id=firm_id,
            document_id=document_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            payload=payload,
            prior_hash=prior_hash,
            this_hash=this_hash,
        )

        session.add(entry)
        await session.flush()
        return entry

    async def _get_prior_hash(
        self, session: AsyncSession, firm_id: uuid.UUID
    ) -> str:
        """Get the hash of the most recent audit log entry for this firm.

        Returns the genesis hash if no entries exist yet.
        """
        stmt = (
            select(AuditLogEntry.this_hash)
            .where(AuditLogEntry.firm_id == firm_id)
            .order_by(AuditLogEntry.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            return GENESIS_HASH
        return row

    async def verify_chain(
        self, session: AsyncSession, firm_id: uuid.UUID
    ) -> tuple[bool, str | None]:
        """Verify the hash chain integrity for a firm.

        Returns (is_valid, first_broken_entry_id).
        """
        stmt = (
            select(AuditLogEntry)
            .where(AuditLogEntry.firm_id == firm_id)
            .order_by(AuditLogEntry.created_at.asc())
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        if not entries:
            return True, None

        expected_prior = GENESIS_HASH

        for entry in entries:
            # Verify prior_hash matches expected
            if entry.prior_hash != expected_prior:
                return False, str(entry.id)

            # Verify this_hash is correctly computed
            computed = _compute_hash(entry.prior_hash, entry.payload)
            if entry.this_hash != computed:
                return False, str(entry.id)

            expected_prior = entry.this_hash

        return True, None


# Singleton instance
audit_log_service = AuditLogService()
