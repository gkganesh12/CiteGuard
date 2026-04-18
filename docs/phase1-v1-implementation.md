# CiteGuard Phase 1: V1 Implementation Guide

| | |
|---|---|
| **Phase** | Phase 1 — V1 MVP (Public Launch) |
| **Duration** | 12 weeks (6 two-week sprints) |
| **Sprint cadence** | 2-week sprints |
| **Target** | ≥3 paying firms, $5K MRR, <3s p95 latency |
| **PRD reference** | `docs/PRD_v1.md` |
| **Last updated** | 2026-04-18 |

---

## 1. Phase Overview

Phase 1 delivers the CiteGuard MVP: an AI verification and audit platform that catches the five highest-frequency failure modes of legal AI output for **federal case law** and produces a tamper-evident audit trail.

### What ships in V1

| Feature | PRD Ref | Description |
|---------|---------|-------------|
| F1: Ingestion Layer | REQ-F1.* | SDK (Python/Node.js) + REST proxy for capturing AI-generated documents |
| F2: Citation Existence | REQ-F2.* | Verify citations against CourtListener |
| F3: Quote Verification | REQ-F3.* | Fuzzy-match quoted passages against source opinions |
| F4: Bluebook Formatting | REQ-F4.* | Rule engine for 21st edition Bluebook citation format |
| F5: Judge Verification | REQ-F5.* | Verify judge names against FJC biographical directory |
| F6: Temporal Validity | REQ-F6.* | Detect overruled/superseded precedent via citation graph |
| F7: Review Queue | REQ-F7.* | Priority-sorted queue with approve/override/reject/defer actions |
| F8: Audit Export | REQ-F8.* | Tamper-evident PDF with hash-chained audit trail |
| F9: Auth & Onboarding | REQ-F9.* | Clerk auth, firm workspaces, roles, API keys |
| F10: Alerts | REQ-F10.* | Slack webhook + batched email alerts |

### What does NOT ship in V1

- State case law (federal only)
- LLM-as-judge evaluators (Holding Accuracy)
- PII/privilege scanning, opposing authority, jurisdiction match, statutory currency
- SSO/SAML, dark mode, custom rules, analytics dashboard
- Mobile app, integrations marketplace

---

## 2. Tech Stack

| Layer | Choice | Key Libraries |
|-------|--------|---------------|
| Backend | Python 3.12 + FastAPI | Pydantic v2, SQLAlchemy 2.0, Alembic, structlog |
| Workers | Arq (Redis-backed) | arq, redis-py |
| Primary DB | Postgres 16 (AWS RDS or Fly.io Postgres) | asyncpg |
| Trace store | ClickHouse Cloud | clickhouse-connect |
| Frontend | Next.js 14, TypeScript, Tailwind CSS | shadcn/ui, TanStack Query, Clerk React |
| Auth | Clerk | @clerk/nextjs, clerk-sdk-python |
| Payments | Stripe | stripe-python |
| PDF generation | WeasyPrint | weasyprint |
| Citation parsing | eyecite | eyecite |
| Fuzzy matching | rapidfuzz | rapidfuzz |
| Backend hosting | Fly.io | flyctl |
| Frontend hosting | Vercel | vercel CLI |
| CDN/WAF | Cloudflare | — |
| Email | Resend or Postmark | resend / postmark |

**ADR:** `adr/0001-tech-stack.md`

---

## 3. Pre-Sprint 0: Foundation (Before Any Code)

### 3.1 ADRs to Create

All 9 foundation ADRs must be committed before Sprint 1 begins:

| ADR | File | Scope |
|-----|------|-------|
| ADR-0001 | `adr/0001-tech-stack.md` | Tech stack selection |
| ADR-0002 | `adr/0002-database-schema.md` | Core 8-table schema |
| ADR-0003 | `adr/0003-audit-log-hash-chain.md` | Append-only hash chain design |
| ADR-0004 | `adr/0004-tenant-isolation.md` | firm_id enforcement, 404-not-403 |
| ADR-0005 | `adr/0005-evaluator-architecture.md` | IEvaluator protocol, orchestrator |
| ADR-0006 | `adr/0006-authentication.md` | Clerk JWT, API keys, RBAC |
| ADR-0007 | `adr/0007-privileged-data-handling.md` | Privilege protection policy |
| ADR-0008 | `adr/0008-external-api-integration.md` | CourtListener/FJC integration |
| ADR-0009 | `adr/0009-ci-cd-pipeline.md` | CI/CD with GitHub Actions |

