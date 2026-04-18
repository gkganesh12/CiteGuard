import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import EvaluatorType, ReviewerActionType, Severity


class FlagResponse(BaseModel):
    """Flag detail in API responses."""

    id: uuid.UUID
    evaluator: EvaluatorType
    evaluator_version: str | None = None
    severity: Severity
    explanation: str
    confidence: float
    start_offset: int | None = None
    end_offset: int | None = None
    suggested_correction: str | None = None
    reviewer_action: ReviewerActionResponse | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewerActionResponse(BaseModel):
    """Reviewer action in API responses."""

    id: uuid.UUID
    action: ReviewerActionType
    reason: str | None = None
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# Fix forward reference
FlagResponse.model_rebuild()


class ReviewerActionCreate(BaseModel):
    """Schema for submitting a reviewer action on a flag."""

    action: ReviewerActionType
    reason: str | None = Field(
        default=None,
        min_length=10,
        description="Required if action is 'override'. Minimum 10 characters.",
    )
