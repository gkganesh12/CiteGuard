import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import DocumentStatus, DocumentType


class DocumentCreate(BaseModel):
    """Schema for submitting a document for verification (POST /v1/documents)."""

    user_id: str = Field(description="Firm-assigned user identifier")
    document_type: DocumentType = Field(default=DocumentType.OTHER)
    text: str = Field(max_length=204800, description="Document text (max 200KB)")
    prompt: str | None = Field(default=None, description="Original prompt (if available)")
    llm_provider: str | None = Field(default=None, description="e.g. anthropic, openai")
    llm_model: str | None = Field(default=None, description="e.g. claude-opus-4-6")
    metadata: dict | None = Field(default=None, description="Free-form metadata (max 4KB)")


class DocumentResponse(BaseModel):
    """Response after document submission."""

    document_id: uuid.UUID
    status: DocumentStatus
    submitted_at: datetime
    review_url: str

    model_config = {"from_attributes": True}


class DocumentDetail(BaseModel):
    """Detailed document view with flags summary."""

    id: uuid.UUID
    status: DocumentStatus
    document_type: DocumentType
    submitted_at: datetime
    resolved_at: datetime | None = None
    summary: dict[str, int] = Field(
        default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "advisory": 0}
    )

    model_config = {"from_attributes": True}