### 3.2 Architecture Diagrams

| File | Content |
|------|---------|
| `arc_diagrams/backend/system-overview.mmd` | Full system component diagram |
| `arc_diagrams/backend/data-model.mmd` | ER diagram for all 8 core tables |
| `arc_diagrams/backend/audit-log-chain.mmd` | Hash chain construction flow |
| `arc_diagrams/backend/evaluator-pipeline.mmd` | Document → evaluator fan-out → flags |
| `arc_diagrams/backend/auth-flow.mmd` | Clerk JWT + API key auth |
| `arc_diagrams/frontend/app-routes.mmd` | Next.js App Router route tree |
| `arc_diagrams/frontend/state-management.mmd` | State management decisions |

---

## 4. Sprint 1 (Weeks 1–2): Technical Foundation + Ingestion

### Sprint Goal

Project scaffolding, database schema, authentication, document submission endpoint, and CI/CD pipeline.

### Backend Components

#### 4.1.1 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                         # FastAPI app with lifespan
│   ├── config.py                       # pydantic-settings (DATABASE_URL, REDIS_URL, etc.)
│   ├── common/
│   │   ├── dependencies.py             # get_db, get_current_user, require_role
│   │   ├── exceptions.py               # CiteGuardException hierarchy
│   │   ├── middleware.py               # request_id, structured logging, CORS
│   │   └── pagination.py              # PaginatedResponse[T] generic
│   ├── db/
│   │   ├── base.py                     # DeclarativeBase
│   │   ├── session.py                  # async engine + session factory
│   │   └── migrations/                 # Alembic
│   │       ├── env.py
│   │       └── versions/
│   ├── models/                         # SQLAlchemy models
│   │   ├── firm.py
│   │   ├── user.py
│   │   ├── api_key.py
│   │   ├── document.py
│   │   ├── flag.py
│   │   ├── reviewer_action.py
│   │   ├── audit_log.py
│   │   └── export.py
│   ├── firms/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   ├── users/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   ├── api_keys/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   ├── documents/
│   │   ├── router.py
│   │   ├── service.py                  # DocumentIngestionService
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── proxy.py                    # LLM proxy endpoint
│   ├── audit/
│   │   ├── service.py                  # AuditLogService (SOLE write path)
│   │   ├── repository.py
│   │   └── schemas.py
│   ├── workers/
│   │   ├── arq_app.py                  # Arq worker definition
│   │   └── tasks/                      # Task placeholders
│   ├── evaluators/                     # (Sprint 2)
│   ├── flags/                          # (Sprint 2)
│   ├── alerts/                         # (Sprint 4)
│   └── integrations/
│       ├── courtlistener/              # (Sprint 2)
│       ├── fjc/                        # (Sprint 3)
│       └── stripe/                     # (Sprint 4)
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml                  # Postgres 16, Redis, ClickHouse
├── .env.example
└── .github/
    └── workflows/
        └── backend.yml
