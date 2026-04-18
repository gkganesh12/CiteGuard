"""Document API endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Query, status

from app.audit.service import audit_log_service
from app.common.dependencies import CurrentUser, DBSession
from app.common.exceptions import entity_not_found, payload_too_large
from app.common.pagination import PaginatedResponse
from app.documents.repository import document_repository
from app.documents.schemas import DocumentCreate, DocumentDetail, DocumentResponse
from app.documents.service import document_ingestion_service
from app.flags.repository import flag_repository
from app.models.enums import AuditEventType, DocumentStatus, DocumentType, Severity

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a document for verification",
)
async def submit_document(
    data: DocumentCreate,
    user: CurrentUser,
    session: DBSession,
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key"
    ),
) -> DocumentResponse:
    """Submit an AI-generated document for CiteGuard verification.

    Accepts document text (max 200KB), queues evaluator pipeline,
    and returns document ID for status tracking.
    """
    # Validate text size before processing
    if len(data.text.encode("utf-8")) > 204800:
        raise payload_too_large()

    async with session.begin():
        doc = await document_ingestion_service.submit_document(
            session=session,
            firm_id=user.firm_id,
            user_id=user.user_id,
            data=data,
            idempotency_key=idempotency_key,
        )

    return DocumentResponse(
        document_id=doc.id,
        status=doc.status,
        submitted_at=doc.submitted_at,
        review_url=f"/documents/{doc.id}",
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetail,
    summary="Get document status and flag summary",
)
async def get_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    session: DBSession,
) -> DocumentDetail:
    """Retrieve document status and flags summary.

    Returns 404 if document not found or belongs to a different firm
    (tenant isolation — never disclose existence to other firms).
    """
    doc = await document_repository.get_by_id(session, user.firm_id, document_id)
    if not doc:
        raise entity_not_found()

    # Compute severity summary from flags
    summary = {"critical": 0, "high": 0, "medium": 0, "advisory": 0}
    for flag in doc.flags:
        severity_key = flag.severity.value.lower()
        if severity_key in summary:
            summary[severity_key] += 1

    return DocumentDetail(
        id=doc.id,
        status=doc.status,
        document_type=doc.document_type,
        submitted_at=doc.submitted_at,
        resolved_at=doc.resolved_at,
        summary=summary,
    )


@router.get(
    "",
    response_model=PaginatedResponse[DocumentDetail],
    summary="List documents in the review queue",
)
async def list_documents(
    user: CurrentUser,
    session: DBSession,
    status_filter: DocumentStatus | None = Query(default=None, alias="status"),
    document_type: DocumentType | None = Query(default=None),
    submitter: uuid.UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    cursor: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=25, le=100),
) -> PaginatedResponse[DocumentDetail]:
    """List documents with filters, sorted by severity then date.

    Supports cursor-based pagination.
    """
    docs = await document_repository.list_documents(
        session=session,
        firm_id=user.firm_id,
        status=status_filter,
        document_type=document_type,
        submitter_id=submitter,
        date_from=date_from,
        date_to=date_to,
        cursor=cursor,
        limit=limit,
    )

    has_more = len(docs) > limit
    items = docs[:limit]

    # Sort by worst severity DESC, then submitted_at ASC
    severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.ADVISORY: 3}

    def _worst_severity(doc: object) -> int:
        flags = getattr(doc, "flags", [])
        if not flags:
            return 4  # No flags = lowest priority
        return min(severity_order.get(f.severity, 4) for f in flags)

    items.sort(key=lambda d: (_worst_severity(d), d.submitted_at))

    details = []
    for doc in items:
        summary = {"critical": 0, "high": 0, "medium": 0, "advisory": 0}
        for flag in doc.flags:
            key = flag.severity.value.lower()
            if key in summary:
                summary[key] += 1
        details.append(DocumentDetail(
            id=doc.id,
            status=doc.status,
            document_type=doc.document_type,
            submitted_at=doc.submitted_at,
            resolved_at=doc.resolved_at,
            summary=summary,
        ))

    return PaginatedResponse(
        items=details,
        next_cursor=str(items[-1].id) if has_more and items else None,
        has_more=has_more,
    )


@router.put(
    "/{document_id}/finalize",
    response_model=DocumentDetail,
    summary="Finalize a document (all flags must be resolved)",
)
async def finalize_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    session: DBSession,
) -> DocumentDetail:
    """Finalize a document — moves to Resolved status.

    Blocked if any flags have no reviewer action (enforced server-side).
    """
    doc = await document_repository.get_by_id(session, user.firm_id, document_id)
    if not doc:
        raise entity_not_found()

    if doc.status == DocumentStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already finalized",
        )

    # Check for unresolved flags — finalize BLOCKED while flags unresolved
    has_unresolved = await flag_repository.has_unresolved_flags(
        session, user.firm_id, document_id
    )
    if has_unresolved:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot finalize: document has unresolved flags. "
            "All flags must be approved, overridden, rejected, or deferred.",
        )

    async with session.begin():
        doc = await document_repository.update_status(
            session, user.firm_id, document_id, DocumentStatus.RESOLVED
        )

        await audit_log_service.append(
            session=session,
            firm_id=user.firm_id,
            event_type=AuditEventType.DOCUMENT_FINALIZED,
            actor_user_id=user.user_id,
            document_id=document_id,
            payload={"document_id": str(document_id)},
        )

    summary = {"critical": 0, "high": 0, "medium": 0, "advisory": 0}
    for flag in doc.flags:
        key = flag.severity.value.lower()
        if key in summary:
            summary[key] += 1

    return DocumentDetail(
        id=doc.id,
        status=doc.status,
        document_type=doc.document_type,
        submitted_at=doc.submitted_at,
        resolved_at=doc.resolved_at,
        summary=summary,
    )


@router.put(
    "/{document_id}/reopen",
    response_model=DocumentDetail,
    summary="Reopen a finalized document",
)
async def reopen_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    session: DBSession,
) -> DocumentDetail:
    """Reopen a Resolved document — returns to In Review status."""
    doc = await document_repository.get_by_id(session, user.firm_id, document_id)
    if not doc:
        raise entity_not_found()

    if doc.status != DocumentStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only finalized documents can be reopened",
        )

    async with session.begin():
        doc = await document_repository.update_status(
            session, user.firm_id, document_id, DocumentStatus.IN_REVIEW
        )

        await audit_log_service.append(
            session=session,
            firm_id=user.firm_id,
            event_type=AuditEventType.DOCUMENT_REOPENED,
            actor_user_id=user.user_id,
            document_id=document_id,
            payload={"document_id": str(document_id)},
        )

    summary = {"critical": 0, "high": 0, "medium": 0, "advisory": 0}
    for flag in doc.flags:
        key = flag.severity.value.lower()
        if key in summary:
            summary[key] += 1

    return DocumentDetail(
        id=doc.id,
        status=doc.status,
        document_type=doc.document_type,
        submitted_at=doc.submitted_at,
        resolved_at=doc.resolved_at,
        summary=summary,
    )
