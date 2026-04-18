# Architecture Decision Record (ADR)

**Status: Accepted**

## ADR-0002: Database Schema Design

### Decision

We have decided to implement **8 core tables** — `firms`, `users`, `api_keys`, `documents`, `flags`, `reviewer_actions`, `audit_log`, and `exports` — with **UUID/ULID primary keys**, **firm_id foreign keys** on every tenant-scoped table for isolation, and an **append-only audit_log** with SHA-256 hash chain.

### Context

- CiteGuard's audit log is the core product artifact — it must have ACID guarantees for hash-chain integrity. Any partial write or read anomaly would break the chain and undermine the compliance value of the product.
- Multi-tenant isolation via `firm_id` on every table is mandatory. Firm A must never see Firm B's data. A tenant isolation failure is an existential risk (privilege waivers, malpractice exposure).
- The schema must support the full document lifecycle: submission, evaluation, review (approve/override/reject/defer), finalization, and export.
- Evaluator output varies by evaluator type and version, requiring flexible storage (JSONB) while maintaining queryability.
- Queue performance is critical: reviewers need fast access to their pending documents, filtered by firm, status, and creation time.

### Rationale

#### Single Postgres Instance with Tenant Scoping
- A single PostgreSQL 16 instance with `firm_id` on every tenant-scoped table provides strong isolation without the operational complexity of per-tenant databases.
- RLS-compatible schema design allows future migration to Row-Level Security if needed.
- Composite indexes on `(firm_id, status, created_at)` ensure queue queries are fast even as document volume grows.

#### ULID for Audit Log, UUID for Other Tables
- ULID (Universally Unique Lexicographically Sortable Identifier) on `audit_log` provides time-ordered IDs, which simplifies chain verification and time-range queries.
- UUID v4 on other tables provides standard uniqueness without ordering requirements.

#### JSONB for Flexible Metadata
- Evaluator output structure varies by evaluator type and version. JSONB allows schema evolution without migrations.
- Document metadata (page count, word count, source system) varies by submission method. JSONB accommodates this flexibility.
- JSONB supports GIN indexes for queryability when needed.

#### Append-Only Audit Log
- `REVOKE UPDATE, DELETE` at the database role level makes the audit log physically append-only — no application code can accidentally modify or delete historical entries.
- This is enforced at the DB layer, not the application layer, providing defense in depth.

### Implementation Details

#### Table Definitions

##### `firms`
- **id**: UUID, primary key
- **name**: VARCHAR(255), NOT NULL
- **slug**: VARCHAR(100), UNIQUE, NOT NULL
- **settings**: JSONB, DEFAULT '{}'
- **created_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **updated_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()

##### `users`
- **id**: UUID, primary key
- **firm_id**: UUID, FK to firms(id), NOT NULL
- **clerk_id**: VARCHAR(255), UNIQUE, NOT NULL
- **email**: VARCHAR(255), NOT NULL
- **role**: ENUM('admin', 'reviewer', 'submitter'), NOT NULL
- **deleted_at**: TIMESTAMPTZ, nullable (soft delete)
- **created_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **updated_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **Index**: `(firm_id, email)` UNIQUE WHERE deleted_at IS NULL

##### `api_keys`
- **id**: UUID, primary key
- **firm_id**: UUID, FK to firms(id), NOT NULL
- **created_by**: UUID, FK to users(id), NOT NULL
- **key_hash**: VARCHAR(64), NOT NULL (SHA-256 of the API key; raw key never stored)
- **key_prefix**: VARCHAR(8), NOT NULL (for identification in UI)
- **label**: VARCHAR(255)
- **deleted_at**: TIMESTAMPTZ, nullable (soft delete / revocation)
- **created_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **Index**: `(key_hash)` UNIQUE

##### `documents`
- **id**: UUID, primary key
- **firm_id**: UUID, FK to firms(id), NOT NULL
- **submitted_by**: UUID, FK to users(id), NOT NULL
- **title**: VARCHAR(500)
- **status**: ENUM('pending', 'in_review', 'resolved'), NOT NULL, DEFAULT 'pending'
- **metadata**: JSONB, DEFAULT '{}'
- **flag_summary**: JSONB, DEFAULT '{}' (denormalized counts by severity)
- **created_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **updated_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **finalized_at**: TIMESTAMPTZ, nullable
- **Index**: `(firm_id, status, created_at)` for queue queries