```

#### 4.1.2 Database Schema (Alembic Initial Migration)

**8 core tables** per PRD section 10.1:

- `firms` — id (UUID PK), name, created_at, billing_email, stripe_customer_id, settings (JSONB)
- `users` — id (UUID PK), firm_id (FK), email, role (ENUM: admin/reviewer/submitter), created_at, last_login, deleted_at
- `api_keys` — id (UUID PK), firm_id (FK), name, key_hash (bcrypt), created_by (FK), last_used_at, revoked_at
- `documents` — id (UUID PK), firm_id (FK), submitter_user_id (FK), text (large), document_type, llm_provider, llm_model, prompt (nullable), metadata (JSONB), status (ENUM: pending/in_review/resolved), submitted_at, resolved_at
- `flags` — id (UUID PK), document_id (FK), evaluator (ENUM), severity (ENUM), explanation, confidence (FLOAT), start_offset (INT), end_offset (INT), suggested_correction, raw_evaluator_output (JSONB), created_at
- `reviewer_actions` — id (UUID PK), flag_id (FK), user_id (FK), action (ENUM: approve/override/reject/defer), reason (text), created_at
- `audit_log` — id (ULID PK), firm_id (FK), document_id (FK, nullable), event_type (ENUM), actor_user_id (FK), payload (JSONB), prior_hash (CHAR 64), this_hash (CHAR 64), created_at
- `exports` — id (UUID PK), document_id (FK), user_id (FK), created_at, pdf_path, pdf_hash (SHA-256)

**Critical constraints:**
- `audit_log`: REVOKE UPDATE, DELETE at DB role level in migration
- Composite indexes: `(firm_id, status, created_at)` on documents, `(firm_id, created_at)` on audit_log
- All tables with firm_id have FK to firms(id)

#### 4.1.3 Auth Module

- **Clerk JWT verification** via JWKS endpoint — `get_current_user` dependency
- **require_role(Role)** dependency factory for endpoint-level authorization
- **API key auth** for SDK/proxy: bcrypt hash stored, key shown once at creation
- API key format: `cg_live_...` / `cg_test_...`

#### 4.1.4 Document Ingestion

- `POST /v1/documents` — accepts `DocumentCreate` schema, validates 200KB limit (413), idempotency via `Idempotency-Key` header
- `DocumentIngestionService` — single ingestion path for SDK and proxy
- Writes `audit_log` entry (`event_type='document_submitted'`) in same transaction
- Returns 201 with `document_id`, `status: pending`, `review_url`

#### 4.1.5 Audit Log Foundation

- `AuditLogService.append(event)` — the ONLY write path
- Hash chain: `this_hash = sha256(prior_hash || canonical_json(payload))`
- Genesis row created on firm creation: `prior_hash = sha256("")`

#### 4.1.6 Worker Skeleton

- Arq worker definition with Redis connection
- Task placeholder for `evaluator_run`

### Frontend Components

#### 4.2.1 Project Structure

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── sign-in/[[...sign-in]]/page.tsx
│   │   ├── sign-up/[[...sign-up]]/page.tsx
│   │   └── layout.tsx
│   ├── (authenticated)/
│   │   ├── layout.tsx                  # AppShell with sidebar
│   │   ├── dashboard/
│   │   │   ├── page.tsx                # Dashboard home
│   │   │   └── loading.tsx
│   │   ├── queue/                      # (Sprint 3)
│   │   ├── documents/[documentId]/     # (Sprint 3)
│   │   ├── audit/                      # (Sprint 4)
│   │   └── firm/
│   │       ├── users/                  # (Sprint 4)
│   │       ├── api-keys/              # (Sprint 4)
│   │       ├── settings/              # (Sprint 4)
│   │       └── billing/               # (Sprint 5)
│   ├── layout.tsx                      # Root layout
│   ├── page.tsx                        # Landing (Sprint 6)
│   └── middleware.ts                   # Clerk middleware
├── components/
│   ├── common/
│   │   ├── severity-badge.tsx          # CRITICAL/HIGH/MEDIUM/ADVISORY
│   │   ├── empty-state.tsx
│   │   └── page-header.tsx
│   └── ui/                            # shadcn/ui components
├── hooks/
├── lib/
│   ├── api/                            # API client (generated from OpenAPI)
│   └── env.ts                          # zod-validated env vars
├── tailwind.config.ts                  # Severity color palette
├── tsconfig.json                       # strict mode
└── package.json
```

#### 4.2.2 Severity Color System

```
CRITICAL = red-600 / red-500 (dark)
HIGH     = orange-600 / orange-500 (dark)
MEDIUM   = amber-600 / amber-500 (dark)
ADVISORY = blue-600 / blue-500 (dark)
```

Never green. Severity conveyed by color + icon + text, never color alone.

### Infrastructure

- Fly.io app creation + Dockerfile deploy
- Vercel project connected to GitHub
- Managed Postgres 16 (Fly.io Postgres or AWS RDS)
- Redis (Upstash or Fly.io Redis)
- ClickHouse Cloud instance
- Clerk application with Google OAuth
- Sentry projects (backend + frontend)
- GitHub Actions CI: mypy, ruff, pytest, tsc, eslint, vitest

