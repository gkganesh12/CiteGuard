"""Audit export API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.audit.exporter import audit_export_service
from app.audit.service import audit_log_service
from app.common.dependencies import CurrentUser, DBSession
from app.common.exceptions import entity_not_found
from app.documents.repository import document_repository
from app.models.enums import AuditEventType, DocumentStatus

router = APIRouter(prefix="/v1", tags=["audit"])


@router.post(
    "/documents/{document_id}/export",
    status_code=status.HTTP_201_CREATED,
    summary="Generate audit PDF export",
)
async def export_audit_pdf(
    document_id: uuid.UUID,
    user: CurrentUser,
    session: DBSession,
) -> dict:
    """Generate a tamper-evident PDF audit export for a document.

    Document should be finalized before export, but export is allowed
    in any status for flexibility.
    """
    doc = await document_repository.get_by_id(session, user.firm_id, document_id)
    if not doc:
        raise entity_not_found()

    async with session.begin():
        export = await audit_export_service.generate_export(
            session=session,
            firm_id=user.firm_id,
            firm_name="Firm",  # TODO: fetch from firms table
            document_id=document_id,
            user_id=user.user_id,
        )

        await audit_log_service.append(
            session=session,
            firm_id=user.firm_id,
            event_type=AuditEventType.EXPORT_GENERATED,
            actor_user_id=user.user_id,
            document_id=document_id,
            payload={
                "export_id": str(export.id),
                "pdf_hash": export.pdf_hash,
            },
        )

    return {
        "export_id": str(export.id),
        "pdf_path": export.pdf_path,
        "pdf_hash": export.pdf_hash,
        "generated_at": export.created_at.isoformat() if export.created_at else None,
    }
