"""Firm, user, and API key management endpoints."""

import secrets
import uuid

import bcrypt
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.audit.service import audit_log_service
from app.common.dependencies import CurrentUser, DBSession, require_role
from app.common.exceptions import entity_not_found
from app.firms.schemas import (
    APIKeyCreate,
    APIKeyCreated,
    APIKeyResponse,
    RoleUpdate,
    UserInvite,
    UserResponse,
)
from app.models.api_key import APIKey
from app.models.enums import AuditEventType, UserRole
from app.models.user import User

router = APIRouter(prefix="/v1", tags=["firm-management"])


# ── Team Management ────────────────────────────────────────────────────


@router.get("/users", response_model=list[UserResponse], summary="List team members")
async def list_users(
    user: CurrentUser,
    session: DBSession,
) -> list[UserResponse]:
    stmt = select(User).where(
        User.firm_id == user.firm_id,
        User.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


@router.post(
    "/users/invite",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a team member",
    dependencies=[require_role(UserRole.ADMIN)],
)
async def invite_user(
    data: UserInvite,
    user: CurrentUser,
    session: DBSession,
) -> UserResponse:
    """Invite a user by email. Admin only."""
    async with session.begin():
        new_user = User(
            firm_id=user.firm_id,
            email=data.email,
            role=data.role,
        )
        session.add(new_user)
        await session.flush()

        await audit_log_service.append(
            session=session,
            firm_id=user.firm_id,
            event_type=AuditEventType.USER_INVITED,
            actor_user_id=user.user_id,
            payload={"invited_email": data.email, "role": data.role.value},
        )

    return UserResponse.model_validate(new_user)


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Change a user's role",
    dependencies=[require_role(UserRole.ADMIN)],
)
async def update_user_role(
    user_id: uuid.UUID,
    data: RoleUpdate,
    user: CurrentUser,
    session: DBSession,
) -> UserResponse:
    """Change a team member's role. Admin only. Cannot change own role."""
    if user_id == user.user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot change your own role",
        )

    stmt = select(User).where(
        User.id == user_id,
        User.firm_id == user.firm_id,
        User.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise entity_not_found()

    async with session.begin():
        old_role = target_user.role
        target_user.role = data.role
        await session.flush()

        await audit_log_service.append(
            session=session,
            firm_id=user.firm_id,
            event_type=AuditEventType.USER_ROLE_CHANGED,
            actor_user_id=user.user_id,
            payload={
                "target_user_id": str(user_id),
                "old_role": old_role.value,
                "new_role": data.role.value,
            },
        )

    return UserResponse.model_validate(target_user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a team member",
    dependencies=[require_role(UserRole.ADMIN)],
)
async def remove_user(
    user_id: uuid.UUID,
    user: CurrentUser,
    session: DBSession,
) -> None:
    """Soft-delete a user. Admin only. Cannot remove self. Last-admin safeguard."""
    if user_id == user.user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot remove yourself",
        )

    # Last-admin safeguard
    admin_count_stmt = select(func.count()).select_from(User).where(
        User.firm_id == user.firm_id,
        User.role == UserRole.ADMIN,
        User.deleted_at.is_(None),
    )
    result = await session.execute(admin_count_stmt)
    admin_count = result.scalar_one()

    target_stmt = select(User).where(
        User.id == user_id,
        User.firm_id == user.firm_id,
        User.deleted_at.is_(None),
    )
    target_result = await session.execute(target_stmt)
    target_user = target_result.scalar_one_or_none()
    if not target_user:
        raise entity_not_found()

    if target_user.role == UserRole.ADMIN and admin_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot remove the last admin",
        )

    async with session.begin():
        target_user.deleted_at = func.now()
        await session.flush()

        await audit_log_service.append(
            session=session,
            firm_id=user.firm_id,
            event_type=AuditEventType.USER_REMOVED,
            actor_user_id=user.user_id,
            payload={"removed_user_id": str(user_id)},
        )


# ── API Key Management ────────────────────────────────────────────────


@router.get(
    "/api-keys",
    response_model=list[APIKeyResponse],
    summary="List API keys",
)
async def list_api_keys(
    user: CurrentUser,
    session: DBSession,
) -> list[APIKeyResponse]:
    stmt = select(APIKey).where(
        APIKey.firm_id == user.firm_id,
        APIKey.revoked_at.is_(None),
    )
    result = await session.execute(stmt)
    return [APIKeyResponse.model_validate(k) for k in result.scalars().all()]


@router.post(
    "/api-keys",
    response_model=APIKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new API key",
    dependencies=[require_role(UserRole.ADMIN)],
)
async def create_api_key(
    data: APIKeyCreate,
    user: CurrentUser,
    session: DBSession,
) -> APIKeyCreated:
    """Generate a new API key. The plaintext key is shown ONCE and never again."""
    # Generate key: cg_live_ + 32 random bytes (base62-ish)
    raw = secrets.token_urlsafe(32)
    plaintext_key = f"cg_live_{raw}"
    key_prefix = plaintext_key[:12]

    # Hash for storage
    key_hash = bcrypt.hashpw(
        plaintext_key.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    async with session.begin():
        api_key = APIKey(
            firm_id=user.firm_id,
            name=data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            created_by=user.user_id,
        )
        session.add(api_key)
        await session.flush()

        await audit_log_service.append(
            session=session,
            firm_id=user.firm_id,
            event_type=AuditEventType.API_KEY_CREATED,
            actor_user_id=user.user_id,
            payload={"key_id": str(api_key.id), "key_name": data.name},
        )

    resp = APIKeyCreated.model_validate(api_key)
    resp.plaintext_key = plaintext_key
    return resp


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
    dependencies=[require_role(UserRole.ADMIN)],
)
async def revoke_api_key(
    key_id: uuid.UUID,
    user: CurrentUser,
    session: DBSession,
) -> None:
    """Revoke an API key. Admin only."""
    stmt = select(APIKey).where(
        APIKey.id == key_id,
        APIKey.firm_id == user.firm_id,
        APIKey.revoked_at.is_(None),
    )
    result = await session.execute(stmt)
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise entity_not_found()

    async with session.begin():
        api_key.revoked_at = func.now()
        await session.flush()

        await audit_log_service.append(
            session=session,
            firm_id=user.firm_id,
            event_type=AuditEventType.API_KEY_REVOKED,
            actor_user_id=user.user_id,
            payload={"key_id": str(key_id), "key_name": api_key.name},
        )
