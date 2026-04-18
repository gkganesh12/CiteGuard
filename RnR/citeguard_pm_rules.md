# Technical Architect - Code Review Rules

## Role Overview
As a Senior Technical Architect, you are responsible for ensuring code quality, architectural integrity, system scalability, and adherence to best practices across the CiteGuard platform — an AI verification and audit layer for U.S. law firms that processes privileged legal documents and produces tamper-evident compliance records.

**Stack context:**
- **Frontend:** Next.js 14 (App Router) · TypeScript 5+ · Tailwind CSS · shadcn/ui · react-hook-form + zod · TanStack Query
- **Backend:** Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · Arq (Redis-backed workers)
- **Data:** PostgreSQL 16 · ClickHouse (traces/telemetry) · Redis
- **Auth & Payments:** Clerk · Stripe
- **External:** CourtListener API · Federal Judicial Center directory · WeasyPrint (PDF export)

> **⚠️ Domain criticality:** Bugs here are not UX annoyances — they are potential malpractice exposure for customers and compliance events for us. Privileged data, audit integrity, and tenant isolation are non-negotiable architectural concerns.

---

## 1. ARCHITECTURE PRINCIPLES

### 1.1 Separation of Concerns
- **RULE**: Each component/module must have a single, well-defined responsibility
- **CHECK**: No business logic in UI components; move to services/hooks/server actions
- **CHECK**: No data access logic in FastAPI routers; move to repositories
- **CHECK**: No UI rendering logic in API routes
- **CHECK**: Evaluators do verification only — they do not read/write other entities

### 1.2 Layered Architecture
- **RULE**: Enforce clear separation between layers: Presentation → Business Logic → Data Access
- **CHECK**: Frontend never calls the database directly (always via backend API)
- **CHECK**: Backend has clear Router → Service → Repository layers
- **CHECK**: Shared utilities must be framework-agnostic
- **CHECK**: Evaluators live in their own layer, invoked via an orchestrator — never by routes directly

### 1.3 DRY (Don't Repeat Yourself)
- **RULE**: No code duplication beyond 3 lines
- **CHECK**: Repeated logic must be extracted to utilities/helpers
- **CHECK**: Similar components must be abstracted with proper props
- **CHECK**: Database queries must be centralized in repositories
- **CHECK**: Citation parsing / severity classification logic lives in exactly one place

### 1.4 Scalability First
- **RULE**: Design for growth from day one
- **CHECK**: Pagination implemented for all list views (default 20, max 100)
- **CHECK**: Cursor-based pagination for `audit_log` and `flags` (append-only, high cardinality)
- **CHECK**: Efficient database queries with proper indexing
- **CHECK**: Caching strategy for frequently accessed external data (CourtListener opinions, FJC judge directory)
- **CHECK**: Evaluators run in parallel via `asyncio.gather` within a bounded concurrency limit

### 1.5 Tenant Isolation (CiteGuard-Critical)
- **RULE**: Multi-tenancy is a first-class architectural concern
- **CHECK**: Every tenant-scoped table has `firm_id` with an index
- **CHECK**: Every query filters by `firm_id` derived from the authenticated session
- **CHECK**: `firm_id` never accepted from request bodies; always server-derived
- **CHECK**: Cross-firm queries forbidden in application code
- **REJECT**: Any repository method without a `firm_id` parameter on tenant-scoped models

---

## 2. CODE QUALITY STANDARDS

### 2.1 Naming Conventions
- **RULE**: Names must be descriptive and follow project conventions
- **CHECK**: Frontend Components: PascalCase (e.g., `ReviewQueue`, `DocumentDetailView`, `FirmDashboard`)
- **CHECK**: Python classes: PascalCase (`DocumentService`, `EvaluatorOrchestrator`, `AuditLogRepository`)
- **CHECK**: TS/JS functions/variables: camelCase (`getDocumentById`, `flagData`)
- **CHECK**: Python functions/variables: snake_case (`get_document_by_id`, `flag_data`)
- **CHECK**: Constants: UPPER_SNAKE_CASE (`MAX_DOCUMENT_SIZE_BYTES`, `DEFAULT_PAGE_SIZE`)
- **CHECK**: Files: kebab-case for TS utilities, PascalCase for components, snake_case for Python modules
- **CHECK**: Boolean variables: use `is`, `has`, `should`, `can` prefix (`isResolved`, `hasPendingFlags`, `canFinalize`)
- **CHECK**: Event handlers: use `handle` or `on` prefix (`handleApprove`, `onFlagOverride`)

