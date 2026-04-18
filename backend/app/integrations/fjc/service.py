"""FJC directory lookup service — all queries are local (no external API)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.fjc.models import FederalJudge


class FJCService:
    """Looks up federal judges from local FJC directory data."""

    async def find_judges_by_name(
        self,
        session: AsyncSession,
        last_name: str,
        first_name: str | None = None,
    ) -> list[FederalJudge]:
        """Find judges by last name (required) and optional first name."""
        stmt = select(FederalJudge).where(
            FederalJudge.last_name_lower == last_name.lower()
        )

        if first_name:
            first_lower = first_name.lower().rstrip(".")
            stmt = stmt.where(
                or_(
                    FederalJudge.first_name_lower == first_lower,
                    FederalJudge.first_name_lower.startswith(first_lower),
                )
            )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def judge_served_on_court(
        self,
        session: AsyncSession,
        last_name: str,
        court_name: str,
        as_of_date: date | None = None,
    ) -> tuple[bool, list[FederalJudge]]:
        """Check if a judge served on a specific court.

        Returns (served: bool, matching_judges: list).
        Multiple matches possible for common names.
        """
        judges = await self.find_judges_by_name(session, last_name)

        if not judges:
            return False, []

        # Filter by court (fuzzy — court names vary)
        court_lower = court_name.lower()
        court_matches = [
            j for j in judges
            if court_lower in j.court_name.lower()
            or j.court_name.lower() in court_lower
        ]

        if not court_matches:
            return False, judges  # Judge exists but on different court

        if as_of_date:
            # Filter by service period
            period_matches = [
                j for j in court_matches
                if (j.appointment_date is None or j.appointment_date <= as_of_date)
                and (j.termination_date is None or j.termination_date >= as_of_date)
            ]
            if period_matches:
                return True, period_matches
            return False, court_matches

        return True, court_matches

    async def judge_exists(
        self,
        session: AsyncSession,
        last_name: str,
        first_name: str | None = None,
    ) -> bool:
        """Check if any federal judge with this name exists."""
        stmt = select(func.count()).select_from(FederalJudge).where(
            FederalJudge.last_name_lower == last_name.lower()
        )
        if first_name:
            first_lower = first_name.lower().rstrip(".")
            stmt = stmt.where(
                or_(
                    FederalJudge.first_name_lower == first_lower,
                    FederalJudge.first_name_lower.startswith(first_lower),
                )
            )
        result = await session.execute(stmt)
        count = result.scalar_one()
        return count > 0


fjc_service = FJCService()
