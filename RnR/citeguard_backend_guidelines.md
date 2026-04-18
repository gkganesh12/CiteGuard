# Backend Developer - Development Guidelines & Standards (FastAPI + SQLAlchemy + PostgreSQL)

## Role Overview
As a Senior Backend Developer on the CiteGuard project, you are responsible for:
- **Building & Shipping Features**: Developing robust APIs and business logic from requirements to production
- **Code Quality**: Writing clean, maintainable, and well-documented code
- **Architecture**: Designing scalable systems following SOLID principles and clean architecture
- **Performance**: Optimizing database queries, API response times, and resource usage
- **Security**: Implementing security best practices, preventing vulnerabilities, and protecting privileged legal data
- **Testing**: Writing comprehensive unit and integration tests, including evaluator accuracy tests against a fixture corpus
- **Database Design**: Creating efficient schemas and managing migrations, with strict append-only rules for the audit log
- **Code Review**: Reviewing peer code and providing constructive feedback
- **Collaboration**: Working with frontend developers, designers, and product managers

This document serves as your comprehensive guide for development standards, best practices, and rules to follow while building features and reviewing code.

> **⚠️ Domain criticality notice:** CiteGuard processes privileged legal documents for law firms. A bug here is not an inconvenience — it is potential malpractice exposure for our customers and a compliance event for us. Every rule in this document exists because a failure mode is real.

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · PostgreSQL 16 · ClickHouse · Arq (Redis-backed queues) · Clerk (auth) · Stripe (billing) · WeasyPrint (PDF) · pytest

---

## Table of Contents

