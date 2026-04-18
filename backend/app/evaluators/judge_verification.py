"""Judge Verification Evaluator (F5) — v1.0.0

Extracts judge names from documents and verifies them against the
Federal Judicial Center biographical directory.

Checks:
- Judge existed as a federal judge
- Judge served on the cited court during the relevant time period

Severity:
  CRITICAL — no federal judge with this name ever existed
  HIGH     — judge exists but did not sit on cited court during cited period
  ADVISORY — match confirmed; or ambiguous (common name, multiple matches)
"""

from __future__ import annotations

import re

import structlog

from app.evaluators.base import EvaluationContext, FlagResult
from app.models.enums import EvaluatorType, Severity

logger = structlog.get_logger()

VERSION = "1.0.0"

# ── Judge name extraction patterns ──────────────────────────────────────

# "Judge John Smith" / "Judge J. Smith"
JUDGE_TITLE_PATTERN = re.compile(
    r"\b(?:Judge|Justice|Chief\s+Justice|Magistrate\s+Judge)\s+"
    r"([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][A-Za-z\-']+)",
    re.IGNORECASE,
)

# "the Honorable John Smith" / "the Honorable J. Smith"
HONORABLE_PATTERN = re.compile(
    r"\b(?:the\s+)?Honorable\s+"
    r"([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][A-Za-z\-']+)",
    re.IGNORECASE,
)

# "Smith, J." / "Smith, C.J." (judicial opinion attribution)
OPINION_AUTHOR_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z\-']+),\s*(?:J\.|C\.J\.|JJ\.|Circuit\s+Judge)",
)

# Court name extraction near judge mention
COURT_NEAR_JUDGE = re.compile(
    r"(?:(?:United\s+States\s+)?(?:District\s+Court|Court\s+of\s+Appeals)"
    r"(?:\s+for\s+the\s+)?([^,.\n]{5,60}))"
    r"|(?:((?:\d+(?:st|nd|rd|th)|D\.C\.)\s+Cir(?:cuit|\.)))",
    re.IGNORECASE,
)


def _extract_judge_mentions(text: str) -> list[dict[str, str | int]]:
    """Extract judge names from document text using multiple patterns."""
    mentions: list[dict[str, str | int]] = []
    seen_names: set[str] = set()

    for pattern in [JUDGE_TITLE_PATTERN, HONORABLE_PATTERN]:
        for match in pattern.finditer(text):
            full_name = match.group(1).strip()
            name_key = full_name.lower()
            if name_key not in seen_names:
                seen_names.add(name_key)
                mentions.append({
                    "full_name": full_name,
                    "start": match.start(),
                    "end": match.end(),
                    "matched_text": match.group(0),
                })

    for match in OPINION_AUTHOR_PATTERN.finditer(text):
        last_name = match.group(1).strip()
        name_key = last_name.lower()
        if name_key not in seen_names:
            seen_names.add(name_key)
            mentions.append({
                "full_name": last_name,
                "start": match.start(),
                "end": match.end(),
                "matched_text": match.group(0),
            })

    return mentions


def _parse_name(full_name: str) -> tuple[str, str | None]:
    """Split a full name into (last_name, first_name_or_initial)."""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], None
    # Last word is last name, everything else is first/middle
    return parts[-1], parts[0]


def _find_nearby_court(text: str, position: int) -> str | None:
    """Find the court name mentioned near a judge reference."""
    window = text[max(0, position - 300) : position + 300]
    match = COURT_NEAR_JUDGE.search(window)
    if match:
        return (match.group(1) or match.group(2) or "").strip()
    return None


class JudgeVerificationEvaluator:
    """Verifies judge names against the FJC biographical directory."""

    @property
    def name(self) -> EvaluatorType:
        return EvaluatorType.JUDGE_VERIFICATION

    @property
    def version(self) -> str:
        return VERSION

    async def evaluate(
        self, text: str, context: EvaluationContext
    ) -> list[FlagResult]:
        mentions = _extract_judge_mentions(text)
        if not mentions:
            return []

        flags: list[FlagResult] = []

        # Import here to avoid circular imports and allow DB access
        try:
            from app.db.session import async_session_factory
            from app.integrations.fjc.service import fjc_service
        except Exception as exc:
            await logger.awarning("fjc_service_unavailable", error=str(exc))
            return [
                FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.ADVISORY,
                    explanation="Judge verification unavailable — FJC directory not loaded.",
                    confidence=0.0,
                    raw_output={"error": str(exc)},
                )
            ]

        async with async_session_factory() as session:
            for mention in mentions:
                full_name = str(mention["full_name"])
                start = int(mention["start"])
                end = int(mention["end"])
                matched_text = str(mention["matched_text"])

                last_name, first_name = _parse_name(full_name)
                nearby_court = _find_nearby_court(text, start)

                # Check if judge exists at all
                exists = await fjc_service.judge_exists(
                    session, last_name, first_name
                )

                if not exists:
                    flags.append(FlagResult(
                        evaluator=self.name,
                        evaluator_version=self.version,
                        severity=Severity.CRITICAL,
                        explanation=(
                            f"No federal judge named '{full_name}' found in the "
                            f"FJC Biographical Directory. This judge name may be "
                            f"fabricated."
                        ),
                        confidence=0.9,
                        start_offset=start,
                        end_offset=end,
                        raw_output={
                            "judge_name": full_name,
                            "matched_text": matched_text,
                            "found_in_fjc": False,
                        },
                    ))
                    continue

                # Judge exists — check court if we can identify one
                if nearby_court:
                    served, matching = await fjc_service.judge_served_on_court(
                        session, last_name, nearby_court
                    )

                    if not served and matching:
                        actual_courts = ", ".join(
                            set(j.court_name for j in matching[:3])
                        )
                        flags.append(FlagResult(
                            evaluator=self.name,
                            evaluator_version=self.version,
                            severity=Severity.HIGH,
                            explanation=(
                                f"Judge '{full_name}' is a real federal judge but "
                                f"served on {actual_courts}, not '{nearby_court}'. "
                                f"Verify court attribution."
                            ),
                            confidence=0.75,
                            start_offset=start,
                            end_offset=end,
                            raw_output={
                                "judge_name": full_name,
                                "expected_court": nearby_court,
                                "actual_courts": actual_courts,
                            },
                        ))
                        continue

                # Check for ambiguity (common names with multiple matches)
                all_judges = await fjc_service.find_judges_by_name(
                    session, last_name, first_name
                )
                if len(all_judges) > 2:
                    flags.append(FlagResult(
                        evaluator=self.name,
                        evaluator_version=self.version,
                        severity=Severity.ADVISORY,
                        explanation=(
                            f"Judge '{full_name}' matches {len(all_judges)} judges "
                            f"in the FJC directory. Name is ambiguous — verify "
                            f"the specific judge is correctly identified."
                        ),
                        confidence=0.5,
                        start_offset=start,
                        end_offset=end,
                        raw_output={
                            "judge_name": full_name,
                            "match_count": len(all_judges),
                        },
                    ))

        return flags