### 2.2 Function Design
- **RULE**: Functions must be small, focused, and testable
- **CHECK**: Max 50 lines per function (excluding comments)
- **CHECK**: Max 4 parameters per function (use objects / Pydantic models / dataclasses for more)
- **CHECK**: Single return type (avoid union returns when possible)
- **CHECK**: Pure functions where possible (no side effects)
- **CHECK**: Async functions must handle errors properly (no un-awaited promises/coroutines)

### 2.3 Code Complexity
- **RULE**: Keep cyclomatic complexity low
- **CHECK**: Max 3 levels of nesting
- **CHECK**: Max 5 conditional branches per function
- **CHECK**: Extract complex conditionals to named functions
- **CHECK**: Use early returns to reduce nesting
- **CHECK**: Replace type-discriminator `if/elif` chains with polymorphism (critical for evaluators)

### 2.4 Comments & Documentation
- **RULE**: Code should be self-documenting; comments explain "why", not "what"
- **CHECK**: All public APIs must have JSDoc/TSDoc / Python docstrings
- **CHECK**: Complex algorithms must have explanation comments (hash chain construction, citation parsing edge cases)
- **CHECK**: TODOs must have assignee and ticket reference (`# TODO(CG-123): ...`)
- **CHECK**: No commented-out code in main branch
- **REJECT**: Comments that state the obvious (e.g., `// increment counter`)

---

## 3. FRONTEND-SPECIFIC RULES (Next.js 14 + React)

### 3.1 Component Design
- **RULE**: Prefer React Server Components by default; use Client Components only when needed
- **CHECK**: Server Components for static content, data fetching; Client Components (`"use client"`) only for interactivity, state, browser APIs
- **CHECK**: Components under 300 lines (split if larger)
- **CHECK**: Max 10 props per component (use composition or context for more)
- **CHECK**: Props typed with TypeScript (strict mode)
- **CHECK**: Tailwind utility classes; no inline styles; shadcn/ui primitives for all interactive elements
- **CHECK**: Extract sub-components when JSX exceeds 150 lines

### 3.2 State Management
- **RULE**: Use appropriate state management for scope
- **CHECK**: Local state: `useState` for component-specific data
- **CHECK**: URL state: search params via `useSearchParams` for filters/sort/pagination on the review queue
- **CHECK**: Server state: TanStack Query for client-side API data; RSC data fetching for server-rendered views
- **CHECK**: Global state: Zustand only when justified (minimal at V1 — auth state via Clerk, nothing else)
- **CHECK**: Form state: react-hook-form + zod schema validation
- **CHECK**: No prop drilling beyond 2 levels (use Context or composition)

### 3.3 Performance Optimization
- **RULE**: Optimize for render performance — lawyers move fast through the queue
- **CHECK**: Server Components for initial render wherever possible (reduces JS bundle)
- **CHECK**: `React.memo` for expensive list-item components (flag rows, document rows)
- **CHECK**: `useMemo` / `useCallback` for expensive calculations/functions
- **CHECK**: Dynamic imports (`next/dynamic`) for heavy widgets (PDF preview)
- **CHECK**: Virtualization (TanStack Virtual) for any list >100 items (audit log browser)
- **CHECK**: Debounce search inputs (300ms); throttle scroll events
- **CHECK**: Image optimization via `next/image`; fonts via `next/font`

### 3.4 Forms & Validation
- **RULE**: Controlled forms with schema-driven validation
- **CHECK**: react-hook-form + zod for all non-trivial forms (flag override reasons, firm settings, user invites)
- **CHECK**: Same zod schema used for client and server validation (share a `schemas/` package)
- **CHECK**: Display field-level validation errors inline, aria-described
- **CHECK**: Disable submit during API calls; show spinner
- **CHECK**: Handle loading, success, and error states explicitly
- **CHECK**: OVERRIDE reason field enforces min 10 chars on both client and server

