from fastapi import HTTPException, status


class CiteGuardException(Exception):
    """Base exception for all CiteGuard errors."""

    def __init__(self, message: str = "An internal error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class EntityNotFoundError(CiteGuardException):
    """Raised when an entity is not found. Returns 404 to prevent existence disclosure."""

    def __init__(self, entity_type: str = "Resource") -> None:
        super().__init__(f"{entity_type} not found")


class DuplicateEntityError(CiteGuardException):
    """Raised on idempotency key collision or unique constraint violation."""

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message)


class AuthenticationError(CiteGuardException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message)


class AuthorizationError(CiteGuardException):
    """Raised when user lacks required role."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message)


class DocumentTooLargeError(CiteGuardException):
    """Raised when document exceeds 200KB text limit."""

    def __init__(self) -> None:
        super().__init__("Document text exceeds maximum size of 200KB")


class RateLimitExceededError(CiteGuardException):
    """Raised when firm exceeds rate limit."""

    def __init__(self, retry_after: int = 60) -> None:
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")


class AuditLogIntegrityError(CiteGuardException):
    """Raised when audit log hash chain verification fails. This is a P0 incident."""

    def __init__(self, firm_id: str, row_id: str) -> None:
        super().__init__(
            f"CRITICAL: Audit log hash chain integrity violation for firm {firm_id} at row {row_id}"
        )


def entity_not_found() -> HTTPException:
    """Return 404 for missing entities. Use 404 instead of 403 to prevent existence disclosure."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
    )


def payload_too_large() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail="Document text exceeds maximum size of 200KB",
    )


def rate_limited(retry_after: int = 60) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded",
        headers={"Retry-After": str(retry_after)},
    )
