"""Evaluator pipeline worker task.

Invoked asynchronously when a document is submitted. Runs all registered
evaluators in parallel, writes flags to the database, and updates
document status.
"""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import audit_log_service
from app.evaluators.base import EvaluationContext, FlagResult
from app.evaluators.bluebook_format import BluebookFormatEvaluator
from app.evaluators.citation_existence import CitationExistenceEvaluator
from app.evaluators.judge_verification import JudgeVerificationEvaluator
from app.evaluators.orchestrator import EvaluatorOrchestrator
from app.evaluators.quote_verification import QuoteVerificationEvaluator
from app.evaluators.temporal_validity import TemporalValidityEvaluator
from app.models.document import Document
from app.models.enums import AuditEventType, DocumentStatus
from app.models.flag import Flag

logger = structlog.get_logger()


def _build_orchestrator() -> EvaluatorOrchestrator:
    """Create and configure the evaluator orchestrator with all V1 evaluators."""
    orchestrator = EvaluatorOrchestrator(timeout=10.0)
    orchestrator.register(CitationExistenceEvaluator())
    orchestrator.register(QuoteVerificationEvaluator())
    orchestrator.register(BluebookFormatEvaluator())
    orchestrator.register(JudgeVerificationEvaluator())
    orchestrator.register(TemporalValidityEvaluator())
    return orchestrator


async def run_evaluators(
    ctx: dict,  # type: ignore[type-arg]
    document_id: str,
    firm_id: str,
) -> None:
    """Run all evaluators on a document and persist results.

    Called by Arq worker. Retrieves document from DB, runs evaluators,
    writes flags, updates document status, and creates audit entries.
    """
    session_factory = ctx["db_session_factory"]
    doc_uuid = uuid.UUID(document_id)
    firm_uuid = uuid.UUID(firm_id)

    async with session_factory() as session:
        # Fetch document
        stmt = select(Document).where(
            Document.id == doc_uuid,
            Document.firm_id == firm_uuid,
        )
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()

        if not doc:
            await logger.aerror(
                "evaluator_run_document_not_found",
                document_id=document_id,
                firm_id=firm_id,
            )
            return

        await logger.ainfo(
            "evaluator_run_starting",
            document_id=document_id,
            firm_id=firm_id,
        )

        # Build context
        context = EvaluationContext(
            document_id=doc.id,
            firm_id=doc.firm_id,
            document_type=doc.document_type.value,
        )

        # Run all evaluators
        orchestrator = _build_orchestrator()
        flag_results = await orchestrator.run_all(doc.text, context)

        # Persist flags and update document in a single transaction
        async with session.begin():
            for fr in flag_results:
                flag = Flag(
                    document_id=doc.id,
                    evaluator=fr.evaluator,
                    evaluator_version=fr.evaluator_version,
                    severity=fr.severity,
                    explanation=fr.explanation,
                    confidence=fr.confidence,
                    start_offset=fr.start_offset,
                    end_offset=fr.end_offset,
                    suggested_correction=fr.suggested_correction,
                    raw_evaluator_output=fr.raw_output,
                )
                session.add(flag)

            # Update document status
            doc.status = DocumentStatus.IN_REVIEW

            # Write audit entry for evaluation completion
            severity_summary = _summarize_severities(flag_results)
            await audit_log_service.append(
                session=session,
                firm_id=firm_uuid,
                event_type=AuditEventType.EVALUATION_COMPLETE,
                document_id=doc.id,
                payload={
                    "document_id": document_id,
                    "flags_created": len(flag_results),
                    "severity_summary": severity_summary,
                    "evaluators_run": list({fr.evaluator.value for fr in flag_results}),
                },
            )

        await logger.ainfo(
            "evaluator_run_complete",
            document_id=document_id,
            flags_created=len(flag_results),
            severity_summary=severity_summary,
        )


def _summarize_severities(flags: list[FlagResult]) -> dict[str, int]:
    summary: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "advisory": 0}
    for f in flags:
        key = f.severity.value.lower()
        if key in summary:
            summary[key] += 1
    return summary
