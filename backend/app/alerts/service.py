"""Alert service — Slack webhooks and email notifications.

Sends alerts when CRITICAL flags are detected:
- Slack: webhook POST within 60 seconds of CRITICAL flag
- Email: batched every 10 minutes for configured severity threshold
"""

from __future__ import annotations

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()


class SlackNotifier:
    """Sends Slack webhook alerts for CRITICAL flags."""

    async def send_alert(
        self,
        webhook_url: str,
        document_id: str,
        submitter: str,
        flag_summary: dict[str, int],
        review_url: str,
    ) -> bool:
        """Send a Slack alert for a flagged document."""
        critical_count = flag_summary.get("critical", 0)
        high_count = flag_summary.get("high", 0)

        text = (
            f"*CiteGuard Alert*\n"
            f"Document `{document_id}` has been flagged.\n"
            f"Submitted by: {submitter}\n"
            f"*{critical_count} CRITICAL* | {high_count} HIGH\n"
            f"<{review_url}|Review now>"
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    webhook_url,
                    json={"text": text},
                )
                resp.raise_for_status()
                return True
        except Exception as exc:
            await logger.aerror(
                "slack_alert_failed",
                document_id=document_id,
                error=str(exc),
            )
            return False


class EmailNotifier:
    """Sends batched email alerts (placeholder — uses Resend/Postmark in production)."""

    async def send_alert(
        self,
        to_email: str,
        document_id: str,
        flag_summary: dict[str, int],
    ) -> bool:
        """Send an email alert. Placeholder for Resend/Postmark integration."""
        await logger.ainfo(
            "email_alert_queued",
            to=to_email,
            document_id=document_id,
            summary=flag_summary,
        )
        # TODO: Integrate with Resend or Postmark
        return True


slack_notifier = SlackNotifier()
email_notifier = EmailNotifier()
