"""Flag service — handles reviewer actions with audit logging."""

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import audit_log_service
from app.flags.repository import flag_repository
from app.flags.schemas import ReviewerActionCreate
from app.models.enums import AuditEventType, ReviewerActionType
from app.models.flag import Flag
from app.models.reviewer_action import ReviewerAction

logger = structlog.get_logger()


class FlagService:

    async def submit_reviewer_action(
        self,
        session: AsyncSession,
        firm_id: uuid.UUID,
        user_id: uuid.UUID,
        flag_id: uuid.UUID,
        data: ReviewerActionCreate,
    ) -> ReviewerAction:
        """Submit a reviewer action on a flag with audit logging.

        Override requires a reason of at least 10 characters.
        """
        # Verify flag exists and belongs to this firm
        flag = await flag_repository.get_by_id_with_tenant_check(
            session, firm_id, flag_id
        )
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Not found"
            )

        # Override requires reason
        if data.action == ReviewerActionType.OVERRIDE and (
            not data.reason or len(data.reason) < 10
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Override action requires a reason of at least 10 characters",
            )

        # Create reviewer action
        action = await flag_repository.create_reviewer_action(
            session,
            flag_id=flag_id,
            user_id=user_id,
            action=data.action,
            reason=data.reason,
        )

        # Write audit log entry in the same transaction
        await audit_log_service.append(
            session=session,
            firm_id=firm_id,
            event_type=AuditEventType.FLAG_ACTION_TAKEN,
            actor_user_id=user_id,
            document_id=flag.document_id,
            payload={
                "flag_id": str(flag_id),
                "action": data.action.value,
                "evaluator": flag.evaluator.value,
                "severity": flag.severity.value,
            },
        )

        await logger.ainfo(
            "reviewer_action_taken",
            flag_id=str(flag_id),
            action=data.action.value,
            firm_id=str(firm_id),
        )

        return action


flag_service = FlagService()