### Sprint 1 Acceptance Criteria

- [ ] Backend deployed to Fly.io, `/healthz` returns 200
- [ ] Frontend deployed to Vercel, sign-in/sign-up functional via Clerk
- [ ] `POST /v1/documents` accepts a document, stores in Postgres, returns document_id
- [ ] Audit log entry written for document submission (hash chain verified)
- [ ] CI pipeline green (type checking, linting, tests)
- [ ] Docker Compose runs locally (Postgres + Redis + ClickHouse)

---

## 5. Sprint 2 (Weeks 3–4): First Two Evaluators + LLM Proxy

### Sprint Goal

Citation Existence (F2) and Quote Verification (F3) evaluators running end-to-end. LLM proxy functional.

### Backend Components

#### 5.1.1 Evaluator Infrastructure

```python
# app/evaluators/base.py
class IEvaluator(Protocol):
    name: str
    version: str

    async def evaluate(
        self, document: Document, context: EvaluationContext
    ) -> list[FlagResult]: ...

# app/evaluators/orchestrator.py
class EvaluatorOrchestrator:
    async def run_all(self, document: Document) -> list[FlagResult]:
        # asyncio.gather with per-evaluator timeout (10s)
        # Exceptions converted to ADVISORY flags
```

#### 5.1.2 Citation Existence Evaluator (`app/evaluators/citation_existence.py`)

- **Version:** 1.0.0
- **Parser:** eyecite library for citation extraction
- **Formats:** Supreme Court (`410 U.S. 113`), Federal Reporter (`304 F.3d 451`), Federal Supplement, Federal Rules Decisions, generic reporter
- **Resolution:** CourtListener `/api/rest/v3/opinions/` by volume/reporter/page
- **Severity:** CRITICAL (no match), HIGH (match but case name mismatch), ADVISORY (confirmed)
- **Output:** cited text, parsed citation, resolved opinion (or null), severity, explanation, confidence (0–1)
- **Cache:** Redis — key: `cl:{volume}:{reporter}:{page}`, hit TTL: 24h, miss TTL: 1h

#### 5.1.3 Quote Verification Evaluator (`app/evaluators/quote_verification.py`)

- **Version:** 1.0.0
- **Extraction:** Regex for quoted passages followed by citation within 200 chars
- **Verification:** Fetch full opinion text from CourtListener, normalize whitespace/punctuation
- **Matching:** rapidfuzz `partial_ratio`, threshold 85%
- **Severity:** CRITICAL (no match — fabricated quote), HIGH (significant alterations), ADVISORY (match within threshold)
- **Output:** quoted text, cited opinion, match result, closest matching passage, similarity score

#### 5.1.4 CourtListener Integration (`app/integrations/courtlistener/`)

```
app/integrations/courtlistener/
├── client.py       # async httpx, retry (3x, exponential backoff), circuit breaker
├── cache.py        # Redis cache wrapper
└── schemas.py      # Response models
```

- Retry: 3 attempts, exponential backoff (1s, 2s, 4s), max 10s
- Circuit breaker: 5 failures in 60s opens circuit for 30s
- Rate limit monitoring via response headers

#### 5.1.5 LLM Proxy

- `POST /v1/llm/proxy` — accepts OpenAI-compatible and Anthropic-compatible payloads
- Forwards to upstream LLM provider via httpx async
- Captures request + response, routes through `DocumentIngestionService`
- Optional header: `X-CiteGuard-Document-Type: brief`

#### 5.1.6 Worker Task

- `evaluator_run` Arq task: invokes `EvaluatorOrchestrator`, writes flags to DB, writes audit entries, updates document status to `in_review`

### Frontend Components

- **"Paste & Test" form** on dashboard: text area + document type selector + submit button
- **Document status polling:** `useDocument(id)` and `useFlags(id)` TanStack Query hooks
- **Basic queue table:** document list with severity badge, flag count, submitter, timestamp, status

### Test Corpus (Begin)

Start building the 100-document evaluator corpus:
- 25 documents with seeded fake citations (Citation Existence)
- 25 documents with fabricated quotes (Quote Verification)
- 50 clean documents with valid federal citations and quotes

### Sprint 2 Acceptance Criteria

