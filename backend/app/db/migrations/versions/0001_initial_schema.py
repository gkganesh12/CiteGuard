"""Initial schema — all 8 core tables

Revision ID: 0001
Revises: None
Create Date: 2026-04-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum types
user_role = postgresql.ENUM("admin", "reviewer", "submitter", name="user_role", create_type=False)
document_status = postgresql.ENUM(
    "pending", "in_review", "resolved", name="document_status", create_type=False
)
document_type = postgresql.ENUM(
    "brief", "memo", "contract", "other", name="document_type", create_type=False
)
severity = postgresql.ENUM(
    "CRITICAL", "HIGH", "MEDIUM", "ADVISORY", name="severity", create_type=False
)
evaluator_type = postgresql.ENUM(
    "citation_existence",
    "quote_verification",
    "bluebook_format",
    "judge_verification",
    "temporal_validity",
    name="evaluator_type",
    create_type=False,
)
reviewer_action_type = postgresql.ENUM(
    "approve", "override", "reject", "defer", name="reviewer_action_type", create_type=False
)
audit_event_type = postgresql.ENUM(
    "document_submitted",
    "evaluation_complete",
    "flag_created",
    "flag_action_taken",
    "document_finalized",
    "document_reopened",
    "export_generated",
    "user_invited",
    "user_role_changed",
    "user_removed",
    "api_key_created",
    "api_key_revoked",
    "firm_created",
    "firm_settings_updated",
    name="audit_event_type",
    create_type=False,
)


def upgrade() -> None:
    # Create enum types
    user_role.create(op.get_bind(), checkfirst=True)
    document_status.create(op.get_bind(), checkfirst=True)
    document_type.create(op.get_bind(), checkfirst=True)
    severity.create(op.get_bind(), checkfirst=True)
    evaluator_type.create(op.get_bind(), checkfirst=True)
    reviewer_action_type.create(op.get_bind(), checkfirst=True)
    audit_event_type.create(op.get_bind(), checkfirst=True)

    # 1. firms
    op.create_table(
        "firms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("billing_email", sa.String(255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("settings", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # 2. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "firm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("firms.id"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="submitter"),
        sa.Column("clerk_user_id", sa.String(255), nullable=True, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_firm_id", "users", ["firm_id"])

    # 3. api_keys
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "firm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("firms.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_api_keys_firm_id", "api_keys", ["firm_id"])

    # 4. documents
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "firm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("firms.id"),
            nullable=False,
        ),
        sa.Column(
            "submitter_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("document_type", document_type, nullable=False, server_default="other"),
        sa.Column("llm_provider", sa.String(100), nullable=True),
        sa.Column("llm_model", sa.String(100), nullable=True),
        sa.Column("prompt", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("status", document_status, nullable=False, server_default="pending"),
        sa.Column("idempotency_key", sa.String(255), nullable=True, unique=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_documents_firm_id", "documents", ["firm_id"])
    op.create_index(
        "ix_documents_firm_status_created",
        "documents",
        ["firm_id", "status", "submitted_at"],
    )

    # 5. flags
    op.create_table(
        "flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column("evaluator", evaluator_type, nullable=False),
        sa.Column("evaluator_version", sa.Text, nullable=True),
        sa.Column("severity", severity, nullable=False),
        sa.Column("explanation", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("start_offset", sa.Integer, nullable=True),
        sa.Column("end_offset", sa.Integer, nullable=True),
        sa.Column("suggested_correction", sa.Text, nullable=True),
        sa.Column("raw_evaluator_output", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_flags_document_id", "flags", ["document_id"])

    # 6. reviewer_actions
    op.create_table(
        "reviewer_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "flag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flags.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("action", reviewer_action_type, nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_reviewer_actions_flag_id", "reviewer_actions", ["flag_id"])

    # 7. audit_log (APPEND-ONLY — CRITICAL)
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "firm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("firms.id"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=True,
        ),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("prior_hash", sa.String(64), nullable=False),
        sa.Column("this_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_log_firm_id", "audit_log", ["firm_id"])
    op.create_index("ix_audit_log_firm_created", "audit_log", ["firm_id", "created_at"])

    # CRITICAL: Revoke UPDATE and DELETE on audit_log for the application role.
    # This enforces append-only at the database level.
    # NOTE: In production, create a separate DB role for the app (e.g., citeguard_app)
    # and run: REVOKE UPDATE, DELETE ON audit_log FROM citeguard_app;
    # For development, we add a comment as a reminder.
    op.execute(
        "COMMENT ON TABLE audit_log IS "
        "'APPEND-ONLY: UPDATE and DELETE must be REVOKED for the application DB role. "
        "All writes must go through AuditLogService.';"
    )

    # 8. exports
    op.create_table(
        "exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("pdf_path", sa.String(1024), nullable=False),
        sa.Column("pdf_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_exports_document_id", "exports", ["document_id"])


def downgrade() -> None:
    op.drop_table("exports")
    op.drop_table("audit_log")
    op.drop_table("reviewer_actions")
    op.drop_table("flags")
    op.drop_table("documents")
    op.drop_table("api_keys")
    op.drop_table("users")
    op.drop_table("firms")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS audit_event_type")
    op.execute("DROP TYPE IF EXISTS reviewer_action_type")
    op.execute("DROP TYPE IF EXISTS evaluator_type")
    op.execute("DROP TYPE IF EXISTS severity")
    op.execute("DROP TYPE IF EXISTS document_type")
    op.execute("DROP TYPE IF EXISTS document_status")
    op.execute("DROP TYPE IF EXISTS user_role")