### Core Principles & Architecture
1. [SOLID Principles (Mandatory)](#1-solid-principles-mandatory)
2. [Code Duplication (Zero Tolerance)](#2-code-duplication-zero-tolerance)
3. [Performance Optimization](#3-performance-optimization)

### Framework & Technology Best Practices
4. [FastAPI Architectural Patterns](#4-fastapi-architectural-patterns)
5. [SQLAlchemy + Alembic Best Practices](#5-sqlalchemy--alembic-best-practices)

### Security & Quality
6. [Security (Critical)](#6-security-critical)
7. [Error Handling & Logging](#7-error-handling--logging)
8. [Testing Requirements](#8-testing-requirements)
9. [Code Quality & Maintainability](#9-code-quality--maintainability)

### Project-Specific Guidelines
10. [Specific Project Rules (CiteGuard)](#10-specific-project-rules-citeguard)
11. [API Design Standards](#11-api-design-standards)
12. [Environment & Configuration](#12-environment--configuration)

### Workflow & Process
13. [Development Workflow](#13-development-workflow)
14. [Code Review Checklist](#14-code-review-checklist)
15. [Rejection Criteria](#15-rejection-criteria-development--code-review)
16. [Collaboration & Communication](#16-collaboration--communication)

### Philosophy & Mindset
- [Developer Mindset](#-developer-mindset)
- [Final Note](#final-note)

---

## 1. SOLID PRINCIPLES (MANDATORY)

### 1.1 Single Responsibility Principle (SRP)
- **RULE**: Each class/module must have ONE reason to change
- **CHECK**: Routers (FastAPI `APIRouter`) only handle HTTP requests/responses, no business logic
- **CHECK**: Services contain business logic, no direct database access
- **CHECK**: Repositories handle database operations only
- **CHECK**: Pydantic schemas only define data structure + declarative validation; no business rules
- **CHECK**: SQLAlchemy models represent database structure only, no business logic
- **CHECK**: Auth dependencies only handle authentication/authorization, no business logic
- **CHECK**: Middleware only handles cross-cutting request/response concerns, no business logic
- **CHECK**: Evaluators perform one verification check only (e.g., `CitationExistenceEvaluator` does NOT also do Bluebook formatting)
- **REJECT**: Services with more than 10 public methods (split into multiple services)
- **REJECT**: Routers containing business logic (if/else for business rules)
- **REJECT**: Repositories with business logic calculations
- **REJECT**: Evaluators that combine multiple verification concerns

### 1.2 Open/Closed Principle (OCP)
- **RULE**: Open for extension, closed for modification
- **CHECK**: Use abstract base classes (`abc.ABC`) or `Protocol` for extensible behavior
- **CHECK**: Strategy pattern for evaluators — adding a new evaluator (e.g., `StatutoryCurrencyEvaluator` in V1.1) must NOT require modifying existing evaluators
- **CHECK**: Strategy pattern for notification channels (email, Slack, webhook)
- **CHECK**: Factory pattern for creating evaluator instances from configuration
- **CHECK**: Use dependency injection (FastAPI `Depends`, or a registry) to swap implementations
- **CHECK**: Avoid if/elif chains on type discriminators for business logic (use polymorphism)
- **REJECT**: Modifying existing evaluators to add a new check type
- **REJECT**: Hard-coded type checks (`if evaluator_type == 'citation_existence': ...`)
- **EXAMPLE**: `EvaluatorOrchestrator` depends on a registered list of `IEvaluator` implementations; each implements `async def evaluate(self, document: Document) -> list[Flag]`. Adding a 6th evaluator = add a new class + register it. Zero changes to existing code.

### 1.3 Liskov Substitution Principle (LSP)
- **RULE**: Derived classes must be substitutable for base classes
- **CHECK**: Subclasses don't raise new exceptions not declared in the base class
- **CHECK**: Subclasses don't weaken preconditions
- **CHECK**: Subclasses don't strengthen postconditions
- **CHECK**: Method signatures match in derived classes (same params, compatible return types)
- **CHECK**: Every `IEvaluator` implementation returns `list[Flag]` (possibly empty) — never `None`, never raises for "no flags found"
- **REJECT**: Derived class that raises `NotImplementedError` for required methods
- **REJECT**: Overriding methods with incompatible return types
- **REJECT**: Subclass that requires more parameters than base class

### 1.4 Interface Segregation Principle (ISP)
- **RULE**: No client should depend on methods it doesn't use
- **CHECK**: Interfaces (`Protocol` or ABC) are small and focused (max 5 methods)
- **CHECK**: Split large interfaces into role-specific interfaces
- **CHECK**: Services depend only on the interfaces they actually use
- **REJECT**: "God interfaces" with 10+ methods
- **REJECT**: Empty method implementations (method not needed but required by interface)
- **EXAMPLE**: Split `IDocumentRepository` into `IDocumentReader` (findById, listByFirm) and `IDocumentWriter` (create, updateStatus, softDelete). `ReviewQueueService` only needs `IDocumentReader`.

### 1.5 Dependency Inversion Principle (DIP)
- **RULE**: Depend on abstractions, not concretions
- **CHECK**: All dependencies injected via constructor or FastAPI `Depends`
- **CHECK**: Services depend on Protocols/ABCs, not concrete classes
- **CHECK**: Providers registered via a dependency-injection layer (FastAPI `Depends` + a small container)
- **REJECT**: Direct instantiation with `ConcreteService()` in business logic
- **REJECT**: Module-level singletons that hide coupling
- **REJECT**: Importing concrete implementations in services
- **MANDATE**: Always inject the database session (`AsyncSession`) via `Depends(get_db)` — never instantiate engines in business logic
- **MANDATE**: Always inject external API clients (`ICourtListenerClient`) — never call `httpx.get("https://www.courtlistener.com/...")` inside services

---

## 2. CODE DUPLICATION (ZERO TOLERANCE)

### 2.1 Duplication Detection
- **RULE**: No code duplication beyond 3 lines
- **CHECK**: Identical logic in multiple services must be extracted
- **CHECK**: Similar database queries must be centralized in repositories
- **CHECK**: Repeated validation logic must use shared Pydantic validators or custom validator functions
- **CHECK**: Common error handling must use base exceptions + global exception handlers
- **CHECK**: Citation-parsing logic lives in exactly one place (`CitationParserService`) — never reimplement
- **REJECT**: Copy-pasted code blocks
- **REJECT**: Similar functions differing only by entity type (use generics)

### 2.2 Extraction Strategies
- **RULE**: Extract duplication to appropriate layers
- **CHECK**: Common business logic → Shared service
- **CHECK**: Common database queries → Base repository
- **CHECK**: Common validations → Pydantic validators / reusable validator functions
- **CHECK**: Common transformations → Utility functions in `app/common/utils/`
- **CHECK**: Common error handling → Custom exception classes + global `@app.exception_handler`
- **CHECK**: Common response formatting → Response models / middleware
- **CHECK**: Common evaluator scaffolding (severity classification, offset tracking, confidence scoring) → `BaseEvaluator` abstract class

### 2.3 Generic Solutions
- **RULE**: Use Python generics (`TypeVar`, `Generic`) for type-safe reusability
- **CHECK**: Generic repository base class for CRUD operations (`BaseRepository[T]`)
- **CHECK**: Generic pagination response wrapper (`PaginatedResponse[T]`)
- **CHECK**: Generic response envelope (`ApiResponse[T]`)
- **CHECK**: Generic validation helpers
- **MANDATE**: `BaseRepository[ModelT]` provides `get_by_id`, `list_by_firm`, `create`, `update`, `soft_delete` — with built-in `firm_id` scoping enforcement so multi-tenant isolation cannot be accidentally skipped

### 2.4 Constants & Configuration
- **RULE**: No magic numbers or strings
- **CHECK**: Extract all constants to dedicated modules (`app/constants/`)
- **CHECK**: Use `enum.StrEnum` / `enum.IntEnum` for fixed sets of values (`Severity`, `EvaluatorType`, `UserRole`, `DocumentStatus`, `ReviewerAction`)
- **CHECK**: Use `pydantic-settings` for environment-specific values
- **REJECT**: Hard-coded strings for status values
- **REJECT**: Hard-coded numbers for pagination limits, rate-limit buckets, or severity thresholds
- **MANDATE**: All error messages in `app/constants/messages.py` with error codes like `CG_E_CITATION_PARSE_FAIL`

---

## 3. PERFORMANCE OPTIMIZATION

### 3.1 Database Query Optimization
- **RULE**: Optimize every database interaction
- **CHECK**: Use `select(Model.col_a, Model.col_b)` to fetch only required columns, never load full rows when not needed
- **CHECK**: Use `selectinload` / `joinedload` deliberately — avoid lazy loading in async contexts (will raise)
- **CHECK**: Implement pagination on every list endpoint (default: 20 items, max 100)
- **CHECK**: Use keyset (cursor) pagination for large datasets (`AuditLog`, `Flag`)
- **CHECK**: Add indexes on frequently queried fields: `firm_id`, `status`, `severity`, `created_at`, foreign keys
- **CHECK**: Use `limit()` and `offset()` consistently; never unbounded queries
- **CHECK**: Use `func.count()` separately if not needed on every list request
- **REJECT**: `session.scalars(select(Model))` without a `.limit()`
- **REJECT**: N+1 query patterns (always measure with `sqlalchemy.log` or `echo=True` in dev)
- **REJECT**: Fetching entire rows when only IDs are needed
- **REJECT**: Sequential awaited queries that could run with `asyncio.gather`

### 3.2 Query Batching & Caching
- **RULE**: Minimize database round trips
- **CHECK**: Use `asyncio.gather()` for parallel independent queries/HTTP calls
- **CHECK**: Use transactions (`async with session.begin():`) for related writes
- **CHECK**: Cache external-API results (CourtListener opinion lookups) in Redis with appropriate TTLs — 24h for hits, 1h for misses
- **CHECK**: Cache computed values (court hierarchies, FJC judge directory) that rarely change — refresh via scheduled Arq job
- **REJECT**: Sequential awaited calls in `for` loops
- **REJECT**: Fetching the same data multiple times in one request
- **MANDATE**: Cache user/firm/role data for the duration of a request via request-scoped cache

### 3.3 Async Operations & Concurrency
- **RULE**: Never block the event loop
- **CHECK**: All I/O is `async` — database (async SQLAlchemy), HTTP (httpx async), file I/O (aiofiles)
- **CHECK**: Use Arq jobs for long-running work (PDF export, evaluator pipeline, email sending)
- **CHECK**: Use streams/chunks for large text processing (documents up to 200KB)
- **CHECK**: Use `concurrent.futures.ProcessPoolExecutor` only for truly CPU-bound work (PDF rendering if inline)
- **REJECT**: Synchronous filesystem operations in the request path
- **REJECT**: Blocking calls (`time.sleep`, `requests.get`, sync `open()` on large files) in async code
- **REJECT**: Running heavy sync code in async endpoints
- **MANDATE**: PDF audit export runs in an Arq worker, not inline in the request handler

### 3.4 Memory Management
- **RULE**: Prevent memory leaks and excessive usage
- **CHECK**: Close/dispose database sessions properly (rely on `Depends(get_db)` context management)
- **CHECK**: Close HTTP clients on shutdown (`lifespan` events)
- **CHECK**: Stream large response bodies with `StreamingResponse`
- **CHECK**: Limit request payload size (max 200KB of document text per submission — reject with 413)
- **CHECK**: Implement memory monitoring in production (Sentry + Prometheus)
- **REJECT**: Loading entire opinion corpora into memory repeatedly (keep a long-lived cached index)
- **REJECT**: Creating large lists unnecessarily — use generators where possible
- **REJECT**: Un-awaited or dangling async tasks

### 3.5 Response Time Optimization
- **RULE**: Fast API responses for good UX
- **TARGET**: p50 evaluation latency <1,500ms; p95 <3,000ms; p99 <7,000ms
- **TARGET**: Simple DB queries <50ms
- **CHECK**: Indexes on foreign keys (`firm_id`, `document_id`, `user_id`)
- **CHECK**: Use `EXPLAIN ANALYZE` on complex queries; log plans for queries >100ms
- **CHECK**: Response compression via reverse proxy (Cloudflare / Fly.io edge)
- **CHECK**: ETags / 304 on cacheable resources (rare in CiteGuard — most data is tenant-scoped)
- **CHECK**: Return 202 Accepted with a job ID for evaluator submissions; evaluation happens in workers
- **REJECT**: Synchronous blocking operations >500ms in request handlers

---

## 4. FASTAPI ARCHITECTURAL PATTERNS

### 4.1 Package Organization
- **RULE**: Feature-based modular architecture
- **CHECK**: Each feature has its own package (`app/documents/`, `app/evaluators/`, `app/audit/`, `app/users/`)
- **CHECK**: Each package exposes a single `APIRouter` and its public services
- **CHECK**: Shared functionality in `app/common/` (utils, exceptions, dependencies)
- **CHECK**: Maximum 10 services/providers per package; split if larger
- **CHECK**: Clear package dependencies; avoid circular imports (enforced via pre-commit)
- **REJECT**: Monolithic `main.py` with all routes and logic
- **REJECT**: Circular imports between feature packages
- **REJECT**: Cross-feature direct imports beyond the exposed service interface (use events or the shared service layer)

### 4.2 Router Design
- **RULE**: Thin routers, fat services
- **CHECK**: Each `routes.py` file max 200 lines; split if larger
- **CHECK**: Each endpoint function max 20 lines (usually much less)
- **CHECK**: Request/response shapes declared via Pydantic models (`schemas.py`)
- **CHECK**: Use `tags=[...]` in routers for OpenAPI grouping
- **CHECK**: Explicit `status_code=` on every endpoint
- **CHECK**: Path params typed (`document_id: UUID`) so FastAPI auto-validates
- **CHECK**: Query params via `Query(...)` with constraints (`ge=`, `le=`, `max_length=`)
- **CHECK**: No try/except in routers — use global exception handlers
- **REJECT**: Business logic in routers
- **REJECT**: Direct database queries in routers
- **REJECT**: Validation logic in routers (Pydantic handles it)
- **REJECT**: Multiple try/except blocks (use exception handlers)

### 4.3 Service Design
- **RULE**: Services contain business logic only
- **CHECK**: Services focused on single domain (one aggregate root per service)
- **CHECK**: Services use repositories for data access, not `AsyncSession` directly
- **CHECK**: Services return Pydantic DTOs, not ORM models (avoid leaking ORM state)
- **CHECK**: All methods testable (dependencies injected)
- **CHECK**: Use transactions for multi-step writes
- **CHECK**: Raise custom exceptions (`DocumentNotFound`, `EvaluatorFailed`) caught by global handlers
- **REJECT**: Services that import `AsyncSession` directly (go through repository)
- **REJECT**: Services with more than 15 methods (split responsibility)
- **REJECT**: Module-level functions doing business logic (use classes for testability)

### 4.4 Repository Pattern
- **RULE**: Centralize all database access
- **CHECK**: One repository per aggregate root (`DocumentRepository`, `FlagRepository`, `AuditLogRepository`)
- **CHECK**: Repositories extend `BaseRepository[ModelT]` for standard CRUD
- **CHECK**: Repositories take `AsyncSession` via constructor injection
- **CHECK**: Repository methods are atomic — single query or single transaction
- **CHECK**: Return ORM entities or `None` — never empty objects, never undefined-like values
- **CHECK**: Every query must filter by `firm_id` — enforce via a required parameter on every list method
- **REJECT**: Business logic in repositories
- **REJECT**: Repositories touching multiple unrelated aggregates
- **REJECT**: Direct `AsyncSession` usage in services
- **REJECT**: Queries that could cross tenants (missing `firm_id` filter)
- **MANDATE**: All SQLAlchemy calls go through repositories

### 4.5 Pydantic Schemas (DTOs)
- **RULE**: Use Pydantic models for all inputs and outputs
- **CHECK**: Separate schemas for Create, Update, Response (e.g., `DocumentCreate`, `DocumentUpdate`, `DocumentResponse`)
- **CHECK**: Use Pydantic v2 validators (`@field_validator`, `@model_validator`) for complex validation
- **CHECK**: Use `Field(..., description=...)` for OpenAPI documentation
- **CHECK**: Schemas are immutable by default (`model_config = ConfigDict(frozen=True)` where appropriate)
- **CHECK**: Compose with inheritance or `create_model` for reuse — equivalent of NestJS's PartialType/PickType
- **CHECK**: Response schemas never expose internal fields (e.g., never return `password_hash`, `api_key_hash`)
- **REJECT**: Returning ORM models directly from routers
- **REJECT**: Validation logic outside schemas or validators (no ad-hoc checks in services)
- **REJECT**: Schemas with business logic methods

### 4.6 Dependencies, Middleware, and Exception Handlers
- **RULE**: Proper use of FastAPI features
- **CHECK**: Dependencies (`Depends(...)`) used for auth (`get_current_user`), DB sessions (`get_db`), pagination parsing
- **CHECK**: Middleware used for logging, request IDs, tracing, compression, CORS
- **CHECK**: Pydantic handles validation; custom validators for complex rules (citation format, severity ranges)
- **CHECK**: Global exception handlers (`@app.exception_handler(CustomException)`) produce uniform error responses
- **CHECK**: Use lifespan events for startup/shutdown (DB pool, HTTP clients, cache warmers)
- **REJECT**: Business logic inside auth dependencies
- **REJECT**: Direct DB access in middleware (use dependencies instead)
- **REJECT**: Multiple concerns in a single dependency or middleware

---

## 5. SQLALCHEMY + ALEMBIC BEST PRACTICES

### 5.1 Schema Design
- **RULE**: Well-designed, normalized schema
- **CHECK**: All tables have `id` (UUID v7 or ULID for time-sortable primary keys), `created_at`, `updated_at`
- **CHECK**: Soft deletes use `deleted_at: Mapped[datetime | None]` column
- **CHECK**: Foreign keys with proper `ondelete=` and `onupdate=` actions
- **CHECK**: Appropriate types (`TIMESTAMPTZ` for timestamps, `NUMERIC` for money, `JSONB` for semi-structured data)
- **CHECK**: Unique constraints where needed (`UniqueConstraint("firm_id", "email", name="uq_firm_email")`)
- **CHECK**: Indexes on foreign keys and frequently queried columns
- **CHECK**: Composite indexes for multi-column queries (`(firm_id, status, created_at)` on `documents`)
- **CHECK**: `audit_log` table is append-only — no UPDATE or DELETE permissions granted on it at the DB role level
- **REJECT**: `VARCHAR(255)` as a default — use `TEXT` or a precisely-sized VARCHAR based on actual constraint
- **REJECT**: Missing indexes on foreign keys
- **REJECT**: Missing timestamps
- **REJECT**: Any ability to UPDATE or DELETE `audit_log` rows

### 5.2 Query Best Practices
- **RULE**: Efficient, type-safe queries
- **CHECK**: Use SQLAlchemy 2.0 style (`select(Model).where(...)`)
- **CHECK**: Always handle `None` from `session.scalar(...)` explicitly
- **CHECK**: Always filter soft-deleted records (`where(Model.deleted_at.is_(None))`) unless explicitly retrieving history
- **CHECK**: Use `selectinload` / `joinedload` for eager loading instead of N+1
- **CHECK**: Use `select(Model.col_a, Model.col_b)` to limit fields
- **CHECK**: Use `order_by(...)` for consistent ordering (always include a tiebreaker like `id`)
- **CHECK**: Use unique indexed lookups (`session.scalar(select(Model).where(Model.id == x))`) — not `LIMIT 1` on non-unique
- **REJECT**: Ignoring type errors from mypy/pyright
- **REJECT**: Assuming a query returned a row without a `None` check
- **REJECT**: Using `Any` or `# type: ignore` on SQLAlchemy results

### 5.3 Transaction Management
- **RULE**: Use transactions for data consistency
- **CHECK**: Use `async with session.begin():` for related writes
- **CHECK**: Keep transactions short and focused — never make external HTTP calls inside a transaction
- **CHECK**: Handle transaction failures with rollback (automatic with context manager)
- **CHECK**: For complex multi-step work, use a SAGA-style approach with compensating actions — not long transactions
- **REJECT**: Multiple separate writes that should be atomic
- **REJECT**: External API calls inside transactions (holds DB locks while waiting on network)
- **REJECT**: Ignoring rollback errors
- **MANDATE**: Every write that touches `documents` + `flags` + `audit_log` in the same business operation must be in a single transaction

### 5.4 Migrations (Alembic)
- **RULE**: Safe, versioned schema changes
- **CHECK**: Review auto-generated migration SQL before committing
- **CHECK**: Test migration on a copy of production-shaped data
- **CHECK**: Migrations have proper `upgrade()` AND `downgrade()` paths
- **CHECK**: For large tables, add indexes via `CREATE INDEX CONCURRENTLY` (post-migration script) to avoid locks
- **CHECK**: Data migrations are separate from schema migrations
- **CHECK**: Migration names are descriptive (`alembic revision -m "add_severity_index_on_flags"`)
- **REJECT**: Editing existing migrations that have run anywhere
- **REJECT**: Skipping migration review
- **REJECT**: Destructive migrations (DROP COLUMN) without a data backup plan and a two-phase deploy
- **REJECT**: Migrations that alter the `audit_log` table in destructive ways

### 5.5 Performance with SQLAlchemy
- **RULE**: Optimize SQLAlchemy usage
- **CHECK**: Connection pool configured (asyncpg pool, `min_size=5`, `max_size=20` per instance)
- **CHECK**: Use `select` with pagination; never load entire tables
- **CHECK**: Avoid N+1 with explicit eager loading
- **CHECK**: Use Core (`text("...")` or `sqlalchemy.sql`) for complex aggregations
- **CHECK**: Monitor slow query log (`log_min_duration_statement = 100` in Postgres)
- **REJECT**: Fetching all records without a limit
- **REJECT**: Deeply nested eager loads (>3 levels)
- **REJECT**: Loading relations not used in the code path

---

## 6. SECURITY (CRITICAL)

### 6.1 Input Validation & Sanitization
- **RULE**: Never trust any input
- **CHECK**: All request bodies validated via Pydantic models (automatic with FastAPI)
- **CHECK**: Pydantic `model_config = ConfigDict(extra="forbid")` on all inputs — no extra fields accepted
- **CHECK**: Sanitize any HTML content in outputs (shouldn't occur in V1, but PDF generation must escape)
- **CHECK**: Validate file uploads (content type, size, content bytes) — though V1 has no file uploads
- **CHECK**: Email formats validated via `EmailStr`
- **CHECK**: UUIDs validated via `UUID` type in path params
- **CHECK**: Max document text size enforced (200KB — reject with 413)
- **REJECT**: Accepting arbitrary JSON without a schema
- **REJECT**: Using user input directly in raw SQL strings
- **REJECT**: Trusting any client-provided ID without authorization check
- **REJECT**: Allowing undefined fields on request bodies (set `extra="forbid"`)

### 6.2 Authentication & Authorization
- **RULE**: Secure every protected endpoint
- **CHECK**: Authentication via Clerk (verify JWT via Clerk SDK or JWKS)
- **CHECK**: JWTs short-lived (access token 15 min); refresh handled by Clerk
- **CHECK**: API keys hashed with bcrypt before storage (min cost factor 12)
- **CHECK**: `get_current_user` dependency applied to every protected router
- **CHECK**: Role-based checks via a `require_role(Role.ADMIN)` dependency factory
- **CHECK**: `@public` explicit on any endpoint that does not require auth
- **CHECK**: JWT/API-key secrets loaded from environment only; never committed
- **CHECK**: Signature and expiration always validated; never trust `exp` alone without signature check
- **REJECT**: Storing plaintext API keys
- **REJECT**: Using weak hashing (MD5, SHA1) for credentials
- **REJECT**: Unauthenticated endpoints without explicit `@public` marker
- **REJECT**: Hardcoded secrets in code
- **MANDATE**: Every route must explicitly declare its auth requirements

### 6.3 Authorization & Access Control (Multi-Tenancy)
- **RULE**: Principle of least privilege, enforced tenant isolation
- **CHECK**: Role-based access: `ADMIN`, `REVIEWER`, `SUBMITTER`
- **CHECK**: Resource ownership: every query filtered by `firm_id` derived from the authenticated user
- **CHECK**: Ownership verified at service layer, not only at router layer
- **CHECK**: Audit logs for sensitive operations (API key creation, user role change, data export)
- **CHECK**: Firm ID comes from the authenticated session — NEVER from the request body or URL unless cross-checked
- **REJECT**: Trusting `firm_id` or `user_id` from request payloads
- **REJECT**: Missing ownership checks on update/delete/export operations
- **REJECT**: Admin-only operations without a role check
- **MANDATE**: Every repository list/get method takes `firm_id` as a required argument; the base repository enforces it

### 6.4 SQL Injection & XSS Prevention
- **RULE**: Prevent injection attacks
- **CHECK**: Use SQLAlchemy parameterized queries (default behavior with ORM + Core)
- **CHECK**: When raw SQL is needed, use `text("... :param ...")` with bound params — never f-strings
- **CHECK**: Never concatenate user input into SQL, ever
- **CHECK**: PDF export sanitizes all text (WeasyPrint treats it as text by default; verify no HTML injection in document content)
- **CHECK**: JSON responses properly escape; avoid custom serializers unless reviewed
- **REJECT**: `session.execute(text(f"SELECT * FROM x WHERE id = {user_id}"))` — never
- **REJECT**: Any use of string formatting in SQL
- **REJECT**: Rendering unsanitized user content in PDFs
- **MANDATE**: Never concatenate user input into SQL

### 6.5 Data Protection & Privacy
- **RULE**: Protect sensitive data — especially privileged legal content
- **CHECK**: Never log document text, prompts, or completions in application logs
- **CHECK**: Never include document content in error responses or stack traces
- **CHECK**: Mask sensitive fields in logs (`api_key`, `email`, `document.text`) via a structlog processor
- **CHECK**: Enforce HTTPS in production (HSTS header)
- **CHECK**: Secure cookie flags where cookies are used (`HttpOnly`, `Secure`, `SameSite=Strict`)
- **CHECK**: Rate limiting on auth and submission endpoints
- **CHECK**: Document text encrypted at rest (AES-256 via managed Postgres encryption)
- **REJECT**: Logging full request bodies
- **REJECT**: Returning document content in error messages
- **REJECT**: Exposing stack traces to clients
- **REJECT**: Any path where document text leaves the US (residency violation)
- **MANDATE**: A log sanitizer middleware strips known-sensitive fields before any log write

### 6.6 API Security
- **RULE**: Secure API endpoints
- **CHECK**: Rate limiting via `slowapi` or Redis-backed limiter — defaults 100 req/15min per IP; 10 req/min on auth endpoints
- **CHECK**: CORS via `fastapi.middleware.cors.CORSMiddleware` with an explicit allow-list — no wildcards
- **CHECK**: Security headers via middleware (CSP, X-Content-Type-Options, Referrer-Policy, X-Frame-Options)
- **CHECK**: `Content-Type: application/json` required on POST/PUT/PATCH
- **CHECK**: Request body size limited (reverse proxy + FastAPI)
- **CHECK**: API versioning via URL prefix (`/v1/...`)
- **CHECK**: CSRF not applicable for pure API with bearer tokens; for any cookie-based flow, apply CSRF
- **REJECT**: Wildcard CORS (`allow_origins=["*"]`)
- **REJECT**: No rate limiting on authentication endpoints
- **REJECT**: Large requests without size limits
- **MANDATE**: Apply tightest rate-limit bucket on `/v1/documents` (submission) and any auth route

---

## 7. ERROR HANDLING & LOGGING

### 7.1 Exception Handling
- **RULE**: Comprehensive, consistent error handling
- **CHECK**: Define a base `CiteGuardException` with `status_code`, `error_code`, `message`
- **CHECK**: Subclass for specific errors: `DocumentNotFound`, `EvaluatorFailed`, `RateLimitExceeded`, `InvalidCitation`, `AuditChainBroken`
- **CHECK**: Global `@app.exception_handler(CiteGuardException)` returns uniform JSON
- **CHECK**: Proper HTTP status codes (see Section 11)
- **CHECK**: Error codes stable across versions; documented in API docs
- **REJECT**: Raising bare `Exception` or `RuntimeError` for known conditions
- **REJECT**: Exposing internal errors or stack traces to clients
- **REJECT**: Swallowing exceptions silently (`except: pass`)
- **REJECT**: Try/except blocks in routers (let global handlers work)

### 7.2 Error Response Format
- **RULE**: Consistent error response structure
- **CHECK**: Format: `{ "error": { "code": "CG_E_...", "message": "...", "details": [...] }, "request_id": "...", "timestamp": "..." }`
- **CHECK**: Include `request_id` (generated by middleware) for tracing
- **CHECK**: Pydantic validation errors formatted consistently with `details`
- **CHECK**: i18n-ready: message keys resolved from a catalog
- **REJECT**: Different error shapes across endpoints
- **REJECT**: Stack traces in production responses
- **REJECT**: Vague "Internal Server Error" without a correlation ID for support

### 7.3 Logging Standards
- **RULE**: Comprehensive, structured logging
- **CHECK**: Use `structlog` with JSON output in production, pretty output locally
- **CHECK**: Levels: `error`, `warning`, `info`, `debug` (never `print`)
- **CHECK**: Every log record includes: `request_id`, `firm_id` (if any), `user_id` (if any), `route`, `duration_ms`
- **CHECK**: Log all unhandled exceptions with context
- **CHECK**: Log slow queries (>100ms) with the query signature
- **CHECK**: Log authentication failures (without the attempted credential)
- **CHECK**: Structured logging only — no unstructured string concatenation
- **REJECT**: `print()` anywhere in application code
- **REJECT**: Logging document text, prompts, or completions
- **REJECT**: Logging full objects without explicit filtering
- **MANDATE**: CI grep check rejects any PR containing `print(` in `app/`

### 7.4 Monitoring & Alerting
- **RULE**: Proactive error detection
- **CHECK**: `/healthz` (liveness) and `/readyz` (readiness, checks DB + Redis) endpoints
- **CHECK**: Sentry configured for error tracking; scrubs document content via `before_send`
- **CHECK**: Alerts on error rate spikes, p95 latency breaches, queue depth growth
- **CHECK**: Track API response times per route
- **CHECK**: Monitor DB pool utilization and Redis queue depth
- **CHECK**: Monitor CourtListener rate-limit response headers; alert if we approach the cap
- **REJECT**: Production without monitoring
- **REJECT**: Silent failures without logs

---

## 8. TESTING REQUIREMENTS

### 8.1 Unit Testing
- **RULE**: High unit test coverage
- **TARGET**: 80%+ coverage
- **CHECK**: Test all service methods
- **CHECK**: Test all utility and pure functions
- **CHECK**: Mock external dependencies (`CourtListenerClient`, `ClerkClient`, `StripeClient`) via `pytest-mock` or injected fakes
- **CHECK**: Test edge cases and error paths
- **CHECK**: Use `pytest` + `pytest-asyncio` for async tests
- **CHECK**: Follow AAA pattern (Arrange, Act, Assert)
- **CHECK**: Every evaluator has a dedicated test module with the fixture corpus of seeded hallucinations + clean examples
- **REJECT**: Testing implementation details instead of observable behavior
- **REJECT**: Brittle tests coupled to private helpers
- **REJECT**: Tests that call real external APIs (except in explicit integration suites)

### 8.2 Integration Testing
- **RULE**: Test API endpoints end-to-end
- **CHECK**: Use `httpx.AsyncClient` with FastAPI's `app` for in-process integration tests
- **CHECK**: Test every endpoint
- **CHECK**: Test auth and role enforcement
- **CHECK**: Test DB operations against a real Postgres (testcontainers or a dedicated CI DB)
- **CHECK**: Test error paths (400, 401, 403, 404, 409, 422, 429, 500)
- **CHECK**: Test pagination and filtering
- **CHECK**: Test tenant isolation — a user from firm A must never see firm B data
- **REJECT**: Tests that depend on execution order
- **REJECT**: Tests that hit production or shared dev DBs
- **REJECT**: Hardcoded timestamps/IDs in assertions (use factories)

### 8.3 Test Data Management
- **RULE**: Clean, isolated test data
- **CHECK**: Use `factory_boy` or custom factories for fixtures (`FirmFactory`, `UserFactory`, `DocumentFactory`)
- **CHECK**: Wrap each test in a transaction that rolls back (`pytest-asyncio` + session rollback fixture)
- **CHECK**: Seed minimal data per test
- **CHECK**: Maintain a fixed "evaluator corpus" of 100 documents (50 with seeded hallucinations, 50 clean) for evaluator accuracy tests
- **REJECT**: Tests depending on specific global DB state
- **REJECT**: Shared mutable fixtures across tests
- **REJECT**: Data left behind after a test run

### 8.4 Test Quality
- **RULE**: Maintainable, reliable tests
- **CHECK**: Clear test names (`test_citation_existence_flags_hallucinated_cite`)
- **CHECK**: One concept per test (one assertion focus)
- **CHECK**: Fast unit tests (<100ms each)
- **CHECK**: No flaky tests — if it fails sometimes, it's broken
- **CHECK**: Tests are independent and can run in any order
- **REJECT**: Commented-out tests
- **REJECT**: Tests using `time.sleep` or arbitrary waits
- **REJECT**: "Sometimes fails" tests — fix them or delete them

---

## 9. CODE QUALITY & MAINTAINABILITY

### 9.1 Naming Conventions
- **RULE**: Clear, consistent naming
- **CHECK**: Routers (modules): `documents_router`, `audit_router`
- **CHECK**: Services: `DocumentService`, `EvaluatorOrchestrator`, `AuditLogService`
- **CHECK**: Repositories: `DocumentRepository`, `FlagRepository`, `AuditLogRepository`
- **CHECK**: Pydantic schemas: `DocumentCreate`, `DocumentUpdate`, `DocumentResponse`, `FlagResponse`
- **CHECK**: ORM models: `Document`, `Flag`, `Firm`, `User`, `ApiKey`, `AuditLog`, `Export`, `ReviewerAction`
- **CHECK**: Protocols/ABCs: `IDocumentRepository`, `IEvaluator`, `ICourtListenerClient`
- **CHECK**: Methods: `get_document_by_id`, `create_document`, `soft_delete_document`
- **CHECK**: Boolean methods/properties: `is_active`, `has_permission`, `can_export`
- **CHECK**: snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for constants
- **REJECT**: Abbreviations (`doc`, `usr`, `flg`)
- **REJECT**: Generic names (`data`, `info`, `temp`, `helper`, `utils.py` with 2000 lines)
- **REJECT**: Inconsistent naming across similar classes

### 9.2 Function/Method Design
- **RULE**: Small, focused functions
- **CHECK**: Max 30 lines per function (usually much shorter)
- **CHECK**: Max 4 parameters; use a Pydantic model or dataclass for more
- **CHECK**: Single responsibility per function
- **CHECK**: Pure functions where possible (no hidden side effects)
- **CHECK**: Early returns to reduce nesting
- **REJECT**: Functions with 5+ positional parameters
- **REJECT**: Functions doing multiple unrelated things
- **REJECT**: Nesting >3 levels deep

### 9.3 Comments & Documentation
- **RULE**: Self-documenting code with strategic comments
- **CHECK**: Docstrings on all public functions/classes (Google or reST style, consistent project-wide)
- **CHECK**: Explain "why", not "what"
- **CHECK**: Document non-obvious algorithms (hash chain construction, citation parsing edge cases)
- **CHECK**: Provide `Examples:` in docstrings for complex APIs
- **CHECK**: Keep comments in sync with code
- **REJECT**: Obvious comments (`# increment counter`)
- **REJECT**: Large commented-out blocks
- **REJECT**: Outdated comments
- **REJECT**: `TODO` without a ticket reference (`# TODO(CG-123): ...`)

### 9.4 Python / Type-Hint Best Practices
- **RULE**: Leverage Python's type system
- **CHECK**: Strict type checking enabled (`mypy --strict` or `pyright` in strict mode) in CI
- **CHECK**: No `Any` (use `object` or a real type)
- **CHECK**: Use `Protocol` / ABC for interfaces
- **CHECK**: Use `TypeAlias` for complex types
- **CHECK**: Use `Enum` / `StrEnum` for fixed value sets
- **CHECK**: Use generics (`Generic[T]`, `TypeVar`) for reusable components
- **CHECK**: Explicit `Optional[T]` / `T | None` handling — no implicit `None` returns
- **REJECT**: `Any` used to bypass type errors
- **REJECT**: `# type: ignore` without a linked ticket and a comment explaining why
- **REJECT**: Over-using `cast()` to suppress real type issues

### 9.5 File Organization
- **RULE**: Logical, consistent structure
- **CHECK**: Feature-based package structure
- **CHECK**: One primary class per file (small helpers colocated acceptable)
- **CHECK**: File names snake_case, matching class names where applicable (`document_service.py` contains `DocumentService`)
- **CHECK**: `__init__.py` exports public API of a package
- **CHECK**: Max 300 lines per file — split if larger
- **STRUCTURE**:
  ```
  app/
    ├── main.py                    # FastAPI app instance + lifespan
    ├── common/
    │   ├── dependencies.py        # get_db, get_current_user, etc.
    │   ├── exceptions.py          # CiteGuardException + subclasses
    │   ├── middleware.py          # request_id, logging, CORS wrappers
    │   ├── pagination.py          # PaginatedResponse generic
    │   └── utils/
    ├── config.py                  # pydantic-settings
    ├── db/
    │   ├── base.py                # Declarative base
    │   ├── session.py             # async engine + session factory
    │   └── migrations/            # Alembic
    ├── documents/
    │   ├── __init__.py
    │   ├── routes.py              # APIRouter
    │   ├── service.py             # DocumentService
    │   ├── repository.py          # DocumentRepository
    │   ├── schemas.py             # Pydantic models
    │   ├── models.py              # SQLAlchemy ORM
    │   └── tests/
    ├── evaluators/
    │   ├── __init__.py
    │   ├── base.py                # IEvaluator, BaseEvaluator
    │   ├── orchestrator.py        # EvaluatorOrchestrator
    │   ├── citation_existence.py
    │   ├── quote_verification.py
    │   ├── bluebook_format.py
    │   ├── judge_verification.py
    │   ├── temporal_validity.py
    │   └── tests/
    ├── audit/
    │   ├── routes.py
    │   ├── service.py             # Audit log write + hash chain
    │   ├── repository.py
    │   ├── exporter.py            # PDF export via WeasyPrint (Arq job)
    │   ├── schemas.py
    │   ├── models.py
    │   └── tests/
    ├── flags/
    ├── firms/
    ├── users/
    ├── api_keys/
    ├── integrations/
    │   ├── courtlistener/
    │   ├── fjc/                   # Federal Judicial Center directory
    │   ├── clerk/
    │   └── stripe/
    └── workers/
        ├── __init__.py
        ├── arq_app.py             # Arq worker definition
        └── tasks/                 # evaluator_run, pdf_export, email_send
  ```
- **REJECT**: Mixing routers and services in the same file
- **REJECT**: Deeply nested directory structures (>4 levels)

---

## 10. SPECIFIC PROJECT RULES (CiteGuard)

### 10.1 Document Ingestion & LLM Proxy
- **RULE**: Robust, idempotent submission
- **CHECK**: Both the direct SDK path (`POST /v1/documents`) and the LLM proxy path (`POST /v1/llm/proxy`) route through a single `DocumentIngestionService`
- **CHECK**: Every submission accepts an `Idempotency-Key` header; duplicate key within 24h returns the original response
- **CHECK**: Document text size capped at 200KB; reject with 413 above that
- **CHECK**: Validate `document_type` (`brief`, `memo`, `contract`, `other`)
- **CHECK**: Ingestion enqueues an Arq job for evaluation; returns `202 Accepted` with `document_id`
- **CHECK**: Proxy path forwards to upstream LLM provider (Anthropic, OpenAI) and captures both request and response
- **CHECK**: All submissions write an `audit_log` entry (`event_type='document_submitted'`) in the same transaction as the `Document` insert
- **REJECT**: Synchronous evaluator execution in the request handler
- **REJECT**: Silent truncation of large documents
- **REJECT**: Accepting submissions without `firm_id` (derived from authenticated API key)

### 10.2 Evaluator System
- **RULE**: Safe, extensible, reproducible verification
- **CHECK**: Every evaluator implements `IEvaluator` with `async def evaluate(document: Document) -> list[Flag]`
- **CHECK**: Every evaluator has a stable `evaluator_id` and a `version` string (semver). The `Flag` records both.
- **CHECK**: Evaluators are idempotent — given the same document text + evaluator version, produce the same flags
- **CHECK**: Evaluators are isolated — they never read or write entities other than accepting input and returning `Flag` objects
- **CHECK**: `EvaluatorOrchestrator` runs evaluators in parallel via `asyncio.gather`, bounded by a concurrency limit
- **CHECK**: Evaluator failures are captured as system flags (severity `ADVISORY`, code `CG_E_EVALUATOR_TIMEOUT`) — do NOT fail the whole verification
- **CHECK**: Each flag includes: `evaluator_id`, `evaluator_version`, `severity`, `explanation`, `confidence` (0–1), `start_offset`, `end_offset`, `suggested_correction` (nullable), `raw_evaluator_output` (JSONB)
- **CHECK**: External API dependencies (CourtListener, FJC) are called via injected clients with retry + circuit breaker
- **CHECK**: The LLM-as-judge evaluator (post-V1) NEVER sends document content to a model that could use it for training; send only to configured provider with opt-out headers
- **REJECT**: Evaluators that write to the database directly
- **REJECT**: Evaluators with side effects on other evaluators
- **REJECT**: Evaluators that modify input documents
- **REJECT**: Evaluator behavior that varies between runs on the same input + version
- **MANDATE**: When an evaluator's logic materially changes, bump its version. A version bump triggers re-evaluation of affected documents on demand.

### 10.3 Audit Log Integrity (CRITICAL)
- **RULE**: The audit log is append-only and tamper-evident
- **CHECK**: `audit_log` table has no UPDATE or DELETE grants to the application role (enforced in migration)
- **CHECK**: Every row computes `this_hash = sha256(prior_hash || canonical_json(payload))`
- **CHECK**: Canonical JSON serialization is deterministic (sorted keys, stable numeric formatting, UTF-8 NFC)
- **CHECK**: Genesis row per firm: `prior_hash = sha256("")`, `event_type = 'firm_genesis'`
- **CHECK**: A background job verifies the chain for every firm daily; alert on divergence
- **CHECK**: Every significant event writes an audit entry: document submission, flag creation, reviewer action, finalize, export, API key creation, role change
- **CHECK**: Audit writes are part of the same DB transaction as the action they record — if the action commits, the audit row commits
- **CHECK**: Audit row IDs are ULIDs (time-sortable) so chain traversal is efficient
- **REJECT**: Any code path that writes to `audit_log` outside the `AuditLogService`
- **REJECT**: Any attempt to update or soft-delete an audit row
- **REJECT**: Deferring audit writes to a background job (must be synchronous with the action)
- **REJECT**: Storing sensitive raw content (document text, prompt) in audit payload — store references + hashes
- **MANDATE**: `AuditLogService.append(event)` is the ONLY way audit rows are created, and it is invoked within the action's transaction

### 10.4 Review Queue & Workflow
- **RULE**: Fast, accurate review flow
- **CHECK**: Queue default sort: severity DESC, then submitted_at ASC
- **CHECK**: Reviewer actions: `APPROVE`, `OVERRIDE`, `REJECT`, `DEFER` — `OVERRIDE` requires a `reason` field (min 10 chars)
- **CHECK**: Every reviewer action writes an audit log entry (`event_type='flag_reviewed'`)
- **CHECK**: A document cannot be `FINALIZED` until every flag has a reviewer action
- **CHECK**: Finalize triggers the audit export job
- **CHECK**: Reviewer throughput is instrumented (actions per minute) — visible to firm admins
- **CHECK**: A `REJECT` action is treated as signal for evaluator tuning (no change to product behavior, but logged for analysis)
- **REJECT**: Allowing finalize with pending flags
- **REJECT**: Allowing a reviewer to act on their own submissions (conflict of interest) — configurable per firm but default-deny
- **REJECT**: Silent mutation of flags after creation (actions live on `reviewer_actions`, flags themselves are immutable)

### 10.5 Firm, User & Multi-Tenancy
- **RULE**: Tenant isolation is non-negotiable
- **CHECK**: Every tenant-scoped ORM model has `firm_id` column and an index on it
- **CHECK**: `BaseRepository` requires `firm_id` on every list/get method
- **CHECK**: A request is always scoped to a single firm (derived from API key or authenticated user)
- **CHECK**: Cross-firm queries are forbidden in application code; admin-only analytics run in a separate service with explicit audit
- **CHECK**: User roles: `ADMIN`, `REVIEWER`, `SUBMITTER` — enforced via role dependency
- **CHECK**: Self-deletion prevented (users cannot delete themselves; admins can, but not the last admin of a firm)
- **CHECK**: Soft delete for users; never hard-delete (historical actions must remain attributable)
- **CHECK**: Role changes audited
- **REJECT**: Any query missing a `firm_id` filter on tenant-scoped tables
- **REJECT**: Hard-deleting users
- **REJECT**: Allowing users to change their own role
- **MANDATE**: A CI lint rule greps repositories for queries missing a `firm_id` filter

### 10.6 Privileged Data Handling
- **RULE**: Treat every document as privileged attorney-client material
- **CHECK**: Document text encrypted at rest (managed Postgres encryption); ClickHouse traces never store raw text
- **CHECK**: Logs, traces, and error reports (Sentry) scrub document content via explicit allowlist
- **CHECK**: External services (CourtListener, FJC) receive only the minimum needed (citation strings, quoted passages) — never full documents
- **CHECK**: Customer data stays within US AWS regions (no cross-region replication without explicit contract)
- **CHECK**: Sub-processor list maintained; changes require customer notification
- **CHECK**: Retention default 90 days; firm-configurable up to 7 years
- **CHECK**: Hard-delete requests honored within 30 days (excluding audit log retention)
- **CHECK**: No customer document text is ever sent to a third-party for model training
- **REJECT**: Logging, caching, or persisting document content outside the primary encrypted store
- **REJECT**: Sending full document text to any third party
- **REJECT**: Storing customer data outside the US (V1)
- **MANDATE**: A pre-commit scan checks for accidental logging of `document.text`, `prompt`, or `completion`

---

## 11. API DESIGN STANDARDS

### 11.1 RESTful Conventions
- **RULE**: Follow REST principles
- **CHECK**: Proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **CHECK**: Plural nouns for resources (`/documents`, `/flags`, `/firms`, `/audit-log`)
- **CHECK**: Nested routes for relationships (`/documents/{id}/flags`, `/flags/{id}/actions`)
- **CHECK**: Query params for filtering, sorting, pagination
- **CHECK**: Proper status codes:
  - 200: Success
  - 201: Created
  - 202: Accepted (async evaluator submission)
  - 204: No Content
  - 400: Bad Request
  - 401: Unauthorized
  - 403: Forbidden
  - 404: Not Found
  - 409: Conflict (idempotency violation, state conflict)
  - 413: Payload Too Large
  - 422: Validation Error (Pydantic)
  - 429: Too Many Requests
  - 500: Internal Server Error
- **REJECT**: POST for read operations
- **REJECT**: GET for state-changing operations
- **REJECT**: Verbs in URLs (`/getDocuments`, `/runEvaluator`)

### 11.2 Request/Response Format
- **RULE**: Consistent API contract
- **CHECK**: `Content-Type: application/json` enforced
- **CHECK**: All responses JSON
- **CHECK**: List endpoints use a consistent envelope with `items`, `total`, `page`, `page_size`, `has_next`
- **CHECK**: Dates in ISO 8601 with timezone (`2026-04-18T12:34:56Z`)
- **CHECK**: snake_case for JSON keys (Python convention; document this in API docs)
- **REJECT**: Mixed response shapes across endpoints
- **REJECT**: Different structures for success vs. error
- **REJECT**: Inconsistent date formats

### 11.3 Pagination
- **RULE**: Paginate all list endpoints
- **CHECK**: Default page size: 20
- **CHECK**: Max page size: 100
- **CHECK**: Support both offset (`page`, `page_size`) and cursor (`after`, `limit`) pagination — cursor is mandatory for `audit_log` and `flags`
- **CHECK**: Pagination metadata included (`total`, `has_next`, `has_previous`, `next_cursor`)
- **REJECT**: Unbounded list endpoints
- **REJECT**: No max cap on `page_size`
- **REJECT**: Missing total count on offset pagination

### 11.4 Filtering & Sorting
- **RULE**: Flexible data retrieval
- **CHECK**: Filtering via query params (`?status=pending&severity=critical`)
- **CHECK**: Sort params validated against an allowlist (`sort_by=created_at&order=desc`)
- **CHECK**: Search across specific fields only (never raw text search on document bodies via the public API)
- **CHECK**: All filter values validated by Pydantic
- **REJECT**: Sort by arbitrary fields (validate against an allowlist)
- **REJECT**: SQL injection vectors via filter params
- **REJECT**: No search or filter on list endpoints where obviously needed

### 11.5 Versioning
- **RULE**: API versioning strategy
- **CHECK**: URL versioning (`/v1/...`)
- **CHECK**: Every route lives under a version prefix
- **CHECK**: Backwards compatibility within a major version
- **CHECK**: Document breaking changes in `CHANGELOG.md`; bump major version if breaking
- **REJECT**: Unversioned public routes
- **REJECT**: Breaking changes within the same version

---

## 12. ENVIRONMENT & CONFIGURATION

### 12.1 Environment Variables
- **RULE**: Externalize all configuration
- **CHECK**: All secrets in environment variables, never committed
- **CHECK**: `.env.local` for local development; `.env` never committed
- **CHECK**: `pydantic-settings` validates all env vars on startup — app refuses to boot on missing required vars
- **CHECK**: Typed settings object (`Settings`) injected via `Depends(get_settings)` (cached via `lru_cache`)
- **CHECK**: Required envs for V1: `DATABASE_URL`, `REDIS_URL`, `CLICKHOUSE_URL`, `CLERK_SECRET_KEY`, `COURTLISTENER_API_TOKEN`, `STRIPE_SECRET_KEY`, `SENTRY_DSN`, `APP_ENV`, `LOG_LEVEL`
- **REJECT**: Hardcoded secrets or URLs
- **REJECT**: Committing `.env` files
- **REJECT**: Missing required env vars silently defaulting
- **MANDATE**: Maintain `.env.example` with every required variable documented

### 12.2 Configuration Management
- **RULE**: Centralized configuration
- **CHECK**: One `Settings` class per environment concern, composed in `config.py`
- **CHECK**: Configuration grouped by feature (`DbSettings`, `AuthSettings`, `CourtListenerSettings`)
- **CHECK**: Validation schema with explicit bounds (e.g., `pool_size: int = Field(ge=1, le=50)`)
- **CHECK**: Sensible defaults only for non-critical values
- **REJECT**: Configuration scattered across modules
- **REJECT**: Magic numbers / strings instead of configured values

---

## 13. DEVELOPMENT WORKFLOW

### 13.1 Feature Implementation Process
- **RULE**: Follow structured development workflow
- **STEP 1**: Understand Requirements
  - Read feature specifications (V1 PRD, this document)
  - Review API contracts and data models
  - Clarify ambiguities with PM/Frontend team
  - Identify dependencies (schema changes, external services, evaluators)
- **STEP 2**: Plan Implementation
  - Design database schema changes (if needed)
  - Plan package structure and service boundaries
  - Identify reusable components and services
  - Design endpoints and Pydantic schemas
  - Estimate effort and timeline
- **STEP 3**: Database Design (if needed)
  - Sketch SQLAlchemy models
  - Plan Alembic migration strategy
  - Review with team before generating migration
  - Test migration locally against a production-shaped snapshot
- **STEP 4**: Setup & Scaffolding
  - Create feature branch from main
  - Create package structure (routes, service, repository, schemas, models)
  - Create Pydantic schemas
  - Create unit test modules
- **STEP 5**: Implementation
  - Implement repository layer
  - Implement service layer
  - Implement router layer
  - Add auth dependencies and role checks
  - Implement error handling
  - Add structured logging
- **STEP 6**: Testing
  - Unit tests for service and evaluator logic
  - Integration tests for API endpoints
  - Edge cases and error scenarios
  - Tenant isolation tests (critical)
  - Manual testing with httpie / Bruno
  - Frontend integration smoke test
- **STEP 7**: Documentation
  - Add route tags, `response_model`, `status_code` for OpenAPI
  - Docstrings on services and complex functions
  - Update `CHANGELOG.md`
  - Document breaking changes clearly
- **STEP 8**: Code Review
  - Self-review against this checklist
  - Request peer review
  - Address feedback promptly
- **STEP 9**: Deployment
  - All CI checks green (mypy, ruff, pytest, coverage)
  - Run migrations in staging
  - Test in staging with evaluator corpus
  - Deploy to production
  - Monitor Sentry + metrics for 24h

### 13.2 Git Workflow
- **RULE**: Clean, atomic commits
- **CHECK**: Branch naming: `feature/CG-XXX-short-description` or `fix/CG-XXX-bug-description`
- **CHECK**: Commit messages: `type(scope): description`
  - Types: feat, fix, refactor, test, docs, chore
  - Example: `feat(evaluators): add citation existence evaluator`
- **CHECK**: Small, focused commits
- **CHECK**: Keep branches current with main
- **CHECK**: Rebase before merge (per team policy)
- **REJECT**: Committing `.venv`, `.env`, `__pycache__`, or any generated files
- **REJECT**: Large mixed-concern commits
- **REJECT**: Vague commit messages ("fix", "updates", "WIP")
- **REJECT**: Commented-out code in commits

### 13.3 Pull Request Guidelines
- **RULE**: High-quality PRs for easy review
- **CHECK**: PR title: `[CG-XXX] Clear description`
- **CHECK**: Description includes:
  - **What**: What changed
  - **Why**: Why it was needed (link to ticket)
  - **How**: How it was implemented
  - **Database Changes**: Schema changes, migrations, index additions
  - **API Changes**: New/modified endpoints, schema changes
  - **Testing**: Unit, integration, manual testing summary
  - **Evaluator Corpus Impact**: Changes to accuracy metrics (if evaluator modified)
  - **Breaking Changes**: Highlight explicitly
- **CHECK**: Link to ticket and any related design docs
- **CHECK**: Self-review completed
- **CHECK**: CI green (mypy, ruff, pytest, coverage ≥80%)
- **CHECK**: No merge conflicts
- **CHECK**: Migrations reviewed and tested
- **REJECT**: PRs with 1500+ line diffs (split)
- **REJECT**: PRs without description
- **REJECT**: Failing CI
- **REJECT**: New code without tests

### 13.4 Database Migration Workflow
- **RULE**: Safe, reviewable migrations
- **CHECK**: Review generated Alembic SQL before committing
- **CHECK**: Test migration locally on a production-shaped DB snapshot
- **CHECK**: Both `upgrade()` and `downgrade()` implemented and tested
- **CHECK**: Data migrations separate from schema migrations (two steps)
- **CHECK**: Long-running index creation uses `CREATE INDEX CONCURRENTLY` in a follow-up script
- **CHECK**: Migration notes in PR description
- **REJECT**: Auto-generated migrations committed without review
- **REJECT**: Destructive migrations without a two-phase deploy
- **REJECT**: Migrations >1 minute on production-sized data
- **REJECT**: Migrations that grant UPDATE/DELETE on `audit_log`

---

## 14. CODE REVIEW CHECKLIST

### Before Submitting PR or Approving Code, Verify:

#### ✅ SOLID Principles
- [ ] Single Responsibility: Each class has one reason to change
- [ ] Open/Closed: Extended through interfaces, not modification
- [ ] Liskov Substitution: Subtypes are substitutable
- [ ] Interface Segregation: Small, focused interfaces (Protocols/ABCs)
- [ ] Dependency Inversion: Depends on abstractions

#### ✅ Code Duplication
- [ ] No duplicated logic (DRY principle)
- [ ] Common code extracted to utilities/services
- [ ] Generic solutions used where appropriate
- [ ] No magic numbers or strings

#### ✅ Performance
- [ ] Database queries optimized
- [ ] Pagination implemented
- [ ] No N+1 query patterns
- [ ] Async operations used correctly
- [ ] Memory usage bounded
- [ ] Indexes defined for new query patterns

#### ✅ Architecture
- [ ] Follows FastAPI best practices
- [ ] Proper package organization
- [ ] Repository pattern used
- [ ] Pydantic schemas for all inputs/outputs
- [ ] Proper use of dependencies / middleware / exception handlers

#### ✅ SQLAlchemy & Alembic
- [ ] Schema properly designed
- [ ] Migrations reviewed (up and down)
- [ ] Transactions used where needed
- [ ] Queries are type-safe (no `Any`)
- [ ] Soft deletes implemented
- [ ] All queries scoped by `firm_id`

#### ✅ Security
- [ ] Input validation on all endpoints (Pydantic)
- [ ] Authentication/authorization enforced
- [ ] No SQL injection vectors
- [ ] No sensitive data leakage
- [ ] Sensitive data protected
- [ ] Rate limiting on sensitive endpoints

#### ✅ Error Handling
- [ ] Custom exceptions used
- [ ] Consistent error responses via global handler
- [ ] Meaningful error codes + messages
- [ ] Errors logged with context (but never document content)

#### ✅ Testing
- [ ] Unit tests for services/evaluators
- [ ] Integration tests for routes
- [ ] Edge cases covered
- [ ] Tenant isolation tested
- [ ] CI green, coverage ≥80%

#### ✅ Code Quality
- [ ] Naming conventions followed
- [ ] Functions small and focused
- [ ] Strict typing (no `Any`, no unexplained `type: ignore`)
- [ ] Readable and maintainable
- [ ] Comments explain "why"

#### ✅ Documentation
- [ ] Docstrings on public functions/classes
- [ ] OpenAPI tags / response_models set
- [ ] README / CHANGELOG updated as needed
- [ ] Complex logic documented

#### ✅ CiteGuard-Specific
- [ ] Audit log entries written for the action
- [ ] No document content in logs/traces/errors
- [ ] Hash chain not disturbed
- [ ] Evaluator version bumped if logic changed
- [ ] `firm_id` filter present on every query

---

## 15. REJECTION CRITERIA (Development & Code Review)

### 🚫 Immediate Rejection/Rework Required

1. **Security Issues**
   - SQL injection vectors (raw string SQL)
   - Sensitive data leakage (document text in logs, errors, traces)
   - Exposed secrets or credentials
   - Missing authentication on protected routes
   - API keys / passwords stored in plaintext

2. **Critical Bugs**
   - Un-awaited coroutines
   - Unhandled async exceptions
   - Memory leaks (un-closed clients, un-cancelled tasks)
   - Database connection leaks
   - Race conditions in audit or evaluator paths

3. **SOLID Violations**
   - Business logic in routers
   - Direct `AsyncSession` usage in services (skip repository)
   - Multiple responsibilities in one class
   - God classes (>500 lines)

4. **Code Duplication**
   - Copy-pasted code blocks
   - Repeated logic across services
   - Duplicated validation

5. **Performance Issues**
   - Fetching all records without pagination
   - N+1 query patterns
   - Sync blocking calls in async code
   - Loading large payloads fully into memory

6. **Poor Practices**
   - `Any` used to avoid proper typing
   - `print()` in application code
   - Commented-out code blocks (>10 lines)
   - Missing error handling
   - No tests for new code

7. **Architecture Violations**
   - Circular imports
   - Tight coupling between feature packages
   - Missing repository pattern
   - Returning ORM entities directly from routes

8. **CiteGuard-Specific Violations**
   - Writing to `audit_log` outside `AuditLogService`
   - Missing `firm_id` filter on tenant-scoped queries
   - Logging document content or prompts
   - Sending document content to third parties beyond the declared LLM provider
   - Updating or deleting audit rows
   - Evaluator logic change without version bump
   - Storing or processing customer data outside US regions

---

## 16. COLLABORATION & COMMUNICATION

### 16.1 Code Review Feedback Guidelines

#### When Providing Code Review Feedback:

#### 🎯 Be Specific & Actionable
- ❌ BAD: "This code has performance issues"
- ✅ GOOD: "This query fetches all documents without pagination. Use `.limit(20).offset(...)` or switch to cursor pagination via `after=<ulid>`."

#### 🎯 Explain the Principle
- ❌ BAD: "Move this code"
- ✅ GOOD: "This business logic in the router violates Single Responsibility. Move it to `DocumentService.validate_submission()` and keep the route as a thin dispatcher."

#### 🎯 Provide Solutions
- ❌ BAD: "This won't scale"
- ✅ GOOD: "Evaluators run sequentially here, which will blow p95 latency past our 3s budget. Wrap them in `asyncio.gather(*(ev.evaluate(doc) for ev in evaluators))`."

#### 🎯 Reference Standards
- ❌ BAD: "Use a different pattern"
- ✅ GOOD: "Apply the Repository pattern per §4.4. See `DocumentRepository` for a reference implementation."

#### 🎯 Prioritize Issues
1. **P0 - Critical**: Security, data loss, audit integrity, production crashes
2. **P1 - High**: SOLID violations, performance issues, tenant isolation gaps
3. **P2 - Medium**: Duplication, missing tests, maintainability
4. **P3 - Low**: Naming, formatting, minor optimizations

### 16.2 Working with Frontend Developers
- **RULE**: Seamless backend-frontend collaboration
- **CHECK**: Publish the OpenAPI schema per PR (via CI artifact) so frontend can diff
- **CHECK**: Define API contracts before implementation
- **CHECK**: Communicate API changes early
- **CHECK**: Include example requests/responses in route docstrings (renders into OpenAPI)
- **CHECK**: Stable error codes so the frontend can branch on them
- **CHECK**: Version the API; don't introduce breaking changes silently
- **CHECK**: Test endpoints with Bruno/Postman before marking the ticket complete
- **REJECT**: Changing API contracts without notice
- **REJECT**: Vague error messages
- **REJECT**: Undocumented endpoints
- **REJECT**: Shipping without a frontend-integration smoke test

### 16.3 Working with Database/DevOps Teams
- **RULE**: Coordinate on infrastructure and data
- **CHECK**: Review schema changes with DBA before merging
- **CHECK**: Communicate performance requirements
- **CHECK**: Document index requirements in migration PRs
- **CHECK**: Provide migration rollback plan
- **CHECK**: Coordinate deployment timing
- **CHECK**: Share logging/monitoring requirements
- **REJECT**: Surprise migrations in production
- **REJECT**: Ignoring backup/restore procedures
- **REJECT**: Missing index requirements

### 16.4 Working with Product Managers
- **RULE**: Clear communication on requirements and feasibility
- **CHECK**: Clarify acceptance criteria before starting
- **CHECK**: Communicate technical constraints early (evaluator latency budgets, CourtListener rate limits)
- **CHECK**: Provide realistic estimates including testing time
- **CHECK**: Update on progress regularly
- **CHECK**: Explain trade-offs clearly (e.g., accuracy vs. latency in an evaluator)
- **CHECK**: Suggest alternatives when beneficial
- **REJECT**: Accepting unclear requirements
- **REJECT**: Missing deadlines without communication
- **REJECT**: Implementing features differently than spec without sign-off
- **REJECT**: Not raising feasibility concerns early

### 16.5 API Design Collaboration
- **RULE**: Collaborative API design
- **CHECK**: Review API design with frontend before implementation
- **CHECK**: Align on response shapes, pagination, error codes
- **CHECK**: Agree on auth/authz strategy
- **CHECK**: Frontend use cases drive response fields, not backend convenience
- **REJECT**: Designing APIs in isolation
- **REJECT**: Ignoring frontend ergonomics
- **REJECT**: Over-nested or overly generic responses

### 16.6 Daily Development Practices
- **RULE**: Be a productive team member
- **CHECK**: Attend standups prepared
- **CHECK**: Update ticket status regularly (Linear/Jira)
- **CHECK**: Unblock teammates when possible
- **CHECK**: Share knowledge and gotchas (especially around evaluators and audit chain)
- **CHECK**: Document nontrivial decisions as ADRs in `docs/adr/`
- **CHECK**: Ask for help when stuck (timebox investigations to 2 hours)
- **CHECK**: Respond to code review requests promptly
- **REJECT**: Working in isolation without communication
- **REJECT**: Hoarding knowledge
- **REJECT**: Not asking for help when blocked
- **REJECT**: Letting reviews languish

---

## 🎓 DEVELOPER MINDSET

### When Building Features:
**Build with reliability in mind.**
- Focus on creating robust, fault-tolerant APIs
- Consider error scenarios and edge cases (especially evaluator failures and CourtListener outages)
- Implement proper validation and error handling
- Think about data consistency and transactions
- Plan for scalability from the start

**Build with the team in mind.**
- Write self-documenting code
- Follow established patterns and conventions
- Create reusable services and utilities
- Add meaningful comments for complex logic (hash chain, citation parsing)
- Make code easy to review and maintain
- Document API contracts clearly

**Build with security in mind.**
- Validate all inputs
- Enforce authentication and tenant isolation
- Protect privileged legal data
- Follow security best practices
- Think like an attacker (what could go wrong?)

**Build with performance in mind.**
- Optimize database queries and external API calls
- Paginate everything
- Cache strategically (court data, judge directory)
- Monitor response times
- Respect the evaluator latency budget (p95 <3s)

### When Reviewing Code:
**Only change what is explicitly requested.**

Resist the temptation to "improve" code that wasn't part of the request. Every unnecessary change increases bug risk and makes reviews harder.

**When in doubt:**
- ❓ Ask for clarification from PM/Frontend/DevOps
- 📖 Read existing code for established patterns
- 🔍 Search the codebase for similar implementations
- 💬 Discuss with team in standup or Slack
- 📚 Refer to this doc, the V1 PRD, and the ADR log
- 🚫 Don't assume or guess

### Time Management
- **Break down large features** into smaller, manageable tasks
- **Set realistic estimates** considering complexity, unknowns, and testing
- **Communicate delays early** as soon as you foresee them
- **Timebox investigations** (max 2 hours before asking for help)
- **Balance speed and quality** (fast but broken is worse than slower but solid)
- **Plan for testing time** (coding is ~50% of the work)

### Problem-Solving Approach
1. **Understand the problem thoroughly** before coding
2. **Research existing solutions** in the codebase
3. **Design the solution** (schema, services, APIs)
4. **Implement incrementally** (test as you go)
5. **Test comprehensively** (unit, integration, tenant isolation, evaluator corpus if applicable)
6. **Document clearly** (docstrings, OpenAPI, ADR)
7. **Review critically** (self-review before PR)

---

## FINAL NOTE

These guidelines ensure you build high-quality, maintainable, secure, and performant backend systems for CiteGuard. By following these standards, you will:

✅ **Deliver Features Faster**: Reusable patterns and clear architecture speed up development
✅ **Reduce Bugs**: Comprehensive testing and validation catch issues early
✅ **Improve Security**: Protecting privileged legal data is our core value proposition
✅ **Enhance Performance**: Optimized queries and caching provide fast evaluator runs
✅ **Make Maintenance Easier**: Clean code and documentation help future you and your team
✅ **Build Trust**: Consistent quality and an unbroken audit chain build confidence with law firm buyers

**Remember**: Great backend development is not just about writing code that works — it's about creating robust, secure, and auditable systems that keep our customers out of trouble. At CiteGuard, "works in dev" is not the bar. The bar is "survives scrutiny from a malpractice carrier, a judge, and a SOC 2 auditor."

### Key Principles to Internalize:
1. **SOLID principles** are mandatory, not optional — they guide every architectural decision
2. **Zero code duplication** through proper abstraction and reusability
3. **Performance** is considered from day one, not added later
4. **Security** is paramount — never compromise on security for speed
5. **Tenant isolation** is sacred — no cross-firm data access, ever
6. **Audit integrity** is non-negotiable — the hash chain cannot break
7. **Privileged data** never leaves approved boundaries (no logs, no errors, no third parties)
8. **Testing** gives confidence — untested code is broken code
9. **Documentation** saves time — document as you build, not after
10. **Communication** keeps the team aligned and productive

### Backend Developer's Creed:
- I write **secure code** that protects privileged legal data
- I write **performant code** that scales with customer growth
- I write **tested code** that behaves correctly under adversarial input
- I write **maintainable code** that others can understand
- I write **documented APIs** that frontends can integrate with confidence
- I write **audit-respecting code** that never breaks the chain
- I **communicate proactively** to keep the team aligned
- I **review code thoughtfully** to help the team improve
- I **continuously learn** to become a better developer

---

**Welcome to the CiteGuard Backend Team! Let's build something that judges, malpractice carriers, and auditors all trust.** 🚀