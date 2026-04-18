"""Flag API endpoints."""

import uuid

from fastapi import APIRouter, status

from app.common.dependencies import CurrentUser, DBSession
from app.common.exceptions import entity_not_found
from app.flags.repository import flag_repository
from app.flags.schemas import FlagResponse, ReviewerActionCreate, ReviewerActionResponse
from app.flags.service import flag_service

router = APIRouter(prefix="/v1", tags=["flags"])


@router.get(
    "/documents/{document_id}/flags",
    response_model=list[FlagResponse],
    summary="Get all flags for a document",
)
async def get_document_flags(
    document_id: uuid.UUID,
    user: CurrentUser,
    session: DBSession,
) -> list[FlagResponse]:
    """Retrieve all evaluator flags for a document, sorted by severity."""
    flags = await flag_repository.get_flags_for_document(
        session, user.firm_id, document_id
    )
    return [_flag_to_response(f) for f in flags]


@router.post(
    "/flags/{flag_id}/actions",
    response_model=ReviewerActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a reviewer action on a flag",
)
async def submit_flag_action(
    flag_id: uuid.UUID,
    data: ReviewerActionCreate,
    user: CurrentUser,
    session: DBSession,
) -> ReviewerActionResponse:
    """Submit approve/override/reject/defer action on a flag.

    Override requires a reason of at least 10 characters.
    """
    async with session.begin():
        action = await flag_service.submit_reviewer_action(
            session=session,
            firm_id=user.firm_id,
            user_id=user.user_id,
            flag_id=flag_id,
            data=data,
        )

    return ReviewerActionResponse(
        id=action.id,
        action=action.action,
        reason=action.reason,
        user_id=action.user_id,
        created_at=action.created_at,
    )


def _flag_to_response(flag: "Flag") -> FlagResponse:  # type: ignore[name-defined]
    latest_action = None
    if flag.reviewer_actions:
        latest = max(flag.reviewer_actions, key=lambda a: a.created_at)
        latest_action = ReviewerActionResponse(
            id=latest.id,
            action=latest.action,
            reason=latest.reason,
            user_id=latest.user_id,
            created_at=latest.created_at,
        )

    return FlagResponse(
        id=flag.id,
        evaluator=flag.evaluator,
        evaluator_version=flag.evaluator_version,
        severity=flag.severity,
        explanation=flag.explanation,
        confidence=flag.confidence,
        start_offset=flag.start_offset,
        end_offset=flag.end_offset,
        suggested_correction=flag.suggested_correction,
        reviewer_action=latest_action,
        created_at=flag.created_at,
    )