- [ ] Submit document → Citation Existence evaluator runs → flags created in DB
- [ ] Submit document → Quote Verification evaluator runs → flags created in DB
- [ ] Both evaluators run in parallel via `asyncio.gather`
- [ ] CourtListener integration with retry, backoff, and caching functional
- [ ] LLM proxy forwards to Claude/OpenAI and captures output
- [ ] "Paste & Test" form on dashboard submits documents
- [ ] Basic queue table shows documents with severity badges
- [ ] Citation Existence: ≥95% true-positive on seeded fake citations subset
- [ ] Quote Verification: ≥95% true-positive on fabricated quotes subset
- [ ] ADR: `adr/0010-courtlistener-caching.md` committed

---

## 6. Sprint 3 (Weeks 5–6): Remaining Evaluators + Review Queue

### Sprint Goal

Bluebook Formatting (F4), Judge Verification (F5), Temporal Validity (F6) live. Review Queue (F7) functional with full reviewer workflow.

### Backend Components

#### 6.1.1 Bluebook Formatting Evaluator (`app/evaluators/bluebook_format.py`)

- **Version:** 1.0.0
- **Rules:** Bluebook 21st edition — required elements (volume, reporter, page, year), signal words (See, Cf., But see), pincites (B10.1.4), parentheticals (court + year), common abbreviations
- **Severity:** HIGH (missing required element), MEDIUM (format error), ADVISORY (style preference)
- **Output:** exact citation span, rule violated, suggested correction

#### 6.1.2 Judge Verification Evaluator (`app/evaluators/judge_verification.py`)

- **Version:** 1.0.0
- **Extraction:** Regex patterns + NER fallback for judge names ("Judge John Smith", "the Honorable J. Smith", "Smith, J.")
- **Data source:** FJC Biographical Directory of Federal Judges (~4,000 judges)
- **Verification:** Judge existed + served on cited court during cited time period
- **Severity:** CRITICAL (no such judge), HIGH (wrong court/period), ADVISORY (confirmed)
- **Ambiguity:** Common names with multiple matches → ADVISORY with note

#### 6.1.3 Temporal Validity Evaluator (`app/evaluators/temporal_validity.py`)

- **Version:** 1.0.0
- **Data source:** CourtListener citation graph — negative treatment queries
- **Severity:** CRITICAL (expressly overruled), HIGH (abrogated), MEDIUM (>3 negative-treatment cites), ADVISORY (no negative treatment)
- **Output:** treatment type, overruling case (if any), CourtListener link

#### 6.1.4 FJC Integration (`app/integrations/fjc/`)

- Local Postgres table: `fjc_judges` with name, court, start_date, end_date, status
- Data loader from FJC public dataset (CSV import)
- Quarterly refresh via Arq scheduled task

#### 6.1.5 Reviewer Actions API

- `POST /v1/flags/{id}/actions` — action (approve/override/reject/defer), reason (required on override, min 10 chars)
- Writes to `reviewer_actions` + `audit_log` in same transaction
- `PUT /v1/documents/{id}/finalize` — blocks while unresolved flags exist; triggers audit export
- `PUT /v1/documents/{id}/reopen` — returns Resolved → In Review

#### 6.1.6 Queue API

- `GET /v1/documents` — list with filters (severity, status, submitter, date range, document_type)
- Default sort: severity DESC, submitted_at ASC
- Cursor-based pagination
- `GET /v1/documents/{id}` — document detail with all flags and reviewer actions

### Frontend Components

#### 6.2.1 Review Queue (`app/(authenticated)/queue/`)

- `page.tsx` — Server Component fetching initial data
- `_components/QueueTable.tsx` — Client Component with TanStack Query
- URL-synced filters via `useSearchParams` (severity, status, submitter, date range)
- Default sort: severity DESC, submitted_at ASC
- Severity badges (color + icon + text), flag count, submitter, timestamp, status
- Prefetch next document on hover
- `loading.tsx` — skeleton loader

#### 6.2.2 Document Detail (`app/(authenticated)/documents/[documentId]/`)

