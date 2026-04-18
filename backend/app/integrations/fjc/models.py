"""FJC Federal Judge data model for local storage."""

import uuid
from datetime import date

from sqlalchemy import Date, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, generate_uuid


class FederalJudge(Base):
    """Local copy of FJC Biographical Directory of Federal Judges.

    ~4,000 judges. Refreshed quarterly from FJC public dataset.
    All lookups are local — no real-time API dependency.
    """

    __tablename__ = "fjc_judges"
    __table_args__ = (
        Index("ix_fjc_judges_name_lower", "last_name_lower", "first_name_lower"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    suffix: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Lowercased for case-insensitive search
    first_name_lower: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name_lower: Mapped[str] = mapped_column(String(100), nullable=False)

    court_name: Mapped[str] = mapped_column(String(255), nullable=False)
    court_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    appointment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    termination_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