### 3.5 API Integration
- **RULE**: Centralize API calls
- **CHECK**: All client-side API calls in dedicated service modules (e.g., `lib/api/documents.ts`, `lib/api/flags.ts`)
- **CHECK**: A generated TypeScript client from the backend's OpenAPI schema is the source of truth
- **CHECK**: Axios/fetch wrapper with Clerk token auto-attached via interceptor
- **CHECK**: Consistent handling of loading, success, error states via TanStack Query hooks
- **CHECK**: Retry with exponential backoff on 429/5xx (not on 4xx client errors)
- **CHECK**: Cancel pending requests on component unmount (TanStack Query handles this by default)

### 3.6 UI/UX Patterns (CiteGuard-Specific)
- **RULE**: Professional, dense, keyboard-first
- **CHECK**: Severity color language: Critical = red, High = orange, Medium = amber, Advisory = blue. Never green.
- **CHECK**: Density over whitespace — queue shows 20+ items per viewport
- **CHECK**: Keyboard shortcuts for every reviewer action (A = Approve, O = Override, R = Reject, D = Defer)
- **CHECK**: No gamification, no emoji in UI, no "Great job!" micro-copy
- **CHECK**: WCAG 2.1 AA minimum (lawyers skew older; contrast and font size matter)
- **CHECK**: Focus management on queue navigation (next flag auto-focuses)

---

## 4. BACKEND-SPECIFIC RULES

### 4.1 API Design
- **RULE**: RESTful design with consistent patterns
- **CHECK**: Proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **CHECK**: Consistent URL structure (`/v1/documents/:id`, `/v1/flags/:id/actions`)
- **CHECK**: Proper status codes (200, 201, 202, 204, 400, 401, 403, 404, 409, 413, 422, 429, 500)
- **CHECK**: Consistent response envelope for lists (`{ items, total, page, page_size, has_next }`)
- **CHECK**: Consistent error envelope (`{ error: { code, message, details }, request_id, timestamp }`)
- **CHECK**: Versioned APIs (`/v1/...`); breaking changes require a major version bump

### 4.2 Authentication & Authorization
- **RULE**: Security must be implemented at every layer
- **CHECK**: Clerk as the identity provider; verify JWTs via JWKS on every request
- **CHECK**: API keys hashed with bcrypt (cost factor ≥12); plaintext keys shown once at creation
- **CHECK**: Role-based access control (RBAC): `ADMIN`, `REVIEWER`, `SUBMITTER`
- **CHECK**: Protected routes via FastAPI `Depends(get_current_user)` and `Depends(require_role(...))`
- **CHECK**: Input validation on all endpoints via Pydantic
- **CHECK**: Rate limiting on authentication and submission endpoints

### 4.3 Database Design
- **RULE**: Normalized schema with proper relationships
- **CHECK**: Alembic migrations for all schema changes (both up and down paths)
- **CHECK**: Foreign key constraints for referential integrity
- **CHECK**: Indexes on `firm_id`, foreign keys, and frequently queried columns
- **CHECK**: Soft deletes for critical data (`deleted_at TIMESTAMPTZ`)
- **CHECK**: `created_at` / `updated_at` on all tables; `TIMESTAMPTZ` type
- **CHECK**: Proper data types (`NUMERIC` for money, `JSONB` for semi-structured, `TEXT` over arbitrary `VARCHAR(255)`)
- **CHECK**: `audit_log` table explicitly denies UPDATE/DELETE at the DB role level

### 4.4 Data Validation
- **RULE**: Never trust client input
- **CHECK**: Pydantic v2 models for all request schemas with `extra="forbid"`
- **CHECK**: Sanitize any text that flows into PDFs to prevent content-injection
- **CHECK**: Validate declared LLM metadata (provider, model) against allowlist
- **CHECK**: Whitelist allowed fields on updates (never mass-assign arbitrary payload)
- **CHECK**: Type-coerce query parameters via FastAPI's type hints, bounded with `Query(ge=..., le=...)`

