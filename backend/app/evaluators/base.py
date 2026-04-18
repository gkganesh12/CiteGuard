"""Evaluator base protocol and common types.

Every evaluator implements the IEvaluator protocol. Evaluators are:
- Independent (one failure doesn't block others)
- Versioned (every logic change bumps version)
- Testable against a fixed corpus
- Failures produce ADVISORY flags, not hard errors
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.models.enums import EvaluatorType, Severity


@dataclass(frozen=True)
class FlagResult:
    """Output from a single evaluator finding."""

    evaluator: EvaluatorType
    evaluator_version: str
    severity: Severity
    explanation: str
    confidence: float  # 0.0 to 1.0
    start_offset: int | None = None
    end_offset: int | None = None
    suggested_correction: str | None = None
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationContext:
    """Context passed to every evaluator alongside the document."""

    document_id: uuid.UUID
    firm_id: uuid.UUID
    document_type: str


@runtime_checkable
class IEvaluator(Protocol):
    """Protocol that every evaluator must implement."""

    @property
    def name(self) -> EvaluatorType: ...

    @property
    def version(self) -> str: ...

    async def evaluate(
        self, text: str, context: EvaluationContext
    ) -> list[FlagResult]: ...
