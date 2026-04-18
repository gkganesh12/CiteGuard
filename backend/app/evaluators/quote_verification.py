"""Quote Verification Evaluator (F3) — v1.0.0

Verifies that every quoted passage followed by a case citation
actually appears in the cited opinion.

Severity:
  CRITICAL — quoted passage does not appear in cited opinion (fabricated quote)
  HIGH     — passage appears but with significant alterations
  ADVISORY — passage matches within threshold

Uses rapidfuzz for fuzzy substring matching (85% similarity threshold).
"""

from __future__ import annotations

import re

import structlog

from app.evaluators.base import EvaluationContext, FlagResult
from app.evaluators.citation_existence import _parse_citations
from app.integrations.courtlistener.client import courtlistener_client
from app.models.enums import EvaluatorType, Severity

logger = structlog.get_logger()

VERSION = "1.0.0"
SIMILARITY_THRESHOLD = 85  # rapidfuzz partial_ratio threshold
MIN_QUOTE_LENGTH = 20  # Ignore very short quotes
MAX_CITATION_DISTANCE = 200  # Max chars between quote end and citation

# Pattern to find quoted passages
QUOTE_PATTERN = re.compile(
    r'["\u201c]'     # Opening quote (straight or curly)
    r'([^"\u201d]+)'  # Content
    r'["\u201d]',     # Closing quote
    re.DOTALL,
)


def _find_quoted_passages_with_citations(text: str) -> list[dict]:
    """Find quoted passages followed by a case citation within 200 characters.

    Returns list of dicts: {quote, quote_start, quote_end, citation, cite_volume,
    cite_reporter, cite_page}
    """
    quotes = list(QUOTE_PATTERN.finditer(text))
    citations = _parse_citations(text)
    paired: list[dict] = []

    for quote_match in quotes:
        quote_text = quote_match.group(1).strip()
        quote_end = quote_match.end()

        if len(quote_text) < MIN_QUOTE_LENGTH:
            continue

        # Find nearest citation after quote (within MAX_CITATION_DISTANCE chars)
        for cite in citations:
            cite_start = int(cite.get("start", 0))
            if 0 < cite_start - quote_end <= MAX_CITATION_DISTANCE:
                paired.append({
                    "quote": quote_text,
                    "quote_start": quote_match.start(),
                    "quote_end": quote_end,
                    "citation": cite,
                })
                break  # Pair with nearest citation only

    return paired


def _normalize_text(text: str) -> str:
    """Normalize whitespace and punctuation for comparison."""
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Normalize quotes
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    # Remove ellipses markers commonly used in legal quotes
    text = re.sub(r"\s*\.\.\.\s*", " ", text)
    text = re.sub(r"\s*\[\.\.\.\]\s*", " ", text)
    return text.lower()


def _fuzzy_match(quote: str, opinion_text: str) -> tuple[float, str]:
    """Perform fuzzy substring match of quote against opinion text.

    Returns (similarity_score, best_matching_passage).
    """
    try:
        from rapidfuzz import fuzz

        normalized_quote = _normalize_text(quote)
        normalized_opinion = _normalize_text(opinion_text)

        score = fuzz.partial_ratio(normalized_quote, normalized_opinion)

        # Extract the best matching window from the opinion
        best_passage = ""
        if score > 0:
            # Find approximate location of best match
            quote_len = len(normalized_quote)
            best_start = 0
            best_score = 0
            step = max(1, quote_len // 4)

            for i in range(0, len(normalized_opinion) - quote_len + 1, step):
                window = normalized_opinion[i : i + quote_len + 50]
                window_score = fuzz.ratio(normalized_quote, window)
                if window_score > best_score:
                    best_score = window_score
                    best_start = i

            best_passage = opinion_text[best_start : best_start + len(quote) + 50].strip()

        return float(score), best_passage

    except ImportError:
        # Fallback: simple substring check
        if _normalize_text(quote) in _normalize_text(opinion_text):
            return 100.0, quote
        return 0.0, ""


class QuoteVerificationEvaluator:
    """Verifies quoted passages against source opinions."""

    @property
    def name(self) -> EvaluatorType:
        return EvaluatorType.QUOTE_VERIFICATION

    @property
    def version(self) -> str:
        return VERSION

    async def evaluate(
        self, text: str, context: EvaluationContext
    ) -> list[FlagResult]:
        paired = _find_quoted_passages_with_citations(text)
        if not paired:
            return []

        flags: list[FlagResult] = []

        for item in paired:
            quote = item["quote"]
            cite = item["citation"]
            quote_start = item["quote_start"]
            quote_end = item["quote_end"]
            matched_cite = str(cite.get("matched_text", ""))

            # Resolve citation to get opinion
            result = await courtlistener_client.resolve_citation(
                volume=str(cite["volume"]),
                reporter=str(cite["reporter"]),
                page=str(cite["page"]),
            )

            if not result.found or not result.opinion:
                # Can't verify quote if citation doesn't resolve
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.CRITICAL,
                    explanation=(
                        f"Cannot verify quote — citation '{matched_cite}' "
                        f"does not resolve to a known opinion."
                    ),
                    confidence=0.9,
                    start_offset=quote_start,
                    end_offset=quote_end,
                    raw_output={
                        "quote_preview": quote[:100],
                        "citation": matched_cite,
                        "reason": "citation_not_found",
                    },
                ))
                continue

            # Fetch full opinion text
            opinion_text = await courtlistener_client.fetch_opinion_text(
                result.opinion.id
            )

            if not opinion_text:
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.ADVISORY,
                    explanation=(
                        f"Quote verification unavailable — opinion text for "
                        f"'{matched_cite}' could not be retrieved."
                    ),
                    confidence=0.0,
                    start_offset=quote_start,
                    end_offset=quote_end,
                    raw_output={
                        "quote_preview": quote[:100],
                        "citation": matched_cite,
                        "reason": "opinion_text_unavailable",
                    },
                ))
                continue

            # Fuzzy match
            score, best_passage = _fuzzy_match(quote, opinion_text)

            if score < 50:
                # Very low match — likely fabricated
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.CRITICAL,
                    explanation=(
                        f"Quoted passage does not appear in '{matched_cite}' "
                        f"(similarity: {score:.0f}%). This quote may be fabricated."
                    ),
                    confidence=0.95,
                    start_offset=quote_start,
                    end_offset=quote_end,
                    raw_output={
                        "quote_preview": quote[:100],
                        "citation": matched_cite,
                        "similarity_score": score,
                        "closest_passage": best_passage[:200] if best_passage else None,
                    },
                ))
            elif score < SIMILARITY_THRESHOLD:
                # Moderate match — significant alterations
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.HIGH,
                    explanation=(
                        f"Quoted passage from '{matched_cite}' has significant "
                        f"alterations (similarity: {score:.0f}%). "
                        f"Review against source opinion."
                    ),
                    confidence=0.8,
                    start_offset=quote_start,
                    end_offset=quote_end,
                    suggested_correction=best_passage[:500] if best_passage else None,
                    raw_output={
                        "quote_preview": quote[:100],
                        "citation": matched_cite,
                        "similarity_score": score,
                        "closest_passage": best_passage[:200] if best_passage else None,
                    },
                ))
            # else: score >= SIMILARITY_THRESHOLD — match confirmed, no flag

        return flags