### 4.5 Error Handling
- **RULE**: Comprehensive error handling with proper logging
- **CHECK**: Custom exception classes (`DocumentNotFound`, `EvaluatorFailed`, `AuditChainBroken`, etc.)
- **CHECK**: Global exception handlers produce uniform error JSON
- **CHECK**: Never expose stack traces to client in production
- **CHECK**: Log errors with context (`request_id`, `firm_id`, `user_id`, route, duration) — NEVER log document content
- **CHECK**: Sentry for error monitoring; `before_send` scrubs privileged content

---

## 5. SECURITY REQUIREMENTS

### 5.1 Input Validation & Sanitization
- **RULE**: All inputs are guilty until proven innocent
- **CHECK**: Validate all API inputs (body, query, params) via Pydantic
- **CHECK**: Sanitize any text rendered into PDFs (no injection vectors in audit exports)
- **CHECK**: Parameterized queries (SQLAlchemy ORM / Core) — never string-interpolated SQL
- **CHECK**: Implement CSRF protection for any cookie-based state-changing operations (not needed for pure bearer-token APIs)

### 5.2 Authentication Security
- **RULE**: Implement defense in depth
- **CHECK**: HTTPS only (HSTS header, no HTTP in production)
- **CHECK**: Clerk-managed sessions with proper token rotation
- **CHECK**: Password policies enforced by Clerk (min 12 chars, complexity requirements)
- **CHECK**: Account lockout via Clerk after repeated failed attempts
- **CHECK**: API key revocation is immediate (no caching of compromised keys)

### 5.3 Data Protection
- **RULE**: Protect privileged legal data at rest and in transit
- **CHECK**: TLS 1.2+ in transit; AES-256 at rest via managed Postgres encryption
- **CHECK**: No secrets in code (environment variables only, validated at startup via pydantic-settings)
- **CHECK**: **Never** log or trace document content, prompts, or completions
- **CHECK**: Sentry / ClickHouse scrubs privileged fields via explicit allowlist
- **CHECK**: US-only data residency (us-east-1 primary, us-west-2 standby)
- **CHECK**: Data retention defaults to 90 days (configurable to 7 years per firm); hard-delete honored within 30 days
- **CHECK**: No customer document content is ever sent to any party except the customer's declared upstream LLM provider

### 5.4 API Security
- **RULE**: Secure all endpoints
- **CHECK**: Authentication required for all protected routes; explicit `@public` markers on anonymous routes
- **CHECK**: Authorization checks for resource access (ownership + role + firm scope)
- **CHECK**: Rate limiting (tighter on auth and submission endpoints)
- **CHECK**: CORS with explicit allowlist (no wildcards in production)
- **CHECK**: Security headers (CSP, X-Content-Type-Options, Referrer-Policy, X-Frame-Options)

---

## 6. TESTING STANDARDS

### 6.1 Test Coverage
- **RULE**: Maintain high test coverage
- **TARGET**: 80%+ unit test coverage (backend), 70%+ (frontend)
- **TARGET**: 70%+ integration test coverage
- **CHECK**: All utility functions have unit tests
- **CHECK**: All API endpoints have integration tests
- **CHECK**: Critical user flows have E2E tests (submit document → see flags → review → finalize → download audit PDF)
- **CHECK**: Every evaluator has tests against the fixed accuracy corpus (50 seeded hallucinations + 50 clean examples)

### 6.2 Test Quality
- **RULE**: Tests must be reliable and maintainable
- **CHECK**: Test files co-located with source (`document_service.py` → `test_document_service.py`; `ReviewQueue.tsx` → `ReviewQueue.test.tsx`)
- **CHECK**: Clear test descriptions (Given-When-Then format)
- **CHECK**: No flaky tests (tests pass consistently)
- **CHECK**: Mock external dependencies (CourtListener, Clerk, Stripe) via injected fakes
- **CHECK**: Test edge cases and error scenarios
- **CHECK**: Tenant isolation tested — a user from Firm A must never see Firm B data

### 6.3 Test Types
- **RULE**: Use appropriate test types
- **CHECK**: Unit tests: Pure functions, services, evaluators, hooks (pytest + Vitest/Jest)
- **CHECK**: Integration tests: API endpoints, DB operations (pytest + httpx against real Postgres via testcontainers)
- **CHECK**: Component tests: Client Components with user interactions (React Testing Library)
- **CHECK**: E2E tests: Critical user journeys via Playwright
- **CHECK**: Evaluator accuracy tests: Regression tests on the corpus; gate PRs on accuracy metrics

