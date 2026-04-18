# Architecture Decision Record (ADR)

**Status: Accepted**

## ADR-0007: Privileged Data Handling

### Decision

We have decided that document content (text, prompts, completions, model outputs) must NEVER appear in logs, error tracking (Sentry), analytics (ClickHouse traces), error messages, toasts, URLs, page titles, browser history, localStorage, sessionStorage, IndexedDB, Zustand persist, or any third-party service beyond the declared LLM provider.

### Context

CiteGuard processes privileged attorney-client material. Exposure of this content anywhere outside the core data path constitutes a privilege waiver — a P0 incident that could destroy customer trust and trigger bar complaints.

- Attorney-client privilege is a foundational legal protection. Any inadvertent disclosure, even in an internal error log, could be argued as a waiver of privilege for that document.
- CiteGuard's customers are U.S. law firms handling sensitive litigation, regulatory, and transactional matters. A privilege waiver incident would be an existential threat to the product.
- Modern application stacks have many surfaces where content can leak: structured logs, exception trackers, analytics pipelines, browser storage, URL parameters, and page metadata.
- Compliance and audit requirements demand demonstrable controls — not just policies, but automated enforcement at multiple layers.
- The declared LLM provider is the only external service authorized to receive document content, and only the minimum necessary for evaluator processing.

### Rationale

#### Legal Basis
- Attorney-client privilege is absolute in U.S. law. Even accidental disclosure in internal systems can be used to argue waiver.
- Defense-in-depth is the only responsible approach: multiple independent layers must prevent leaks, so a single failure does not cause exposure.
- Regulatory frameworks (ABA Model Rules, state bar rules) require reasonable measures to protect client confidentiality in technology systems.

#### Technical Defense-in-Depth
- Backend log scrubbing catches content at the application layer before it reaches log storage.
- Sentry `beforeSend` callback provides a second line of defense at the error-tracking layer.
- Frontend ESLint rules catch developer mistakes at code-authoring time.
- Pre-commit hooks catch patterns in CI before code is merged.
- Staging test suites verify scrubbing works end-to-end before production deployment.

#### Data Minimization for External APIs
- CourtListener receives only citation strings (e.g., "410 U.S. 113"), never surrounding document text.
- FJC receives only judge names, never document context.
- This minimizes the blast radius if an external service is compromised.

### Implementation Details

#### Backend Logging (structlog)
- **Field Blocklist**: structlog configured to never log fields named `text`, `prompt`, `completion`, `document_text`, `content`, `body`, `raw_text`.
- **Processor Chain**: A custom structlog processor strips blocklisted fields from every log event before serialization.
- **Correlation**: All log entries include `document_id`, `firm_id`, `evaluator_name`, and `request_id` for debugging without document content.

#### Error Tracking (Sentry)
- **beforeSend Callback**: Strips blocklisted fields from exception data, breadcrumbs, and extra context before transmission to Sentry.
- **Scrubbing Verification**: Staging test suite sends synthetic exceptions containing document content and verifies they arrive at Sentry without content fields.
- **DSN Scoping**: Sentry DSN is environment-specific; production DSN has additional server-side scrubbing rules.

#### Analytics (ClickHouse)
- **Schema Enforcement**: ClickHouse tables contain only metadata columns: `document_id`, `firm_id`, `evaluator_name`, `latency_ms`, `severity`, `created_at`.
- **No Content Columns**: No column in any ClickHouse table accepts document text. Schema migrations are reviewed for this invariant.

#### Frontend Browser
- **URL Parameters**: No document content in URL params or path segments. Routes use `document_id` only.
- **Page Titles**: Display `document_id` or document name (user-provided label), never content preview.
- **Browser Storage**: No document content in `localStorage`, `sessionStorage`, `IndexedDB`, or Zustand persist stores. Document content lives only in component state (React memory) and is garbage-collected on unmount.
- **Console Logging**: ESLint custom rule (`no-privileged-console-log`) flags `console.log` calls that reference document content variables.

#### CI Enforcement
- **Pre-commit Hook**: Grep for patterns like `logger.info(document.text)`, `print(doc.content)`, `console.log(document.body)`. Fail the commit if matched.
- **CI Pipeline Step**: Same grep runs in CI as a dedicated step, blocking merge on violation.
- **Sentry Scrubbing Test**: CI runs a staging test that verifies Sentry `beforeSend` strips content fields from synthetic exceptions.

#### Data Residency
- **Primary Region**: `us-east-1` (AWS).
- **Standby Region**: `us-west-2` (AWS).
- **No Non-US Processing**: All data processing occurs within U.S. boundaries. No CDN edge function processes document content.

### Consequences

**Positive:**
- Privilege protection: Multiple independent layers ensure that no single failure results in content exposure.
- Compliance-ready: Automated enforcement provides auditable evidence of controls for bar inquiries and client due diligence.
- Defense-in-depth: Even if one layer fails (e.g., a developer bypasses the ESLint rule), backend scrubbing and Sentry callbacks provide backup.
- Customer trust: Firms can point to concrete technical controls when their own clients ask about data handling.
- US data residency: Eliminates concerns about cross-border data transfer for U.S. law firms.

**Challenges:**
- Debugging is harder without document content in logs: Engineers must reproduce issues using `document_id` correlation and test fixtures. Mitigation: maintain a set of representative test documents that can be used locally.
- Error reports are less descriptive: Sentry exceptions lack the context that would come from including document excerpts. Mitigation: include metadata (document_id, evaluator_name, severity, error code) and require reproduction steps in bug reports.
- Developer friction: Pre-commit hooks and ESLint rules may flag false positives (e.g., a variable named `content` that is not document content). Mitigation: allow targeted `// eslint-disable-next-line` with mandatory comment explaining why the variable is safe.
- Performance overhead: structlog processor runs on every log event. Mitigation: blocklist check is O(1) hash lookup per field; negligible overhead.

---

**Date:** 2026-04-18
**Supersedes:** None
**Related ADRs:** ADR-0006 (Authentication and Authorization), ADR-0008 (External API Integration Strategy)