- `page.tsx` — rendered document text with inline flag highlights (severity-colored underlines)
- `_components/FlagSidePanel.tsx` — evaluator explanation, severity, confidence, suggested correction, action buttons
- `_components/ReviewActionButtons.tsx` — Approve / Override / Reject / Defer
- Override dialog with reason text area (min 10 chars, validated client + server)
- Finalize button disabled while unresolved flags exist (with tooltip)
- Document status badge (Pending / In Review / Resolved)

#### 6.2.3 Keyboard Shortcuts (`hooks/useReviewShortcuts.ts`)

| Key | Action |
|-----|--------|
| A | Approve current flag |
| O | Override current flag (opens reason dialog) |
| R | Reject current flag |
| D | Defer current flag |
| J | Next flag |
| K | Previous flag |
| N | Next document in queue |
| ? | Show shortcuts overlay |

Disabled when text input focused.

#### 6.2.4 Optimistic UI

- `useApproveFlag`, `useOverrideFlag`, `useRejectFlag`, `useDeferFlag` mutation hooks
- Optimistic update in TanStack Query cache with rollback on error
- Toast notifications on success/error

### Test Corpus (Complete)

Complete 100-document corpus:
- 10 fake citations, 10 fabricated quotes, 10 wrong judges, 10 overruled cases, 10 format errors (= 50 seeded hallucinations)
- 50 clean documents with valid federal citations, quotes, judges, formatting

### Sprint 3 Acceptance Criteria

- [ ] All 5 evaluators run in parallel on every document submission
- [ ] Review Queue shows flagged documents sorted by severity
- [ ] Filters functional: severity, status, submitter, date range, document type
- [ ] Document detail view shows inline flag highlights
- [ ] Reviewer can approve/override/reject/defer each flag
- [ ] Override requires reason (min 10 chars, enforced server-side)
- [ ] Finalize blocked while flags unresolved (enforced server-side)
- [ ] Keyboard shortcuts functional (A/O/R/D/J/K/N/?)
- [ ] Evaluator accuracy on full 100-doc corpus: ≥95% TP, <5% FP
- [ ] All reviewer actions write audit log entries

---

## 7. Sprint 4 (Weeks 7–8): Audit Export + Alerts + Team Management

### Sprint Goal

Audit PDF export with hash chain, Slack/email alerts, complete team management, Stripe billing.

### Backend Components

#### 7.1.1 Audit Export (`app/audit/exporter.py`)

- `POST /v1/documents/{id}/export` — triggers Arq job, returns 202 with export_id
- WeasyPrint HTML-to-PDF in Arq worker
- **PDF contents** (per REQ-F8.2):
  - Document ID, firm name, submitter, reviewers, timestamps
  - Original submitted text (full)
  - Each flag: severity, evaluator, explanation, reviewer action, reason (if override)
  - Summary table: total flags by severity, resolution counts
  - Hash chain: SHA-256 hash of document's audit records + preceding hash
  - CiteGuard version, evaluator versions
- S3 storage for PDFs, signed URL with 1h expiry
- Deterministic rendering (same state → identical PDF)
- Export logged in audit_log

#### 7.1.2 Hash Chain Verification

- Daily Arq scheduled job: re-compute chain from genesis for every firm
- Alert on divergence → P0 incident
- `GET /v1/audit-log` — paginated (cursor-based) audit log viewer for firm admins

#### 7.1.3 Alerts (`app/alerts/`)

- `SlackNotifier` — webhook POST on CRITICAL flags, within 60 seconds
- `EmailNotifier` — batched every 10 minutes, configurable severity threshold (default: CRITICAL + HIGH)
- Per-firm Slack webhook configuration (firm settings)
- Per-user email alert preferences
- Role-aware: submitters see own docs, reviewers see assigned/queue docs

#### 7.1.4 Team Management

- `POST /v1/firms/{id}/invites` — invite by email (admin-only)
- `PATCH /v1/users/{id}/role` — change role (admin-only, not self-change)
- `DELETE /v1/users/{id}` — soft delete (admin-only, last-admin safeguard)
- `POST /v1/api-keys` — generate, return plaintext once
- `DELETE /v1/api-keys/{id}` — revoke
- `GET /v1/api-keys` — list (without plaintext)
- All admin actions write audit entries

#### 7.1.5 Stripe Integration (`app/integrations/stripe/`)

- Customer creation on firm sign-up
- Usage metering: per-document usage records on submission
- Basic billing portal link