---

## 7. PERFORMANCE STANDARDS

### 7.1 Frontend Performance
- **RULE**: Fast, responsive user experience
- **TARGET**: First Contentful Paint < 1.5s
- **TARGET**: Time to Interactive < 3.5s
- **TARGET**: Review queue interaction (approve/override) feels instant (<100ms optimistic UI)
- **CHECK**: Bundle size < 500KB (gzipped) for initial JS
- **CHECK**: Images optimized via `next/image` (WebP/AVIF, lazy loading)
- **CHECK**: Fonts optimized via `next/font` (subset, preload, no FOUT)
- **CHECK**: Route-based code splitting (automatic with App Router)
- **CHECK**: Server Components used wherever interactivity isn't required

### 7.2 Backend Performance
- **RULE**: Fast API response times
- **TARGET**: p50 evaluation latency <1,500ms; p95 <3,000ms; p99 <7,000ms
- **TARGET**: Simple DB queries <50ms (p95)
- **TARGET**: PDF audit export <5,000ms (runs in Arq worker, not in request path)
- **CHECK**: Database queries optimized (no N+1; eager loading via `selectinload`/`joinedload`)
- **CHECK**: Proper indexing on `firm_id`, FKs, status/severity/created_at composites
- **CHECK**: Cache CourtListener results in Redis (24h TTL for hits, 1h for misses)
- **CHECK**: Pagination for all list endpoints

### 7.3 Database Performance
- **RULE**: Efficient data access patterns
- **CHECK**: Indexes on foreign keys and frequently queried columns
- **CHECK**: `select(Model.col_a, Model.col_b)` — not whole-row loads when only IDs/few fields needed
- **CHECK**: Batch operations instead of loops
- **CHECK**: Async connection pool configured (asyncpg: min 5, max 20 per instance)
- **CHECK**: `EXPLAIN ANALYZE` reviewed for queries >100ms
- **CHECK**: `log_min_duration_statement = 100` in Postgres to surface slow queries

---

## 8. MAINTAINABILITY

### 8.1 Code Organization
- **RULE**: Logical project structure
- **CHECK**: Feature-based folder structure (frontend: `app/documents/`, `app/queue/`, `app/firm/`; backend: `app/documents/`, `app/evaluators/`, `app/audit/`)
- **CHECK**: Shared utilities in dedicated folders (`lib/` on frontend, `app/common/` on backend)
- **CHECK**: Consistent import ordering (external → internal aliases → relative)
- **CHECK**: Barrel exports (`index.ts` / `__init__.py`) for public APIs of each feature package

### 8.2 Configuration Management
- **RULE**: Externalize configuration
- **CHECK**: Environment-specific configs via `.env.local` (frontend) and `.env` (backend)
- **CHECK**: No hardcoded values in code
- **CHECK**: Type-safe config objects (`pydantic-settings` on backend; typed `env.ts` on frontend with zod validation)
- **CHECK**: Validate env variables on startup; app refuses to boot if required vars are missing

### 8.3 Dependency Management
- **RULE**: Keep dependencies current and minimal
- **CHECK**: Lock files committed (`pnpm-lock.yaml`, `uv.lock` or `poetry.lock`)
- **CHECK**: No unused dependencies (`knip` for frontend, `pip-audit` / `uv` for backend)
- **CHECK**: Security audits passing in CI (`pnpm audit`, `pip-audit`)
- **CHECK**: Major version updates tested thoroughly before merge
- **CHECK**: Dependabot/Renovate enabled
- **REJECT**: Adding large libraries for simple tasks (e.g., lodash when native JS suffices)

### 8.4 Git Practices
- **RULE**: Clean, meaningful git history
- **CHECK**: Descriptive commit messages (conventional commits: `feat(evaluators): add citation existence evaluator`)
- **CHECK**: Small, focused commits (one logical change)
- **CHECK**: Rebase instead of merge commits in feature branches
- **CHECK**: Branch naming: `feature/CG-XXX-description`, `fix/CG-XXX-description`
- **REJECT**: Commits with "WIP", "fix", "temp", "updates"

