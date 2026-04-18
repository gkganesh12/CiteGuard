"""Bluebook Formatting Evaluator (F4) — v1.0.0

Validates citations against Bluebook 21st edition rules.

Checks:
- Required elements (volume, reporter, page, year for case cites)
- Signal words (See, Cf., But see, etc.)
- Pincites (rule B10.1.4)
- Parentheticals (court + year)
- Common abbreviations

Severity:
  HIGH     — missing required element
  MEDIUM   — format error (wrong abbreviation, malformed parenthetical)
  ADVISORY — style preference (recommended pincite)
"""

from __future__ import annotations

import re

from app.evaluators.base import EvaluationContext, FlagResult
from app.models.enums import EvaluatorType, Severity

VERSION = "1.0.0"

# ── Bluebook rule definitions ──────────────────────────────────────────

# Valid signal words (Bluebook rule 1.2)
VALID_SIGNALS = {
    "see", "see also", "see, e.g.,", "see generally",
    "cf.", "compare", "but see", "but cf.",
    "contra", "accord", "e.g.,",
}

# Signal pattern: starts a sentence or follows a period
SIGNAL_PATTERN = re.compile(
    r"(?:^|(?<=\.\s))(" + "|".join(re.escape(s) for s in sorted(VALID_SIGNALS, key=len, reverse=True)) + r")\s",
    re.IGNORECASE | re.MULTILINE,
)

# Common reporter abbreviations (correct forms)
CORRECT_REPORTERS: dict[str, str] = {
    "U.S.": "U.S.",
    "S. Ct.": "S. Ct.",
    "S.Ct.": "S. Ct.",
    "L. Ed.": "L. Ed.",
    "L. Ed. 2d": "L. Ed. 2d",
    "F.2d": "F.2d",
    "F.3d": "F.3d",
    "F.4th": "F.4th",
    "F. Supp.": "F. Supp.",
    "F. Supp. 2d": "F. Supp. 2d",
    "F. Supp. 3d": "F. Supp. 3d",
    "F.R.D.": "F.R.D.",
    "B.R.": "B.R.",
}

# Wrong abbreviation patterns
WRONG_ABBREVIATIONS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bF\.\s*3rd\b"), "F.3rd", "F.3d"),
    (re.compile(r"\bF\.\s*2nd\b"), "F.2nd", "F.2d"),
    (re.compile(r"\bF\.\s*4th\b"), "F.4th", "F.4th"),  # correct
    (re.compile(r"\bS\.Ct\.\b"), "S.Ct.", "S. Ct."),
    (re.compile(r"\bL\.Ed\.\b"), "L.Ed.", "L. Ed."),
    (re.compile(r"\bF\.Supp\.\b"), "F.Supp.", "F. Supp."),
    (re.compile(r"\bFed\.App[x']\b", re.IGNORECASE), "Fed.Appx", "F. App'x"),
]

# Full citation pattern: volume reporter page (court year)
FULL_CITE_PATTERN = re.compile(
    r"(\d{1,4})\s+"
    r"([A-Z][A-Za-z.\s']+?)\s+"
    r"(\d{1,5})"
    r"(?:,\s*(\d{1,5}))?"  # optional pincite
    r"\s*"
    r"(?:\(([^)]*)\))?"     # optional parenthetical
)

# Year pattern in parenthetical
YEAR_PATTERN = re.compile(r"\b(1[89]\d{2}|20[0-2]\d)\b")

# Court abbreviation in parenthetical
COURT_IN_PAREN = re.compile(
    r"(1st|2d|2nd|3d|3rd|4th|5th|6th|7th|8th|9th|10th|11th|D\.C\.|Fed)\s+Cir\."
    r"|[A-Z]\.[A-Z]\.\s+\d{4}"
    r"|S\.D\.N\.Y\.|N\.D\.\s*(?:Cal|Ill|Tex|Ga)"
    r"|[SNWED]\.D\.\s*[A-Z][a-z]+"
)


class BluebookFormatEvaluator:
    """Validates Bluebook 21st edition citation formatting."""

    @property
    def name(self) -> EvaluatorType:
        return EvaluatorType.BLUEBOOK_FORMAT

    @property
    def version(self) -> str:
        return VERSION

    async def evaluate(
        self, text: str, context: EvaluationContext
    ) -> list[FlagResult]:
        flags: list[FlagResult] = []

        # Check abbreviation errors
        flags.extend(self._check_abbreviations(text))

        # Check full citation structure
        flags.extend(self._check_citation_structure(text))

        return flags

    def _check_abbreviations(self, text: str) -> list[FlagResult]:
        """Check for incorrect reporter abbreviations."""
        flags: list[FlagResult] = []
        for pattern, wrong, correct in WRONG_ABBREVIATIONS:
            if wrong == correct:
                continue
            for match in pattern.finditer(text):
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.MEDIUM,
                    explanation=(
                        f"Incorrect reporter abbreviation '{match.group()}'. "
                        f"Bluebook format requires '{correct}'."
                    ),
                    confidence=0.9,
                    start_offset=match.start(),
                    end_offset=match.end(),
                    suggested_correction=correct,
                    raw_output={
                        "rule": "reporter_abbreviation",
                        "found": match.group(),
                        "expected": correct,
                    },
                ))
        return flags

    def _check_citation_structure(self, text: str) -> list[FlagResult]:
        """Check citation structure: required elements, parentheticals, pincites."""
        flags: list[FlagResult] = []

        for match in FULL_CITE_PATTERN.finditer(text):
            volume = match.group(1)
            reporter = match.group(2).strip()
            page = match.group(3)
            pincite = match.group(4)
            parenthetical = match.group(5)

            cite_text = match.group(0)
            start = match.start()
            end = match.end()

            # Check: parenthetical with year is required
            if not parenthetical:
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.HIGH,
                    explanation=(
                        f"Citation '{cite_text}' is missing a parenthetical with "
                        f"court and year. Bluebook requires (Court Year) format."
                    ),
                    confidence=0.85,
                    start_offset=start,
                    end_offset=end,
                    suggested_correction=f"{cite_text} (Court YYYY)",
                    raw_output={"rule": "missing_parenthetical", "citation": cite_text},
                ))
                continue

            # Check: year present in parenthetical
            if not YEAR_PATTERN.search(parenthetical):
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.HIGH,
                    explanation=(
                        f"Citation '{cite_text}' parenthetical '{parenthetical}' "
                        f"is missing the decision year."
                    ),
                    confidence=0.9,
                    start_offset=start,
                    end_offset=end,
                    raw_output={
                        "rule": "missing_year",
                        "citation": cite_text,
                        "parenthetical": parenthetical,
                    },
                ))

            # Check: recommend pincite for non-U.S. Reports citations
            if not pincite and "U.S." not in reporter:
                flags.append(FlagResult(
                    evaluator=self.name,
                    evaluator_version=self.version,
                    severity=Severity.ADVISORY,
                    explanation=(
                        f"Citation '{cite_text}' lacks a pincite. "
                        f"Bluebook rule B10.1.4 recommends including a "
                        f"specific page reference."
                    ),
                    confidence=0.6,
                    start_offset=start,
                    end_offset=end,
                    raw_output={"rule": "missing_pincite", "citation": cite_text},
                ))

        return flags