### Frontend Components

- **Audit export UI:** export button (Finalized docs only), async progress, download history, hash display
- **Team management:** user list + roles, invite modal (email + role), role change dropdown, remove with confirmation, last-admin safeguard
- **API key management:** generate modal (name input), one-time display + copy, key list, revoke
- **Firm settings:** name, billing contact, Slack webhook, default reviewer, retention config
- **Alert preferences:** severity threshold selector, email toggle
- **Dashboard:** summary stats (docs verified, flags by severity), recent activity, quick actions

### Sprint 4 Acceptance Criteria

- [ ] Finalized document → one-click PDF export with hash chain
- [ ] PDF contains all required fields per REQ-F8.2
- [ ] Hash chain verifiable (recompute from chain matches)
- [ ] Re-export produces identical PDF for same document state
- [ ] Slack alert fires within 60 seconds of CRITICAL flag
- [ ] Email alerts batched and sent every 10 minutes
- [ ] Admin can invite users, change roles, manage API keys
- [ ] Last-admin safeguard prevents removing the only admin
- [ ] API keys shown only at creation, never again
- [ ] Stripe usage metering records per-document charges
- [ ] Daily hash chain verification job running

---

## 8. Sprint 5 (Weeks 9–10): Testing + Hardening + Onboarding

### Sprint Goal

Load testing, security review, E2E test suite, SDK packaging, design partner onboarding.

### Backend Components

#### 8.1.1 Load Testing (k6)

- Scenario: sustained 10 docs/sec submission rate
- Verify: p50 <1500ms, p95 <3000ms, p99 <7000ms
- PDF export under concurrent load
- Queue page load <500ms p95

#### 8.1.2 Security Hardening

- Sentry `beforeSend` scrubbing verified (no document content in any exception/breadcrumb)
- Pre-commit hook: grep for document content logging patterns
- Rate limiting tuned: 100 req/min/firm (submissions), 10 req/min (auth)
- CORS allow-list finalized
- Security headers: HSTS, X-Frame-Options, X-Content-Type-Options, CSP
- Secrets validated at startup via pydantic-settings

#### 8.1.3 Health Endpoints

- `/healthz` — liveness probe (always 200)
- `/readyz` — readiness probe (checks DB + Redis connectivity)

#### 8.1.4 Observability

- structlog with JSON output: request_id, firm_id, user_id, route, duration_ms
- ClickHouse trace integration (metadata only — never document content)
- Sentry error tracking with privilege scrubbing
- Uptime monitoring (BetterStack or UptimeRobot)

#### 8.1.5 SDK Packaging

- **Python SDK** (`citeguard` on PyPI):
  ```python
  import citeguard
  client = citeguard.Client(api_key="cg_live_...")
  result = client.verify(text="...", document_type="brief")
  ```
- **Node.js SDK** (`@citeguard/sdk` on npm):
  ```typescript
  import { CiteGuard } from '@citeguard/sdk';
  const client = new CiteGuard({ apiKey: 'cg_live_...' });
  const result = await client.verify({ text: '...', documentType: 'brief' });
  ```

### Frontend Components

#### 8.2.1 Onboarding Wizard (`app/(auth)/onboarding/`)

Steps:
1. Create firm workspace (name, billing email)
2. Generate first API key (copy it)
3. "Paste & Test" first document
4. SDK installation instructions (Python/Node.js)
5. Invite team members
6. Connect Slack for alerts
7. Done — firm is live

**Target:** Sign-up to first verified document in <15 minutes.

#### 8.2.2 Error States Polish

- `error.tsx` at route level — generic error boundary
- `not-found.tsx` — custom 404
- Toast system (non-blocking feedback)
- 429 handling with retry timer display

#### 8.2.3 E2E Playwright Tests

- Sign in → submit document → see flags → review → finalize → download audit PDF
- Invite user → role assignment → permissions enforced
- API key lifecycle: create → use → revoke
- Keyboard-only review flow (A/O/R/D/J/K/N)

### Infrastructure

- Production environment finalized on Fly.io
- Database backups verified via restore test
- Runbooks for top 5 operational incidents:
  1. CourtListener outage
  2. Audit hash chain break
  3. Privilege data leak
  4. Tenant isolation breach
  5. Production database failure

