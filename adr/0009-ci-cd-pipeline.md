# Architecture Decision Record (ADR)

**Status: Accepted**

## ADR-0009: CI/CD Pipeline

### Decision

We have decided to use GitHub Actions for CI/CD with separate pipelines for backend (Python) and frontend (Next.js). Backend deploys to Fly.io, frontend deploys to Vercel. All PRs must pass type checking, linting, tests, and coverage checks before merge.

### Context

CiteGuard needs automated quality gates to prevent regressions in evaluator accuracy, audit log integrity, tenant isolation, and privileged data protection. A solo founder needs CI/CD to enforce standards that would normally require a team of reviewers.

- CiteGuard has critical invariants (privilege protection, tenant isolation, audit log integrity) that must be verified on every code change.
- Manual code review alone is insufficient for a solo founder — automated checks are the primary quality gate.
- Backend (Python/FastAPI) and frontend (Next.js/TypeScript) have different toolchains and deployment targets.
- Evaluator changes require corpus regression testing to prevent accuracy degradation.
- Database migrations must be reversible to enable safe rollbacks.
- Staging environments on every PR enable manual verification before merge.

### Rationale

#### GitHub Actions as CI Platform
- GitHub Actions is the standard CI platform for GitHub-hosted repositories, requiring no additional service integration.
- Native integration with PR checks, status gates, and branch protection rules.
- Generous free-tier minutes for open-source and small private repos.
- Large marketplace of reusable actions for common tasks (Python setup, Node.js setup, Docker caching).

#### Separate Pipelines for Backend and Frontend
- Backend and frontend have independent dependency trees, test suites, and deployment targets.
- Separate pipelines allow independent deployment: a frontend-only change does not trigger backend tests and vice versa.
- Path-based triggering (`paths: ['backend/**']`, `paths: ['frontend/**']`) reduces CI minutes and feedback time.

#### Fly.io for Backend, Vercel for Frontend
- Fly.io provides container-based deployment with built-in TLS, auto-scaling, and proximity to US regions (matching data residency requirements from ADR-0007).
- Vercel provides zero-config Next.js deployment with edge CDN, preview deployments on every PR, and automatic HTTPS.
- Both platforms support preview/staging environments tied to PR branches.

### Implementation Details

#### Backend CI (`.github/workflows/backend.yml`)
- **Python Version**: 3.12
- **Dependency Installation**: `pip install` from `pyproject.toml` with pip cache
- **Type Checking**: `mypy --strict` — zero tolerance for type errors
- **Linting**: `ruff check` + `ruff format --check` — enforces consistent code style
- **Unit and Integration Tests**: `pytest` with coverage reporting
  - Coverage target: 80%+ overall
  - Coverage target: 100% on `AuditLogService` and `BaseRepository`
- **Tenant Isolation Tests**: Dedicated `@pytest.mark.tenant_isolation` marker; these tests run as a separate step with explicit pass/fail reporting
- **Privilege Leak Grep**: CI step that greps for patterns matching document content in logs (e.g., `logger.info(document.text)`, `print(doc.content)`). Fails the build on any match.
- **Evaluator Corpus Regression**: On PRs touching `app/evaluators/`, runs the evaluator against the fixture corpus (50 seeded hallucinations + 50 clean docs). Compares accuracy against baseline. Fails if accuracy drops without explicit sign-off.

#### Frontend CI (`.github/workflows/frontend.yml`)
- **Node.js Version**: 20
- **Package Manager**: pnpm
- **Type Checking**: `tsc --noEmit` — strict TypeScript, no implicit any
- **Linting**: ESLint with custom `no-privileged-console-log` rule (see ADR-0007)
- **Unit Tests**: Vitest with coverage reporting
  - Coverage target: 70%+
- **E2E Tests**: Playwright with headless Chrome
  - Tests cover critical user flows: login, document upload, review dashboard, audit log view
  - Tests verify no document content in URLs, page titles, or localStorage

#### Deployment

##### Backend (Fly.io)
- **Trigger**: Auto-deploy on merge to `main` branch.
- **Process**: Build Docker image, run Alembic migrations (`alembic upgrade head`), deploy new container, health check, cut over traffic.
- **Rollback**: Alembic `downgrade` tested in CI — every migration must have both `upgrade()` and `downgrade()` functions. CI runs `upgrade` followed by `downgrade` to verify reversibility.
- **Preview Apps**: Fly.io preview apps created for every PR, torn down on PR close.

##### Frontend (Vercel)
- **Trigger**: Auto-deploy on merge to `main` branch via Vercel GitHub integration.
- **Preview Deployments**: Vercel creates a unique preview URL for every PR push.
- **Environment Variables**: Managed via Vercel project settings; staging and production use different API endpoints.

#### Secrets Management
- **GitHub Actions Secrets**: Database URLs, API keys, Sentry DSN, Fly.io auth token, Clerk keys stored as GitHub repository secrets.
- **Environment Separation**: Separate secrets for staging and production environments.
- **No Secrets in Code**: `.env` files are in `.gitignore`. CI uses only injected secrets.

### Consequences

**Positive:**
- Automated quality gates: Type errors, lint violations, test failures, privilege leaks, and tenant isolation regressions are caught before merge, without requiring manual review.
- Fast deploy: Merge-to-deploy pipeline means accepted changes reach production within minutes.
- Staging on every PR: Preview environments allow manual verification of changes in a realistic environment before merge.
- Evaluator regression protection: Corpus regression tests prevent accuracy degradation from being merged without explicit sign-off.
- Migration safety: Up/down testing in CI ensures every migration is reversible for safe rollbacks.

**Challenges:**
- CI minutes cost: Running full test suites on every PR consumes GitHub Actions minutes. Mitigation: path-based triggering, pip/pnpm caching, and parallel job execution to minimize total minutes.
- Fly.io deploy speed: Container builds and Alembic migrations can be slow (2-5 min). Mitigation: Docker layer caching, multi-stage builds, and migration batching.
- Secrets management: Managing separate secrets for staging and production across GitHub, Fly.io, and Vercel requires discipline. Mitigation: document all required secrets in a `SECRETS.md` (without values) and verify in CI that all required env vars are set.
- Flaky E2E tests: Playwright tests may be flaky due to timing, network, or rendering issues. Mitigation: retry failed tests once, quarantine persistently flaky tests, and track flake rate as a metric.

---

**Date:** 2026-04-18
**Supersedes:** None
**Related ADRs:** ADR-0007 (Privileged Data Handling), ADR-0008 (External API Integration Strategy)
