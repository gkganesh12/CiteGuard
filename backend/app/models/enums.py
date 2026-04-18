import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    SUBMITTER = "submitter"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"


class DocumentType(str, enum.Enum):
    BRIEF = "brief"
    MEMO = "memo"
    CONTRACT = "contract"
    OTHER = "other"


class Severity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    ADVISORY = "ADVISORY"


class EvaluatorType(str, enum.Enum):
    CITATION_EXISTENCE = "citation_existence"
    QUOTE_VERIFICATION = "quote_verification"
    BLUEBOOK_FORMAT = "bluebook_format"
    JUDGE_VERIFICATION = "judge_verification"
    TEMPORAL_VALIDITY = "temporal_validity"


class ReviewerActionType(str, enum.Enum):
    APPROVE = "approve"
    OVERRIDE = "override"
    REJECT = "reject"
    DEFER = "defer"


class AuditEventType(str, enum.Enum):
    # Document lifecycle
    DOCUMENT_SUBMITTED = "document_submitted"
    EVALUATION_COMPLETE = "evaluation_complete"
    FLAG_CREATED = "flag_created"
    FLAG_ACTION_TAKEN = "flag_action_taken"
    DOCUMENT_FINALIZED = "document_finalized"
    DOCUMENT_REOPENED = "document_reopened"
    EXPORT_GENERATED = "export_generated"

    # User management
    USER_INVITED = "user_invited"
    USER_ROLE_CHANGED = "user_role_changed"
    USER_REMOVED = "user_removed"

    # API keys
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"

    # Firm
    FIRM_CREATED = "firm_created"
    FIRM_SETTINGS_UPDATED = "firm_settings_updated"
