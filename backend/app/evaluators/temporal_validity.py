"""Temporal Validity Evaluator (F6) — v1.0.0

Checks whether cited cases have been overruled, abrogated, or superseded
by querying CourtListener's citation graph for negative treatment.

Severity:
  CRITICAL — cited case is expressly overruled by a higher court
  HIGH     — cited case is abrogated in relevant jurisdiction
  MEDIUM   — significant negative treatment (>3 negative-treatment cites)
  ADVISORY — no negative treatment found
"""

from __future__ import annotations

import structlog

from app.evaluators.base import EvaluationContext, FlagResult
from app.evaluators.citation_existence import _parse_citations
from app.integrations.courtlistener.client import courtlistener_client
from app.models.enums import EvaluatorType, Severity

logger = structlog.get_logger()

VERSION = "1.0.0"

# Negative treatment types and their severity mapping
OVERRULED_TERMS = {"overruled", "overruling", "expressly overruled"}
ABROGATED_TERMS = {"abrogated", "abrogation"}
SUPERSEDED_TERMS = {"superseded", "superseded by statute"}
NEGATIVE_TERMS = {
    "criticized",
    "questioned",
    "disagreed with",
    "distinguished",
    "limited",
    "declined to follow",
}


class TemporalValidityEvaluator:
    """Checks for overruled, abrogated, or superseded precedent."""

    @property
    def name(self) -> EvaluatorType:
        return EvaluatorType.TEMPORAL_VALIDITY

    @property
    def version(self) -> str:
        return VERSION

    async def evaluate(
        self, text: str, context: EvaluationContext
    ) -> list[FlagResult]:
        citations = _parse_citations(text)
        if not citations:
            return []

        flags: list[FlagResult] = []

        for cite in citations:
            volume = str(cite["volume"])
            reporter = str(cite["reporter"])
            page = str(cite["page"])
            matched_text = str(cite["matched_text"])
            start = int(cite.get("start", 0))
            end = int(cite.get("end", 0))

            # Resolve citation first
            result = await courtlistener_client.resolve_citation(
                volume=volume, reporter=reporter, page=page
            )

            if not result.found or not result.opinion:
                # Can't check treatment if citation doesn't resolve
                # Citation Existence evaluator handles this case
                continue

            # Query for negative treatment via citation graph
            treatment = await self._check_negative_treatment(result.opinion.id)

            if treatment is None:
                # API failure — ADVISORY
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.ADVISORY,
                    explanation=(
                        f"Negative treatment check unavailable for '{matched_text}'. "
                        f"CourtListener citation graph could not be queried."
                    ),
                    confidence=0.0,
                    start_offset=start,
                    end_offset=end,
                    raw_output={"citation": matched_text, "reason": "api_unavailable"},
                ))
                continue

            if treatment["is_overruled"]:
                overruling_case = treatment.get("overruling_case", "unknown case")
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.CRITICAL,
                    explanation=(
                        f"Citation '{matched_text}' has been expressly overruled "
                        f"by {overruling_case}. This precedent is no longer valid."
                    ),
                    confidence=0.95,
                    start_offset=start,
                    end_offset=end,
                    raw_output={
                        "citation": matched_text,
                        "treatment": "overruled",
                        "overruling_case": overruling_case,
                        "opinion_url": result.opinion.full_url,
                    },
                ))
            elif treatment["is_abrogated"]:
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.HIGH,
                    explanation=(
                        f"Citation '{matched_text}' has been abrogated. "
                        f"Review whether this precedent remains authoritative "
                        f"in the relevant jurisdiction."
                    ),
                    confidence=0.85,
                    start_offset=start,
                    end_offset=end,
                    raw_output={
                        "citation": matched_text,
                        "treatment": "abrogated",
                        "opinion_url": result.opinion.full_url,
                    },
                ))
            elif treatment["negative_count"] > 3:
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.MEDIUM,
                    explanation=(
                        f"Citation '{matched_text}' has significant negative "
                        f"treatment ({treatment['negative_count']} negative citations). "
                        f"Review current authority status."
                    ),
                    confidence=0.7,
                    start_offset=start,
                    end_offset=end,
                    raw_output={
                        "citation": matched_text,
                        "treatment": "negative_treatment",
                        "negative_count": treatment["negative_count"],
                        "opinion_url": result.opinion.full_url,
                    },
                ))

        return flags

    async def _check_negative_treatment(
        self, opinion_id: int
    ) -> dict | None:
        """Query CourtListener for negative treatment of an opinion.

        Returns dict with is_overruled, is_abrogated, negative_count,
        overruling_case. Returns None on API failure.
        """
        try:
            result = await courtlistener_client._call_with_retry(
                f"/opinions/{opinion_id}/cited-by/",
                params={"type": "o"},
            )

            if result is None:
                return None

            citing_opinions = result.get("results", [])

            is_overruled = False
            is_abrogated = False
            negative_count = 0
            overruling_case = None

            for citing in citing_opinions:
                treatment = (citing.get("treatment", "") or "").lower()

                if any(t in treatment for t in OVERRULED_TERMS):
                    is_overruled = True
                    overruling_case = citing.get("caseName", "Unknown")
                    negative_count += 1
                elif any(t in treatment for t in ABROGATED_TERMS):
                    is_abrogated = True
                    negative_count += 1
                elif any(t in treatment for t in SUPERSEDED_TERMS):
                    is_abrogated = True  # Treat superseded similarly
                    negative_count += 1
                elif any(t in treatment for t in NEGATIVE_TERMS):
                    negative_count += 1

            return {
                "is_overruled": is_overruled,
                "is_abrogated": is_abrogated,
                "negative_count": negative_count,
                "overruling_case": overruling_case,
            }

        except Exception as exc:
            await logger.awarning(
                "temporal_validity_check_failed",
                opinion_id=opinion_id,
                error=str(exc),
            )
            return None