---

## 9. SPECIFIC PROJECT RULES (CiteGuard)

### 9.1 Document Ingestion & Evaluation Flow
- **RULE**: Submission flow must be resilient, async, and auditable
- **CHECK**: Both SDK (`POST /v1/documents`) and LLM Proxy (`POST /v1/llm/proxy`) paths route through a single `DocumentIngestionService`
- **CHECK**: Return `202 Accepted` immediately; evaluation runs in Arq workers
- **CHECK**: Idempotency enforced via `Idempotency-Key` header (24h window)
- **CHECK**: Max document size enforced at 200KB; reject with 413 above
- **CHECK**: Every submission writes an `audit_log` entry in the same transaction as the `Document` insert
- **CHECK**: Frontend shows submission status via TanStack Query polling or SSE
- **CHECK**: Evaluators run in parallel; overall orchestration wrapped in a concurrency bound

### 9.2 Audit Log Integrity (CRITICAL)
- **RULE**: The audit log is the product. Treat it accordingly.
- **CHECK**: `audit_log` table is append-only; UPDATE and DELETE grants revoked at the database role level (enforced in Alembic migration)
- **CHECK**: Every row's `this_hash = sha256(prior_hash || canonical_json(payload))`
- **CHECK**: Canonical JSON serialization is deterministic (sorted keys, stable numeric formatting, UTF-8 NFC)
- **CHECK**: Genesis row per firm on firm creation
- **CHECK**: Daily background job verifies hash chains for every firm; alerts on divergence
- **CHECK**: Every significant event writes an audit entry (submission, flag creation, reviewer action, finalize, export, API key events, role changes)
- **CHECK**: Audit writes are transactional with the action they record — if the action commits, the audit row commits
- **CHECK**: Sensitive raw content (document text, prompts) is NOT stored in audit payload — store references + hashes instead
- **REJECT**: Any code path writing to `audit_log` outside `AuditLogService`
- **REJECT**: Any attempt to update or delete an audit row
- **REJECT**: Deferring audit writes to a background job (must be synchronous with the action)

### 9.3 Evaluator System Architecture
- **RULE**: Evaluators are isolated, versioned, reproducible strategies
- **CHECK**: Every evaluator implements the `IEvaluator` protocol (`async def evaluate(document) -> list[Flag]`)
- **CHECK**: Every evaluator has a stable `evaluator_id` and a `version` (semver); flags record both
- **CHECK**: Evaluators are idempotent — same input + same version → same flags
- **CHECK**: Evaluators have no side effects beyond their return value (no DB writes, no log pollution)
- **CHECK**: External API dependencies (CourtListener, FJC) accessed via injected clients with retry + circuit breaker
- **CHECK**: Evaluator failures produce system flags (severity ADVISORY, code `CG_E_EVALUATOR_TIMEOUT`) rather than failing the whole verification
- **CHECK**: When evaluator logic materially changes, the version bumps; re-evaluation of affected documents is supported on demand
- **REJECT**: Adding a new evaluator that requires modifying existing evaluators or the orchestrator core
- **REJECT**: Evaluators with hardcoded `if type == "citation"` branching
- **REJECT**: Evaluator logic change without a version bump

### 9.4 Review Queue & Workflow
- **RULE**: The review queue must be fast, reliable, and explicit
- **CHECK**: Queue default sort: severity DESC, submitted_at ASC
- **CHECK**: Reviewer actions: APPROVE, OVERRIDE (requires reason ≥10 chars), REJECT, DEFER
- **CHECK**: Finalize is blocked while any flag is unresolved
- **CHECK**: Optimistic UI on actions (TanStack Query mutations with rollback on error)
- **CHECK**: Keyboard shortcut coverage: every button has a visible, documented shortcut
- **CHECK**: Finalize triggers the audit export Arq job
- **CHECK**: Reviewer cannot act on their own submissions by default (firm-configurable)
- **CHECK**: Flags themselves are immutable post-creation; mutations live on `reviewer_actions`

