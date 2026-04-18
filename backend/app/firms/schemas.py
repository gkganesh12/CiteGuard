import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import UserRole


class FirmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    billing_email: str | None = None


class FirmResponse(BaseModel):
    id: uuid.UUID
    name: str
    billing_email: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class UserInvite(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    role: UserRole = UserRole.SUBMITTER


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    created_at: datetime
    last_login: datetime | None = None
    model_config = {"from_attributes": True}


class RoleUpdate(BaseModel):
    role: UserRole


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None
    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyResponse):
    """Returned only at creation time — contains the plaintext key (shown once)."""
    plaintext_key: str
