"""Citation Existence Evaluator (F2) — v1.0.0

Verifies every case citation in the document against CourtListener.

Severity:
  CRITICAL — no matching opinion found (likely hallucination)
  HIGH     — match found but case name doesn't match (misattribution)
  ADVISORY — match found, everything consistent

Uses eyecite for citation parsing, supports 5 reporter formats:
Supreme Court, Federal Reporter, Federal Supplement, Federal Rules Decisions, generic.
"""

from __future__ import annotations

import re

import structlog

from app.evaluators.base import EvaluationContext, FlagResult, IEvaluator
from app.integrations.courtlistener.client import courtlistener_client
from app.models.enums import EvaluatorType, Severity

logger = structlog.get_logger()

VERSION = "1.0.0"

# Common federal reporter patterns for fallback parsing if eyecite is unavailable
CITATION_PATTERN = re.compile(
    r"(\d{1,4})\s+"
    r"(U\.S\.|S\.\s*Ct\.|L\.\s*Ed\.\s*2d|F\.\d[a-z]{1,2}|F\.\s*Supp\.\s*\d?[a-z]*"
    r"|F\.\s*R\.\s*D\.|B\.R\.|F\.\s*App(?:'|')x)"
    r"\s+(\d{1,5})"
    r"(?:\s*\(([^)]+)\))?",
    re.IGNORECASE,
)


def _parse_citations(text: str) -> list[dict[str, str | int]]:
    """Parse case citations from document text.

    Attempts to use eyecite for robust parsing, falls back to regex.
    Returns list of dicts with volume, reporter, page, and text span info.
    """
    citations = []

    try:
        from eyecite import get_citations
        from eyecite.models import FullCaseCitation

        for cite in get_citations(text):
            if isinstance(cite, FullCaseCitation):
                citations.append({
                    "volume": str(cite.groups.get("volume", "")),
                    "reporter": str(cite.corrected_reporter()),
                    "page": str(cite.groups.get("page", "")),
                    "matched_text": cite.matched_text(),
                    "start": cite.span()[0],
                    "end": cite.span()[1],
                })

    except ImportError:
        # Fallback to regex if eyecite not installed
        for match in CITATION_PATTERN.finditer(text):
            citations.append({
                "volume": match.group(1),
                "reporter": match.group(2),
                "page": match.group(3),
                "matched_text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })

    return citations


def _extract_case_name_near_citation(text: str, cite_start: int) -> str | None:
    """Extract the case name that appears before a citation.

    Looks for patterns like 'Smith v. Jones, 123 F.3d 456'.
    """
    # Look backwards from citation start for 'v.' pattern
    prefix = text[max(0, cite_start - 200):cite_start].strip().rstrip(",")
    v_match = re.search(r"([A-Z][A-Za-z.\'\-]+\s+v\.\s+[A-Z][A-Za-z.\'\-\s]+)$", prefix)
    if v_match:
        return v_match.group(1).strip()
    return None


class CitationExistenceEvaluator:
    """Verifies that every case citation resolves to a real opinion."""

    @property
    def name(self) -> EvaluatorType:
        return EvaluatorType.CITATION_EXISTENCE

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

            # Resolve against CourtListener
            result = await courtlistener_client.resolve_citation(
                volume=volume, reporter=reporter, page=page
            )

            if result.error:
                # External API failure — produce ADVISORY (failure-as-ADVISORY)
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.ADVISORY,
                    explanation=(
                        f"Citation '{matched_text}' could not be verified: {result.error}"
                    ),
                    confidence=0.0,
                    start_offset=start,
                    end_offset=end,
                    raw_output={"citation": matched_text, "error": result.error},
                ))
                continue

            if not result.found:
                # No matching opinion — likely hallucination
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.CRITICAL,
                    explanation=(
                        f"Citation '{matched_text}' does not match any opinion "
                        f"in CourtListener. This citation may be hallucinated."
                    ),
                    confidence=0.95,
                    start_offset=start,
                    end_offset=end,
                    raw_output={"citation": matched_text, "found": False},
                ))
                continue

            # Match found — check case name consistency
            opinion = result.opinion
            doc_case_name = _extract_case_name_near_citation(text, start)

            if doc_case_name and opinion and opinion.case_name:
                # Simple case name comparison (normalized)
                doc_name_lower = doc_case_name.lower().strip()
                db_name_lower = opinion.case_name.lower().strip()

                # Check if key parts of case name match
                if not _case_names_match(doc_name_lower, db_name_lower):
                    flags.append(FlagResult(
                        evaluator=self.name,
                        evaluator_version=self.version,
                        severity=Severity.HIGH,
                        explanation=(
                            f"Citation '{matched_text}' resolves to "
                            f"'{opinion.case_name}', but the document references "
                            f"'{doc_case_name}'. Possible misattribution."
                        ),
                        confidence=0.8,
                        start_offset=start,
                        end_offset=end,
                        raw_output={
                            "citation": matched_text,
                            "found": True,
                            "db_case_name": opinion.case_name,
                            "doc_case_name": doc_case_name,
                        },
                    ))
                    continue

            # Everything checks out — ADVISORY (no issue)
            # We don't create ADVISORY flags for clean citations to avoid noise
            await logger.adebug(
                "citation_verified",
                citation=matched_text,
                case_name=opinion.case_name if opinion else None,
            )

        return flags


def _case_names_match(doc_name: str, db_name: str) -> bool:
    """Check if case names are substantially similar."""
    # Extract party names (before and after 'v.')
    doc_parts = re.split(r"\s+v\.?\s+", doc_name, maxsplit=1)
    db_parts = re.split(r"\s+v\.?\s+", db_name, maxsplit=1)

    if len(doc_parts) < 2 or len(db_parts) < 2:
        # Can't parse — give benefit of the doubt
        return True

    # Check if first party name appears in db name
    doc_plaintiff = doc_parts[0].strip().split()[-1]  # Last word of plaintiff
    doc_defendant = doc_parts[1].strip().split()[0]  # First word of defendant

    return doc_plaintiff in db_name or doc_defendant in db_name
