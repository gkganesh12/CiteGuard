"""FastAPI dependencies for auth, database, and tenant scoping."""

import uuid
from dataclasses import dataclass
from typing import Annotated

import httpx
import jwt
import structlog
from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
    entity_not_found,
    forbidden,
    unauthorized,
)
from app.config import settings
from app.db.session import get_async_session
from app.models.api_key import APIKey
from app.models.enums import UserRole
from app.models.user import User

logger = structlog.get_logger()

# Type alias for DB session dependency
DBSession = Annotated[AsyncSession, Depends(get_async_session)]

# JWKS cache
_jwks_cache: dict[str, jwt.PyJWK] | None = None


@dataclass(frozen=True)
class AuthenticatedUser:
    """Represents the currently authenticated user with firm context.

    firm_id is extracted from the verified token/API key — NEVER from the request body.
    """

    user_id: uuid.UUID
    firm_id: uuid.UUID
    role: UserRole
    email: str


async def _get_jwks() -> dict[str, jwt.PyJWK]:
    """Fetch and cache Clerk JWKS for JWT verification."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    if not settings.clerk_jwks_url:
        raise AuthenticationError("Clerk JWKS URL not configured")

    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.clerk_jwks_url)
        resp.raise_for_status()
        jwks_data = resp.json()

    jwk_set = jwt.PyJWKSet.from_dict(jwks_data)
    _jwks_cache = {key.key_id: key for key in jwk_set.keys if key.key_id}
    return _jwks_cache


async def _authenticate_jwt(token: str, session: AsyncSession) -> AuthenticatedUser:
    """Verify a Clerk JWT and extract user context."""
    try:
        # Decode header to get kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise AuthenticationError("JWT missing kid header")

        jwks = await _get_jwks()
        jwk = jwks.get(kid)
        if not jwk:
            # Refresh cache and retry
            global _jwks_cache
            _jwks_cache = None
            jwks = await _get_jwks()
            jwk = jwks.get(kid)
            if not jwk:
                raise AuthenticationError("Unknown signing key")

        payload = jwt.decode(
            token,
            jwk.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer if settings.clerk_issuer else None,
        )

        clerk_user_id = payload.get("sub")
        if not clerk_user_id:
            raise AuthenticationError("JWT missing sub claim")

        # Look up user by clerk_user_id
        stmt = select(User).where(
            User.clerk_user_id == clerk_user_id,
            User.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError("User not found")

        return AuthenticatedUser(
            user_id=user.id,
            firm_id=user.firm_id,
            role=user.role,
            email=user.email,
        )

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {e}")


async def _authenticate_api_key(api_key: str, session: AsyncSession) -> AuthenticatedUser:
    """Verify an API key and extract firm context."""
    import bcrypt

    # API key format: cg_live_... or cg_test_...
    prefix = api_key[:12] if len(api_key) >= 12 else api_key

    # Find all non-revoked keys with matching prefix
    stmt = select(APIKey).where(
        APIKey.key_prefix == prefix,
        APIKey.revoked_at.is_(None),
    )
    result = await session.execute(stmt)
    keys = result.scalars().all()

    for key_record in keys:
        if bcrypt.checkpw(api_key.encode("utf-8"), key_record.key_hash.encode("utf-8")):
            # Found matching key — look up the creator for user context
            user_stmt = select(User).where(
                User.id == key_record.created_by,
                User.deleted_at.is_(None),
            )
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                raise AuthenticationError("API key creator not found")

            return AuthenticatedUser(
                user_id=user.id,
                firm_id=key_record.firm_id,
                role=user.role,
                email=user.email,
            )

    raise AuthenticationError("Invalid API key")


async def get_current_user(
    request: Request,
    session: DBSession,
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser:
    """Extract and verify the authenticated user from JWT or API key.

    firm_id comes from the verified credential — NEVER from the request body.
    """
    if not authorization:
        raise unauthorized()

    if authorization.startswith("Bearer "):
        token = authorization[7:]

        # Check if it looks like an API key (cg_live_ or cg_test_)
        if token.startswith("cg_"):
            try:
                return await _authenticate_api_key(token, session)
            except AuthenticationError:
                raise unauthorized()

        # Otherwise treat as JWT
        try:
            return await _authenticate_jwt(token, session)
        except AuthenticationError:
            raise unauthorized()

    raise unauthorized()


# Type alias for authenticated user dependency
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


def require_role(*roles: UserRole):  # type: ignore[no-untyped-def]
    """Dependency factory that enforces role-based access control."""

    async def _check_role(user: CurrentUser) -> AuthenticatedUser:
        if user.role not in roles:
            raise forbidden()
        return user

    return Depends(_check_role)
