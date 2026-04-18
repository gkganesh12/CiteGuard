from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based pagination response."""

    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None
