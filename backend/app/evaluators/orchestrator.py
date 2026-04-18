"""EvaluatorOrchestrator — runs all evaluators in parallel via asyncio.gather.

Key behaviors:
- All evaluators run concurrently (asyncio.gather)
- Per-evaluator timeout (default 10s)
- Exceptions converted to ADVISORY flags (failure-as-ADVISORY)
- Results collected and returned as a flat list of FlagResult
"""

from __future__ import annotations

import asyncio

import structlog

from app.evaluators.base import EvaluationContext, FlagResult, IEvaluator
from app.models.enums import Severity

logger = structlog.get_logger()

DEFAULT_TIMEOUT_SECONDS = 10


class EvaluatorOrchestrator:
    """Orchestrates parallel execution of all registered evaluators."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._evaluators: list[IEvaluator] = []
        self._timeout = timeout

    def register(self, evaluator: IEvaluator) -> None:
        self._evaluators.append(evaluator)

    async def run_all(
        self, text: str, context: EvaluationContext
    ) -> list[FlagResult]:
        """Run all registered evaluators in parallel and collect results."""
        if not self._evaluators:
            return []

        tasks = [
            self._run_with_timeout(evaluator, text, context)
            for evaluator in self._evaluators
        ]

        results = await asyncio.gather(*tasks)

        # Flatten results from all evaluators
        all_flags: list[FlagResult] = []
        for evaluator_flags in results:
            all_flags.extend(evaluator_flags)

        await logger.ainfo(
            "evaluation_complete",
            document_id=str(context.document_id),
            total_flags=len(all_flags),
            evaluators_run=len(self._evaluators),
        )

        return all_flags

    async def _run_with_timeout(
        self,
        evaluator: IEvaluator,
        text: str,
        context: EvaluationContext,
    ) -> list[FlagResult]:
        """Run a single evaluator with timeout and error handling."""
        try:
            return await asyncio.wait_for(
                evaluator.evaluate(text, context),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            await logger.awarning(
                "evaluator_timeout",
                evaluator=evaluator.name.value,
                version=evaluator.version,
                document_id=str(context.document_id),
                timeout_seconds=self._timeout,
            )
            return [
                FlagResult(
                    evaluator=evaluator.name,
                    evaluator_version=evaluator.version,
                    severity=Severity.ADVISORY,
                    explanation=(
                        f"Evaluator '{evaluator.name.value}' timed out after "
                        f"{self._timeout}s. Results unavailable for this run."
                    ),
                    confidence=0.0,
                    raw_output={"error": "timeout"},
                )
            ]
        except Exception as exc:
            await logger.aerror(
                "evaluator_error",
                evaluator=evaluator.name.value,
                version=evaluator.version,
                document_id=str(context.document_id),
                error=str(exc),
            )
            return [
                FlagResult(
                    evaluator=evaluator.name,
                    evaluator_version=evaluator.version,
                    severity=Severity.ADVISORY,
                    explanation=(
                        f"Evaluator '{evaluator.name.value}' encountered an error. "
                        f"Results unavailable for this run."
                    ),
                    confidence=0.0,
                    raw_output={"error": str(exc)},
                )
            ]