##### `flags`
- **id**: UUID, primary key
- **document_id**: UUID, FK to documents(id), NOT NULL
- **firm_id**: UUID, FK to firms(id), NOT NULL (denormalized for query performance)
- **evaluator_type**: ENUM('citation_existence', 'quote_verification', 'bluebook_format', 'judge_verification', 'temporal_validity'), NOT NULL
- **evaluator_version**: VARCHAR(20), NOT NULL (semver)
- **severity**: ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'ADVISORY'), NOT NULL
- **explanation**: TEXT, NOT NULL
- **confidence**: FLOAT, NOT NULL, CHECK (confidence >= 0 AND confidence <= 1)
- **start_offset**: INTEGER, nullable
- **end_offset**: INTEGER, nullable
- **suggested_correction**: TEXT, nullable
- **raw_output**: JSONB
- **created_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **Index**: `(document_id, severity)`, `(firm_id, evaluator_type)`

##### `reviewer_actions`
- **id**: UUID, primary key
- **flag_id**: UUID, FK to flags(id), NOT NULL
- **document_id**: UUID, FK to documents(id), NOT NULL
- **firm_id**: UUID, FK to firms(id), NOT NULL
- **reviewed_by**: UUID, FK to users(id), NOT NULL
- **action_type**: ENUM('approve', 'override', 'reject', 'defer'), NOT NULL
- **comment**: TEXT, nullable
- **created_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **Index**: `(document_id, flag_id)`

##### `audit_log`
- **id**: ULID, primary key (time-ordered)
- **firm_id**: UUID, FK to firms(id), NOT NULL
- **user_id**: UUID, FK to users(id), nullable (system events have no user)
- **event_type**: VARCHAR(50), NOT NULL
- **entity_type**: VARCHAR(50), NOT NULL
- **entity_id**: UUID, NOT NULL
- **payload**: JSONB, NOT NULL
- **prior_hash**: VARCHAR(64), NOT NULL
- **this_hash**: VARCHAR(64), NOT NULL
- **created_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **DB Role**: `REVOKE UPDATE, DELETE ON audit_log FROM app_role`
- **Index**: `(firm_id, created_at)`, `(firm_id, entity_type, entity_id)`

##### `exports`
- **id**: UUID, primary key
- **document_id**: UUID, FK to documents(id), NOT NULL
- **firm_id**: UUID, FK to firms(id), NOT NULL
- **exported_by**: UUID, FK to users(id), NOT NULL
- **format**: VARCHAR(10), NOT NULL, DEFAULT 'pdf'
- **file_url**: TEXT, NOT NULL
- **file_hash**: VARCHAR(64), NOT NULL (SHA-256 of the exported file)
- **created_at**: TIMESTAMPTZ, NOT NULL, DEFAULT now()
- **Index**: `(document_id, firm_id)`

#### Enums
- **document_status**: `pending`, `in_review`, `resolved`
- **severity**: `CRITICAL`, `HIGH`, `MEDIUM`, `ADVISORY`
- **role**: `admin`, `reviewer`, `submitter`
- **action_type**: `approve`, `override`, `reject`, `defer`
- **evaluator_type**: `citation_existence`, `quote_verification`, `bluebook_format`, `judge_verification`, `temporal_validity`

#### Migration Strategy
- All migrations managed via Alembic with auto-generation from SQLAlchemy models.
- Each migration is reviewed for tenant isolation (every new table gets `firm_id`).
- Destructive migrations (column drops, type changes) require explicit ADR.

### Consequences

**Positive:**
- ACID guarantees on audit log: hash-chain integrity is protected by PostgreSQL's transaction isolation.
- Clean tenant isolation: `firm_id` on every table makes cross-tenant queries impossible without explicit intent.
- Flexible evaluator output: JSONB accommodates schema evolution across evaluator versions without migrations.
- Fast queue queries: composite indexes on `(firm_id, status, created_at)` support the reviewer workflow.
- Soft delete on users and API keys: preserves audit trail references while supporting revocation.

**Challenges:**
- Single-tenant performance ceiling: a single Postgres instance may need vertical scaling or read replicas at high volume. Acceptable for V1.
- Alembic migrations require careful review: auto-generated migrations can produce incorrect diffs for complex schema changes.
- Denormalized `firm_id` on `flags` and `reviewer_actions`: adds storage overhead but is necessary for query performance without joins.
- JSONB fields are harder to validate: application-layer validation via Pydantic must compensate for the lack of DB-level schema enforcement on JSONB columns.

---

**Related Documents:**
- `docs/PRD_v1.md` — V1 product requirements
- `adr/0001-tech-stack.md` — technology stack decisions (PostgreSQL 16)
- `adr/0003-audit-log-hash-chain.md` — audit log hash chain implementation
- `adr/0004-tenant-isolation.md` — tenant isolation strategy
- `RnR/citeguard_backend_guidelines.md` — backend coding standards