### 9.5 Firm & User Management
- **RULE**: Proper tenant isolation and role enforcement
- **CHECK**: Every tenant-scoped API requires auth + derives `firm_id` from session/API key, never from payload
- **CHECK**: Only ADMIN can invite/remove users and generate API keys
- **CHECK**: Only ADMIN can change roles; users cannot modify their own role
- **CHECK**: Soft delete for users — historical attribution must remain intact
- **CHECK**: Role changes, user invites/removals, and API key events write audit entries
- **CHECK**: Last-admin safeguard: cannot remove the final admin of a firm
- **CHECK**: Email verification required via Clerk before access

### 9.6 Privileged Data Handling
- **RULE**: Treat every document as privileged attorney-client material
- **CHECK**: Document text encrypted at rest; no ClickHouse trace contains raw text
- **CHECK**: Logs, traces, and Sentry events scrub document content via an explicit allowlist
- **CHECK**: External services receive only minimum necessary data (citation strings, quoted passages — never full documents)
- **CHECK**: US-only data residency in V1; no cross-region replication
- **CHECK**: Sub-processor list maintained publicly; changes require customer notification
- **CHECK**: Default 90-day retention; hard-delete honored within 30 days of request
- **CHECK**: Customer data is NEVER used for model training
- **REJECT**: Logging, caching, or persisting document text outside the primary encrypted store
- **REJECT**: Sending full document text to any third party
- **REJECT**: Storing or processing customer data outside US regions

### 9.7 Accessibility & Responsive Design
- **RULE**: Usable across devices and accessible to all users
- **CHECK**: WCAG 2.1 AA compliance minimum
- **CHECK**: Desktop-first (primary use case is lawyer at workstation) but responsive to 1024px+ without breaking
- **CHECK**: Mobile view (<1024px) shows a read-only dashboard/queue — full review flow is not supported on mobile in V1 and should clearly communicate that
- **CHECK**: Touch-friendly UI elements (min 44px touch targets) on any mobile surface
- **CHECK**: Test on real devices (desktop Chrome, Safari, Edge; Firefox for enterprise users; iPad for read-only views)

---

## 10. CODE REVIEW CHECKLIST

### Before Approving Code, Verify:

#### ✅ Functionality
- [ ] Code solves the stated problem
- [ ] No breaking changes to existing features
- [ ] Edge cases handled
- [ ] Error scenarios handled gracefully

#### ✅ Code Quality
- [ ] Follows naming conventions
- [ ] No code duplication
- [ ] Functions are small and focused
- [ ] Code is self-documenting
- [ ] Comments explain complex logic

#### ✅ Architecture
- [ ] Follows layered architecture
- [ ] Proper separation of concerns
- [ ] No architectural violations
- [ ] Scalable design
- [ ] Tenant isolation preserved

#### ✅ Security
- [ ] No security vulnerabilities
- [ ] Input validation implemented
- [ ] Authentication/authorization correct
- [ ] No sensitive data exposed in logs/traces/errors

#### ✅ Performance
- [ ] No performance regressions
- [ ] Efficient algorithms used
- [ ] Database queries optimized (no N+1, `firm_id` filtered, pagination present)
- [ ] Frontend renders efficiently (RSC by default, memoization where justified)

#### ✅ Testing
- [ ] Unit tests added/updated
- [ ] Integration tests for APIs
- [ ] Tenant isolation tested
- [ ] Tests are passing
- [ ] Good test coverage

#### ✅ Documentation
- [ ] API documentation updated (OpenAPI regenerated)
- [ ] Complex logic documented
- [ ] README updated if needed
- [ ] ADR created for architectural decisions

#### ✅ Dependencies
- [ ] No unnecessary dependencies added
- [ ] Dependencies are up to date
- [ ] License compatibility checked
- [ ] Security audits passing

#### ✅ CiteGuard-Specific
- [ ] Audit log entries written for the action (via `AuditLogService`)
- [ ] No document content in logs, traces, errors, or external calls
- [ ] Hash chain not disturbed
- [ ] Evaluator version bumped if logic changed
- [ ] `firm_id` filter present on every tenant-scoped query

---

## 11. REJECTION CRITERIA (Auto-Reject If Present)