### Sprint 5 Acceptance Criteria

- [ ] p95 evaluation latency <3000ms under 10 docs/sec sustained load
- [ ] Queue page load <500ms p95
- [ ] PDF export <5000ms
- [ ] Security review complete (Sentry scrubbing, pre-commit hooks, headers)
- [ ] E2E test suite passing in CI (Playwright)
- [ ] Python SDK published to PyPI
- [ ] Node.js SDK published to npm
- [ ] Onboarding wizard functional (sign-up to first doc in <15 min)
- [ ] Runbooks documented for top 5 incidents
- [ ] Database backup restore tested

---

## 9. Sprint 6 (Weeks 11–12): Polish + Launch

### Sprint Goal

3+ paying firms converted, landing page live, documentation published, public launch.

### Backend

- Stripe billing finalized: subscription management, invoice generation, payment failure handling
- Data retention: 90-day default, configurable extension (1/3/7 years), hard-delete request (30-day SLA)
- OpenAPI schema finalized: all endpoints documented with tags, response_models, examples

### Frontend

- **WCAG 2.1 AA audit:** color contrast, focus indicators, ARIA labels, screen reader testing
- **Keyboard navigation:** every action accessible via keyboard
- **Professional tone review:** no emoji, no gamification, no green severity, no "Great job!"
- **Density optimization:** 20+ queue items visible per screen
- **Mobile:** read-only below 1024px with notice (not optimized, but doesn't break)
- **Documentation site:** API reference, SDK quick starts, onboarding guide, FAQ

### Sprint 6 Acceptance Criteria (= V1 Release Criteria)

#### Functional (PRD §16.1)
- [ ] All 10 F-requirements implemented with passing E2E tests
- [ ] 5 evaluators produce correct results on 100-document test corpus
- [ ] Review queue supports full approve/override/reject/defer/finalize flow
- [ ] Audit PDF generated, hash chain verifiable
- [ ] Slack alerting working end-to-end

#### Non-Functional (PRD §16.2)
- [ ] All NFR performance targets hit in load test
- [ ] TLS everywhere, keys hashed, encryption at rest
- [ ] DPA and Privacy Policy drafted
- [ ] E&O policy bound and in force

#### Business (PRD §16.3)
- [ ] ≥3 firms on paid contracts ($1,500/mo minimum each)
- [ ] Onboarding doc + API reference published
- [ ] Landing page live
- [ ] Stripe billing with per-doc metering working
- [ ] Support channel active

#### Operational (PRD §16.4)
- [ ] Uptime monitoring + alerting configured
- [ ] Error tracking configured (Sentry)
- [ ] Daily DB backups verified
- [ ] Runbook for top 5 incidents
- [ ] On-call rotation defined

---

## 10. Key Risks (Phase 1)

| Risk | Severity | Mitigation |
|------|----------|------------|
| CourtListener rate limits insufficient | Medium | Cache aggressively (24h TTL), donate for higher quota, plan local mirror for V2 |
| Evaluator false-positive rate annoys design partners | Medium | Weekly threshold tuning, reject_rate as core health metric |
| Cannot sign 3 paying firms in 12 weeks | High | Start sales in week 1, have 5 design partners by week 4 |
| Solo founder capacity | High | Prioritize ruthlessly, automate CI/CD, consider first hire by week 6 |
| PDF export formatting challenges | Low | Use WeasyPrint (pure Python, deterministic), test with real firm data early |

---

## 11. Dependencies Between Sprints

```
Sprint 1 (Foundation) ──→ Sprint 2 (Evaluators 1-2)
                      └──→ Sprint 3 (Evaluators 3-5, Review Queue)
                                         └──→ Sprint 4 (Audit, Alerts, Team)
                                                          └──→ Sprint 5 (Hardening)
                                                                        └──→ Sprint 6 (Launch)
```

Sprint 1 is the foundation — everything depends on it. Sprints 2 and 3 can be partially parallelized if team size allows. Sprint 4+ are sequential.

---

*End of Phase 1 Implementation Guide. This document is the source of truth for V1 implementation scope and sprint structure. Changes require review against `docs/PRD_v1.md`.*
