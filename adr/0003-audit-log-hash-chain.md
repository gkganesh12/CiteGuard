# Architecture Decision Record (ADR)

**Status: Accepted**

## ADR-0003: Audit Log Hash Chain

### Decision

We have decided to implement an **append-only, SHA-256 hash-chained audit log** with **`AuditLogService`** as the sole write path. Every state-changing action in the system writes a corresponding audit row in the same database transaction as the state change. The hash chain provides tamper-evident integrity verification.

### Context

- CiteGuard's audit trail is the core compliance artifact. Law firms use it to prove to malpractice carriers, bar associations, and courts that AI-generated output was properly reviewed before filing.
- Any tampering with the audit log — whether accidental or malicious — must be detectable. A broken hash chain is a P0 incident.
- The audit log must be append-only at the database level (not just the application level) to provide defense in depth against application bugs or compromised credentials.
- A single, controlled write path prevents bypass scenarios where code writes directly to the audit_log table without computing the hash chain.
- The system must support daily automated verification that re-computes the chain from genesis and alerts on any divergence.

### Rationale

#### SHA-256 Hash Chain
- SHA-256 is an industry-standard cryptographic hash function, widely trusted for integrity verification in financial, legal, and compliance contexts.
- Hash chaining (each row's hash includes the prior row's hash) provides a verifiable integrity guarantee: modifying any row invalidates all subsequent hashes.
- This approach provides tamper-evidence without the operational complexity of external blockchain or notarization services.

#### Append-Only Enforcement at DB Level
- `REVOKE UPDATE, DELETE ON audit_log FROM app_role` ensures that even if application code attempts to modify or delete audit rows, the database rejects the operation.
- This is defense in depth: the application layer (AuditLogService) also prevents modifications, but the DB-level enforcement catches bugs and compromised application code.

#### Single Write Path via AuditLogService
- All audit log writes go through `AuditLogService.append()`, which computes the hash chain, validates the payload, and writes within the caller's transaction.
- This prevents scenarios where different code paths compute hashes differently or skip hash computation entirely.
- The service is injected via dependency injection, making it easy to mock in tests while being impossible to bypass in production.

#### Daily Verification Job
- An automated daily job re-computes the entire hash chain from the genesis row and compares against stored hashes.
- Any divergence triggers a P0 alert. This catches corruption from hardware failures, backup restoration errors, or manual DB access.

### Implementation Details

#### Hash Computation Formula
- **Formula**: `this_hash = sha256(prior_hash || canonical_json(payload))`
- **Genesis row**: `prior_hash = sha256("")` (SHA-256 of empty string = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`)
- **Canonical JSON**: sorted keys, UTF-8 NFC normalization, stable numeric representation (no trailing zeros, no scientific notation for integers), no trailing whitespace.
- **Concatenation**: `prior_hash` (hex string) concatenated with canonical JSON string, then SHA-256 hashed.

#### AuditLogService Interface
- **`append(firm_id, user_id, event_type, entity_type, entity_id, payload, session)`**: The sole method for writing audit rows.
  - `session`: The SQLAlchemy async session from the caller's transaction. The audit row is written within this session, ensuring atomicity with the state change.
  - Fetches the most recent audit row for the firm to get `prior_hash`.
  - Computes `this_hash` using the formula above.
  - Inserts the audit row.
  - Returns the created audit row (including `this_hash`).
- **No other public write methods exist.** No `update()`, no `delete()`, no `bulk_insert()`.

#### Event Types
- **`document_submitted`**: A document is submitted for evaluation.
- **`evaluation_complete`**: All evaluators have finished processing a document.
- **`flag_created`**: An evaluator creates a flag on a document.
- **`flag_action_taken`**: A reviewer takes action on a flag (approve, override, reject, defer).
- **`document_finalized`**: A document is marked as resolved with all flags addressed.
- **`document_reopened`**: A finalized document is reopened for further review.
- **`export_generated`**: An audit PDF or report is exported.
- **`user_invited`**: A new user is invited to a firm.
- **`user_role_changed`**: A user's role within a firm is changed.
- **`api_key_created`**: A new API key is created for a firm.
- **`api_key_revoked`**: An API key is revoked (soft-deleted).
- **`firm_settings_updated`**: Firm-level settings are modified.

#### Daily Verification Job
- Runs as an Arq scheduled job at 02:00 UTC daily.
- For each firm: fetches all audit rows ordered by ULID (time-ordered), re-computes the hash chain from genesis, and compares each computed hash against the stored `this_hash`.
- On divergence: logs the first divergent row ID, marks the firm's chain as broken, and triggers a P0 alert via the configured alerting channel.
- Verification is read-only and does not modify any data.

#### Error Handling
- If `AuditLogService.append()` fails (e.g., DB connection error), the entire transaction (including the state change) rolls back. State changes without audit rows are not permitted.
- If the daily verification job fails to run, the missed run is detected by a separate heartbeat monitor and triggers an alert.

### Consequences

**Positive:**
- Tamper-evident audit trail: any modification to historical rows is detectable by re-computing the hash chain.
- Compliance-grade integrity: satisfies requirements from malpractice carriers and courts for verifiable AI review documentation.
- Defense in depth: DB-level REVOKE + application-level AuditLogService + daily verification provides three layers of protection.
- Atomic state changes: audit rows are written in the same transaction as the state change, so the system never has a state change without a corresponding audit entry (or vice versa).

**Challenges:**
- Append-only means no corrections: if an audit entry contains an error (e.g., wrong event_type due to a bug), the only recourse is to write a compensating entry. Historical rows cannot be modified.
- Daily verification adds operational load: re-computing the full chain for all firms grows linearly with audit log size. May need optimization (checkpointing) at scale.
- Canonical JSON serialization must be deterministic across Python versions: any change in JSON serialization behavior (e.g., float representation) would break chain verification. Pinned serialization logic with comprehensive tests is required.
- Per-firm chain ordering: concurrent audit writes within a single firm must be serialized to maintain chain integrity. This is handled by the database transaction isolation level (SERIALIZABLE for audit writes) but adds latency under high concurrency.

---

**Related Documents:**
- `docs/PRD_v1.md` — V1 product requirements (audit log as core artifact)
- `adr/0002-database-schema.md` — audit_log table definition
- `adr/0004-tenant-isolation.md` — firm_id scoping on audit_log
- `RnR/citeguard_backend_guidelines.md` — backend coding standards
- `RnR/citeguard_qa_rules.md` — testing requirements for audit log changes