### 🚫 Immediate Rejection
1. **Security vulnerabilities** (SQL injection via raw SQL, XSS in PDF output, exposed secrets)
2. **Hardcoded credentials** or API keys
3. **`print()` / `console.log` statements** in production code
4. **Commented-out code blocks** (>10 lines)
5. **No error handling** in async operations
6. **Breaking changes** without migration plan
7. **Failing tests** in CI/CD pipeline
8. **Linter / type-checker errors** not fixed
9. **No type safety** (`any` abuse in TypeScript, `Any` abuse in Python)
10. **Document content, prompts, or completions** in logs, traces, or error messages
11. **Unhandled promise rejections / un-awaited coroutines**
12. **Direct database access from frontend**
13. **Missing authentication** on protected routes
14. **N+1 query problems** in database access
15. **Writes to `audit_log` outside `AuditLogService`**
16. **Queries on tenant-scoped tables missing a `firm_id` filter**
17. **Mutations of existing audit rows** (UPDATE/DELETE)
18. **Evaluator logic change without a version bump**
19. **Sending document content to third parties** beyond the declared LLM provider
20. **Storing or processing customer data outside US regions**

---

## 12. FEEDBACK GUIDELINES

### When Providing Feedback:

#### 🎯 Be Specific
- ❌ BAD: "This code is hard to read"
- ✅ GOOD: "Consider extracting lines 45–67 into a separate function like `validate_document_submission()` to improve readability"

#### 🎯 Explain the "Why"
- ❌ BAD: "Change this variable name"
- ✅ GOOD: "Rename `data` to `document_payload` to make it clear what structure this represents. Generic names hide intent."

#### 🎯 Suggest Solutions
- ❌ BAD: "This won't scale"
- ✅ GOOD: "Evaluators run sequentially here; this blows past our 3s p95 budget. Wrap them in `asyncio.gather(*(ev.evaluate(doc) for ev in evaluators))` with a semaphore to bound concurrency."

#### 🎯 Prioritize Issues
1. **Critical (P0)**: Security vulnerabilities, data loss, audit integrity, tenant isolation breach, privileged data leak
2. **High (P1)**: Performance regressions, architecture violations, missing error handling, missing tenant filters
3. **Medium (P2)**: Code quality, maintainability, test gaps, duplication
4. **Low (P3)**: Naming, formatting, minor optimizations

#### 🎯 Provide Examples
- Always include code examples for suggested changes
- Reference similar patterns from the existing codebase
- Link to the relevant ADR, the V1 PRD, or the backend/frontend guidelines doc

---

## 13. CONTINUOUS IMPROVEMENT

### Review Metrics to Track:
- Code review turnaround time (target: <1 business day for first pass)
- Number of iterations per PR (target: <3)
- Common issues found (update rules accordingly)
- Test coverage trends
- Evaluator accuracy metrics on the corpus (per evaluator, per version)
- p95 API latency trends
- Security vulnerability trends (dependency scans)
- Hash-chain verification job results (should always pass)

### Regular Activities:
- **Weekly**: Review and update rules based on new findings
- **Monthly**: Analyze code quality, performance, and evaluator accuracy metrics
- **Quarterly**: Architecture review, refactoring planning, SOC 2 readiness check
- **Ongoing**: Stay current with Next.js, FastAPI, SQLAlchemy, and legal-tech best practices

---

## 🎓 REMEMBER

**Only change what is explicitly requested.**

Resist the temptation to "improve" code that wasn't part of the request. Every unnecessary change increases bug risk and makes reviews harder.

**When in doubt:**
- ❓ Ask for clarification
- 📖 Read existing code for patterns
- 🔍 Search for similar implementations
- 🚫 Don't assume or guess

---

## FINAL NOTE

These rules are living guidelines, not rigid constraints. Use professional judgment when exceptions are warranted, but always document the reasoning. The goal is to maintain high code quality while enabling the team to deliver value efficiently.

At CiteGuard, the bar is not "works in dev." The bar is "survives scrutiny from a malpractice carrier, a state bar ethics investigator, a federal judge, and a SOC 2 auditor." Every architectural decision should serve that bar.

**Remember**: Good architecture is about making decisions that are easy to change later, not about making perfect decisions upfront. Our two non-negotiables — **audit integrity** and **tenant isolation** — are the exceptions; everything else is up for reasoned debate.