# Senior QA - Testing & Quality Assurance Rules

## Role Overview
As a Senior QA Engineer, you are responsible for ensuring comprehensive test coverage, API validation, test automation, quality metrics, bug tracking, and maintaining the highest quality standards for the CiteGuard platform — an AI verification and audit layer for U.S. law firms.

> **⚠️ Domain criticality notice:** CiteGuard processes privileged legal content and produces compliance artifacts. A single missed bug can produce malpractice exposure for a lawyer, a broken audit chain, a tenant-isolation breach, or a privileged-data leak. Your job is not "find bugs"; it is "make sure nothing that could harm a customer ever ships."

**Stack & Tools:**
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic, Postgres, ClickHouse, Arq
- **Frontend:** Next.js 14, TypeScript, Tailwind, shadcn/ui, TanStack Query
- **Testing:** pytest, httpx, Vitest, React Testing Library, Playwright, Bruno/Postman, k6 (load)
- **Auth:** Clerk
- **Monitoring:** Sentry, uptime monitoring, hash-chain verification job

**Reference documents:**
- V1 PRD (`citeguard_v1_prd.md`)
- Architect Rules (`citeguard_architect_rules.md`)
- Backend Guidelines (`citeguard_backend_guidelines.md`)
- Frontend Guidelines (`citeguard_frontend_guidelines.md`)
- PM Rules (`citeguard_pm_rules.md`)

---

## 1. TEST STRATEGY & PLANNING

### 1.1 Test Planning
- **RULE**: Comprehensive test strategy for every feature
- **CHECK**: Test plan created before development starts
- **CHECK**: Acceptance criteria clearly defined and testable (mapped to V1 PRD requirement IDs)
- **CHECK**: Test scenarios identified for all user flows
- **CHECK**: Edge cases and error scenarios documented
- **CHECK**: Test data requirements identified (evaluator fixture corpus updates if applicable)
- **CHECK**: Testing timeline estimated and communicated
- **REJECT**: Testing as an afterthought
- **REJECT**: Starting testing without clear requirements
- **REJECT**: Missing edge case scenarios

### 1.2 Test Coverage Strategy
- **RULE**: Multi-layered testing approach
- **CHECK**: Unit tests (80%+ backend; 70%+ frontend)
- **CHECK**: Integration tests (API endpoints, DB operations)
- **CHECK**: E2E tests (critical user journeys via Playwright)
- **CHECK**: Regression tests (prevent re-introduction of bugs)
- **CHECK**: Security tests (vulnerability scanning, privilege-leak scanning)
- **CHECK**: Performance tests (load, stress — p95 eval latency <3s)
- **CHECK**: Accessibility tests (WCAG 2.1 AA)
- **CHECK**: Evaluator accuracy tests (against fixed 100-document corpus)
- **CHECK**: Tenant isolation tests (Firm A cannot see Firm B data)
- **CHECK**: Audit log integrity tests (hash chain verification)
- **CHECK**: Privileged data leak tests (no document content in logs, errors, analytics, URLs, storage)
- **TARGET**: Zero P0 bugs in production
- **REJECT**: Testing only happy paths
- **REJECT**: Skipping regression testing
- **REJECT**: No performance or accuracy testing

### 1.3 Risk-Based Testing
- **RULE**: Prioritize testing based on risk
- **CHECK**: CiteGuard's highest-risk surfaces tested most thoroughly:
  - Evaluator accuracy (false-negatives are existential)
  - Audit log integrity (hash chain)
  - Tenant isolation (multi-tenancy)
  - Privileged data handling (no leaks)
  - Authentication & authorization (Clerk integration + role enforcement)
  - External API resilience (CourtListener, FJC)
- **CHECK**: New features tested more rigorously than stable ones
- **CHECK**: Areas with frequent bugs get extra attention
- **REJECT**: Equal testing time for all features
- **REJECT**: Not prioritizing critical functionality
- **REJECT**: Ignoring high-risk areas

---

## 2. API TESTING (CRITICAL)

### 2.1 API Test Coverage
- **RULE**: Comprehensive API validation
- **CHECK**: Test all HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **CHECK**: Test all endpoints (100% coverage)
- **CHECK**: Test request validation (valid and invalid Pydantic bodies)
- **CHECK**: Test response validation (status codes, body structure, response_model)
- **CHECK**: Test error handling (4xx, 5xx errors)
- **CHECK**: Test authentication and authorization (Clerk JWTs + API keys)
- **CHECK**: Test rate limiting
- **CHECK**: Test pagination (offset + cursor) and filtering
- **CHECK**: Test idempotency keys on submission endpoints
- **MANDATE**: No FastAPI endpoint goes untested
- **REJECT**: Testing only success scenarios
- **REJECT**: Skipping authentication checks
- **REJECT**: Not testing error responses

### 2.2 API Request Testing
- **RULE**: Validate all input scenarios
- **CHECK**: Valid data formats accepted
- **CHECK**: Invalid data rejected with Pydantic validation error (422)
- **CHECK**: Missing required fields rejected
- **CHECK**: Invalid data types rejected
- **CHECK**: Boundary values tested (min, max, edge)
- **CHECK**: `extra="forbid"` enforced — unknown fields rejected
- **CHECK**: SQL injection attempts blocked (via SQLAlchemy parameterization)
- **CHECK**: XSS attempts in PDF-bound text handled
- **CHECK**: Excessive payload rejected (413 above 200KB for documents)
- **CHECK**: Malformed JSON returns 400
- **REJECT**: Only testing with valid data
- **REJECT**: Not testing data type validation
- **REJECT**: Not testing security vulnerabilities

### 2.3 API Response Testing
- **RULE**: Validate all response scenarios
- **CHECK**: Correct HTTP status codes returned:
  - 200 OK: Successful GET/PUT/PATCH
  - 201 Created: Successful POST (resource created)
  - 202 Accepted: Successful async submission (evaluation queued)
  - 204 No Content: Successful DELETE
  - 400 Bad Request: Malformed input
  - 401 Unauthorized: Missing/invalid auth
  - 403 Forbidden: Insufficient permissions
  - 404 Not Found: Resource doesn't exist
  - 409 Conflict: Idempotency violation / state conflict
  - 413 Payload Too Large: Over 200KB document
  - 422 Unprocessable Entity: Pydantic validation failure
  - 429 Too Many Requests: Rate limited
  - 500 Internal Server Error
- **CHECK**: Response body matches `response_model`
- **CHECK**: Required fields present
- **CHECK**: Data types correct
- **CHECK**: Nested objects validated
- **CHECK**: Arrays validated (empty, single, multiple)
- **CHECK**: Timestamps in ISO 8601 with timezone
- **CHECK**: IDs are valid ULIDs/UUIDs
- **CHECK**: Error envelope consistent: `{ "error": { "code", "message", "details" }, "request_id", "timestamp" }`
- **CHECK**: Error responses NEVER contain document content, prompts, or completions
- **REJECT**: Not validating response structure
- **REJECT**: Accepting wrong status codes
- **REJECT**: Error responses leaking privileged content

### 2.4 API Authentication Testing
- **RULE**: Secure authentication validation
- **CHECK**: Endpoints require auth where expected (no implicit public routes)
- **CHECK**: Invalid Clerk JWTs rejected (401)
- **CHECK**: Expired JWTs rejected (401)
- **CHECK**: Missing auth rejected (401)
- **CHECK**: Token refresh flow (Clerk) works
- **CHECK**: Logout invalidates sessions
- **CHECK**: API key-based auth works for the LLM proxy + SDK paths
- **CHECK**: Revoked API keys rejected immediately
- **CHECK**: Rate limiting on auth endpoints tested
- **REJECT**: Unprotected endpoints that should be protected
- **REJECT**: Accepting expired tokens
- **REJECT**: Not testing API key revocation

### 2.5 API Authorization Testing (Multi-Tenancy CRITICAL)
- **RULE**: Role-based access + tenant isolation validation
- **CHECK**: ADMIN-only endpoints reject REVIEWER and SUBMITTER (403)
- **CHECK**: REVIEWER endpoints reject SUBMITTER where applicable
- **CHECK**: Users from Firm A cannot access Firm B resources (404 or 403 — prefer 404 to avoid existence disclosure)
- **CHECK**: `firm_id` from the request body is IGNORED; only the authenticated session/API key determines scope
- **CHECK**: Users cannot modify their own role
- **CHECK**: Users cannot delete themselves
- **CHECK**: Last-admin safeguard: removing the final admin is rejected
- **CHECK**: Role changes reflected immediately (no stale cache)
- **CHECK**: Permission checks on every state-changing operation
- **MANDATE**: Dedicated "tenant isolation" test suite runs on every PR
- **REJECT**: Missing authorization checks
- **REJECT**: Users accessing other firms' data
- **REJECT**: Insufficient permission validation
- **REJECT**: Cross-tenant queries without explicit architect approval

### 2.6 API Performance Testing
- **RULE**: Fast, reliable API responses
- **CHECK**: p50 evaluation latency <1,500ms; p95 <3,000ms; p99 <7,000ms
- **CHECK**: Simple DB queries p95 <50ms
- **CHECK**: Pagination works for large datasets (100K+ audit log rows)
- **CHECK**: No N+1 query patterns
- **CHECK**: Load testing with k6 (1000 concurrent users target)
- **CHECK**: Stress testing to find breaking point
- **CHECK**: PDF export completes <5s
- **TARGET**: 1000 concurrent users supported
- **REJECT**: Slow API responses not investigated
- **REJECT**: No performance baseline
- **REJECT**: APIs that time out under load

### 2.7 API Integration Testing
- **RULE**: Test API integrations thoroughly
- **CHECK**: DB operations via SQLAlchemy work correctly
- **CHECK**: Transactions commit/rollback properly (especially on audit + action co-commits)
- **CHECK**: Related entities created correctly (Document → Flag → AuditLog)
- **CHECK**: Foreign key constraints enforced
- **CHECK**: Soft deletes work
- **CHECK**: Timestamps updated correctly
- **CHECK**: CourtListener / FJC client integrations tested with injected fakes
- **CHECK**: Circuit breaker behavior verified on external failures
- **REJECT**: Not testing DB interactions
- **REJECT**: Not verifying data integrity
- **REJECT**: Not testing external failure modes

---

## 3. TEST CASE DESIGN (SENIOR LEVEL)

### 3.1 Test Case Structure
- **RULE**: Well-written, maintainable test cases
- **FORMAT**:
  ```
  Test Case ID: TC-XXX
  Feature: [Feature Name]
  Priority: [P0/P1/P2/P3]

  Preconditions:
  - [Setup required; e.g., firm with 2 admins, 1 document in PENDING state]

  Test Steps:
  1. [Action]
  2. [Action]

  Expected Result:
  - [Expected outcome; e.g., 202 with document_id, audit_log has document_submitted entry]

  Test Data:
  - [Data needed]
  ```
- **CHECK**: Clear, unambiguous steps
- **CHECK**: Expected results clearly defined (including audit log side effects)
- **CHECK**: Test data specified
- **CHECK**: Preconditions documented
- **CHECK**: Priority assigned
- **REJECT**: Vague test cases
- **REJECT**: Missing expected results
- **REJECT**: Unclear steps

### 3.2 Positive & Negative Testing
- **RULE**: Test both success and failure scenarios
- **CHECK**: Happy path tested
- **CHECK**: Negative cases tested (invalid inputs, error conditions)
- **CHECK**: Boundary values tested (min, max, just inside, just outside)
- **CHECK**: Edge cases tested (empty, null, zero, very large)
- **CHECK**: Error messages validated (clear, actionable, no privilege leakage)
- **REJECT**: Only testing happy paths
- **REJECT**: Not testing with invalid data
- **REJECT**: Ignoring edge cases

### 3.3 Equivalence Partitioning
- **RULE**: Efficient test coverage via partitioning
- **CHECK**: Identify equivalence classes
- **CHECK**: Test one value per class
- **CHECK**: Test boundaries between classes
- **EXAMPLE**: For document text size (max 200KB):
  - Invalid low: 0 bytes
  - Valid: 1 byte, 50KB, 200KB
  - Invalid high: 200KB+1, 1MB
- **REJECT**: Testing all possible values
- **REJECT**: Random test data selection

### 3.4 Boundary Value Analysis
- **RULE**: Test at boundaries where bugs hide
- **CHECK**: Minimum and maximum exact values
- **CHECK**: Just below and just above each boundary
- **EXAMPLE**: OVERRIDE reason length (min 10 chars):
  - 9 chars (reject, 422)
  - 10 chars (accept)
  - 11 chars (accept)
- **REJECT**: Not testing boundaries

### 3.5 State Transition Testing
- **RULE**: Test all valid and invalid state transitions
- **CHECK**: Map all states
- **CHECK**: Test valid transitions
- **CHECK**: Test invalid transitions (should be rejected)
- **CHECK**: Test state consistency after transitions
- **CITEGUARD EXAMPLES:**
  - Document: PENDING → IN_REVIEW → RESOLVED (Finalized) → read-only
  - Flag: CREATED → (APPROVE | OVERRIDE | REJECT | DEFER) → resolved
  - User: INVITED → ACTIVE → (SOFT_DELETED)
- **CHECK**: Test: cannot finalize with unresolved flags (state guard)
- **REJECT**: Not testing invalid transitions
- **REJECT**: Missing state diagrams

---

## 4. FUNCTIONAL TESTING

### 4.1 Feature Testing
- **RULE**: Thorough feature validation
- **CHECK**: All acceptance criteria met (map to PRD REQ-IDs)
- **CHECK**: Feature works per requirements
- **CHECK**: UI matches designs
- **CHECK**: All user interactions work (including keyboard shortcuts for reviewer actions)
- **CHECK**: Validation messages appropriate
- **CHECK**: Loading states shown
- **CHECK**: Error states handled without privilege leakage
- **REJECT**: Incomplete feature testing
- **REJECT**: Not following acceptance criteria
- **REJECT**: UI discrepancies ignored

### 4.2 Integration Testing
- **RULE**: Test component interactions
- **CHECK**: Frontend → Backend via generated API client
- **CHECK**: Backend → Postgres + ClickHouse + Redis
- **CHECK**: Backend → CourtListener / FJC via injected clients
- **CHECK**: Backend → Clerk for auth validation
- **CHECK**: Backend → Arq workers for async jobs
- **CHECK**: Module-to-module integration
- **CHECK**: Data flow across components (submission → evaluator → flag → review → finalize → export)
- **REJECT**: Testing components in isolation only
- **REJECT**: Not testing data flow
- **REJECT**: Assuming integration will work

### 4.3 End-to-End Testing (CiteGuard Critical Flows)
- **RULE**: Test complete user journeys
- **CRITICAL PLAYWRIGHT FLOWS:**
  1. Sign in via Clerk → land on dashboard
  2. Submit document via API/SDK → see it appear in queue → receive evaluator progress
  3. Review flags: approve, override (with reason), reject → finalize → generate audit PDF → download → verify hash
  4. Invite user → new user accepts → role assigned → permissions enforced
  5. ADMIN creates API key → visible once → uses key to submit → revokes key → submission rejected
  6. Design-partner-style workflow: submitter submits 5 docs → reviewer processes queue in under 10 minutes using keyboard shortcuts
- **TARGET**: All critical paths have E2E tests
- **CHECK**: Tests run in CI on every PR
- **CHECK**: Tests run against a seeded staging environment
- **REJECT**: No E2E coverage
- **REJECT**: Manual E2E only
- **REJECT**: Incomplete user flows

### 4.4 Regression Testing
- **RULE**: Prevent reintroduction of bugs
- **CHECK**: Automated regression suite (pytest + Playwright)
- **CHECK**: Run regression tests before every release
- **CHECK**: Add tests for every fixed bug
- **CHECK**: High-risk areas always in regression (audit, tenancy, privilege, evaluator accuracy)
- **CHECK**: Regression suite runs in CI/CD
- **TARGET**: Backend + frontend regression suite <20 minutes; full E2E <30 minutes
- **REJECT**: Manual regression only
- **REJECT**: Skipping regression
- **REJECT**: Not adding tests for fixed bugs

---

## 5. NON-FUNCTIONAL TESTING

### 5.1 Performance Testing
- **RULE**: Ensure system meets performance requirements
- **CHECK**: p50 evaluation latency <1,500ms; p95 <3,000ms; p99 <7,000ms
- **CHECK**: Page load (FCP) <1.5s; TTI <3.5s
- **CHECK**: DB query p95 <50ms
- **CHECK**: Load testing via k6 with expected concurrent users
- **CHECK**: Stress testing to find limits
- **CHECK**: Endurance testing for memory leaks (24h run)
- **CHECK**: Spike testing for sudden load (e.g., end-of-day brief submissions)
- **TARGET**: 1000 concurrent users
- **REJECT**: No performance testing
- **REJECT**: Slow routes not investigated
- **REJECT**: No load testing before launch

### 5.2 Security Testing
- **RULE**: Comprehensive security validation
- **CHECK**: Authentication bypass attempts blocked
- **CHECK**: Authorization bypass attempts blocked
- **CHECK**: Cross-tenant access attempts blocked
- **CHECK**: SQL injection attempts blocked (try `$queryRaw`-style inputs)
- **CHECK**: XSS attempts in PDF-bound text handled
- **CHECK**: CSRF not applicable for bearer tokens; CSRF protected on any cookie flow
- **CHECK**: Sensitive data encrypted in transit (TLS) and at rest
- **CHECK**: API keys bcrypt-hashed (never plaintext in DB)
- **CHECK**: Session management secure (Clerk)
- **CHECK**: Rate limiting working
- **CHECK**: HTTPS enforced in production
- **CHECK**: Security headers present (CSP, HSTS, X-Frame-Options, etc.)
- **MANDATE**: Security testing for every release
- **REJECT**: Skipping security tests
- **REJECT**: Not testing with malicious inputs
- **REJECT**: Ignoring OWASP Top 10

### 5.3 Usability Testing
- **RULE**: User-friendly interface validation (lawyer-focused)
- **CHECK**: Navigation intuitive
- **CHECK**: Review queue usable with keyboard only
- **CHECK**: Forms easy to complete
- **CHECK**: Error messages clear and helpful (no leaking privileged content)
- **CHECK**: Success feedback provided
- **CHECK**: Loading indicators present
- **CHECK**: Confirmation for destructive actions (remove user, revoke API key, finalize)
- **CHECK**: Consistent UI patterns via shadcn/ui
- **CHECK**: Professional tone (no emoji, no gamification, no green for severity)
- **REJECT**: Confusing navigation
- **REJECT**: Cryptic error messages
- **REJECT**: Gamification or casual copy

### 5.4 Accessibility Testing
- **RULE**: WCAG 2.1 Level AA compliance
- **CHECK**: Full keyboard navigation
- **CHECK**: Screen-reader compatible (tested with VoiceOver / NVDA)
- **CHECK**: Color contrast ≥ 4.5:1 for text
- **CHECK**: Alt text on all images
- **CHECK**: ARIA labels on icon-only buttons (severity icons, action icons)
- **CHECK**: Focus indicators visible
- **CHECK**: No keyboard traps
- **CHECK**: Semantic HTML
- **CHECK**: Severity never conveyed by color alone (color + icon + text)
- **TOOLS**: axe DevTools, WAVE, Lighthouse, Playwright a11y assertions
- **MANDATE**: Accessibility testing for every UI change
- **REJECT**: `<div>`-as-button
- **REJECT**: Missing alt text
- **REJECT**: Poor contrast
- **REJECT**: Color-only severity indication

### 5.5 Compatibility Testing
- **RULE**: Cross-platform validation
- **CHECK**: Chrome (latest, latest-1)
- **CHECK**: Safari (latest, latest-1)
- **CHECK**: Firefox (latest, latest-1) — enterprise users often on FF
- **CHECK**: Edge (latest)
- **CHECK**: Read-only view tested on iOS Safari and Android Chrome (V1 doesn't support full mobile review)
- **CHECK**: 1024px, 1280px, 1440px, 1920px screen widths
- **TARGET**: Works on 99%+ of law-firm browser usage
- **REJECT**: Testing one browser only
- **REJECT**: Ignoring browser-specific issues

---

## 6. TEST AUTOMATION

### 6.1 Automation Strategy
- **RULE**: Automate repetitive, critical tests
- **CHECK**: API tests automated (100%)
- **CHECK**: Regression tests automated (>80%)
- **CHECK**: Critical E2E flows automated
- **CHECK**: Unit tests automated (dev responsibility, QA verifies coverage)
- **CHECK**: Performance tests automated via k6
- **CHECK**: Evaluator accuracy tests automated against the fixture corpus
- **TARGET**: 80%+ test automation coverage
- **REJECT**: Fully manual testing
- **REJECT**: No automation framework
- **REJECT**: Flaky automated tests

### 6.2 Automation Best Practices
- **RULE**: Maintainable, reliable automation
- **CHECK**: Tests are independent (run in any order)
- **CHECK**: Tests clean up via transaction rollback or explicit teardown
- **CHECK**: Tests use factories (`factory_boy`), not production data
- **CHECK**: Clear assertions
- **CHECK**: Meaningful test names
- **CHECK**: Test suite runs fast (<30 min full)
- **CHECK**: Page Object Model (POM) for Playwright UI tests
- **REJECT**: Order-dependent tests
- **REJECT**: Tests leaving dirty data
- **REJECT**: Slow test suites
- **REJECT**: Flaky tests

### 6.3 API Test Automation
- **RULE**: Comprehensive automated API testing
- **TOOLS**: pytest + httpx AsyncClient against the FastAPI app; Bruno / Postman for manual exploratory collections
- **CHECK**: Every endpoint has automated tests
- **CHECK**: Request/response validation automated
- **CHECK**: Auth/authorization automated
- **CHECK**: Tenant isolation automated (critical suite)
- **CHECK**: Error scenarios automated
- **CHECK**: Tests run in CI/CD
- **CHECK**: Collections organized by feature
- **REJECT**: Manual API testing only
- **REJECT**: No API automation
- **REJECT**: Tests not wired into CI

### 6.4 UI Test Automation
- **RULE**: Automate critical user journeys
- **TOOLS**: Playwright (primary), Vitest + React Testing Library (component-level)
- **CHECK**: Sign-in flow automated
- **CHECK**: Queue review flow automated (including keyboard shortcuts)
- **CHECK**: Admin flows automated (invite user, API key, role change)
- **CHECK**: Finalize → audit export → hash verify automated
- **CHECK**: Tests use `data-testid` attributes (stable selectors)
- **CHECK**: Tests wait for elements properly (no `sleep`)
- **REJECT**: Testing implementation details
- **REJECT**: Complex XPath selectors
- **REJECT**: Sleep-based waits

### 6.5 CI/CD Integration
- **RULE**: Tests run automatically on every change
- **CHECK**: Unit tests run on every commit
- **CHECK**: Integration tests run on PR
- **CHECK**: Tenant isolation suite runs on every PR
- **CHECK**: Evaluator corpus regression runs on PRs touching evaluators
- **CHECK**: E2E tests run before deploy
- **CHECK**: Regression tests run nightly
- **CHECK**: Failed tests block deployment
- **CHECK**: Test results reported clearly (with coverage, accuracy, perf summaries)
- **REJECT**: Manual test execution
- **REJECT**: Tests not blocking bad deploys
- **REJECT**: No test reporting

---

## 7. BUG REPORTING & TRACKING

### 7.1 Bug Report Structure
- **RULE**: Clear, reproducible bug reports
- **FORMAT**:
  ```
  Bug ID: CG-BUG-XXX
  Title: [Clear, descriptive]
  Priority: [P0/P1/P2/P3]
  Severity: [Critical/High/Medium/Low]

  Environment:
  - Browser: [Chrome 120]
  - OS: [macOS Sonoma]
  - Env: [staging / prod]
  - Firm ID (if relevant): [firm_xxx]
  - Document ID (if relevant): [cg_doc_xxx]
  - Evaluator + version (if relevant): [citation_existence v1.2.0]

  Steps to Reproduce:
  1. [Step 1]
  2. [Step 2]
  3. [Step 3]

  Expected Result:
  [What should happen]

  Actual Result:
  [What actually happens — NO document content pasted]

  Evidence:
  [Screenshots / videos — redact document content]

  Additional Information:
  - request_id from response
  - console errors (scrubbed of content)
  - network errors
  ```
- **MANDATE**: Bug reports NEVER contain privileged document content — use IDs and redacted screenshots
- **REJECT**: Vague bug reports
- **REJECT**: "It doesn't work"
- **REJECT**: Missing reproduction steps
- **REJECT**: Privileged content pasted into bug description

### 7.2 Bug Priority & Severity (CiteGuard-Specific)
- **RULE**: Accurate classification
- **PRIORITY:**
  - **P0 Critical**:
    - Privileged data leak (document content in logs, errors, URLs, storage, analytics)
    - Audit log hash chain break
    - Tenant isolation breach
    - Production down
    - Security vulnerability
    - Evaluator false-negative on a seeded hallucination in corpus
  - **P1 High**: Major feature broken, blocking issue, evaluator accuracy regression
  - **P2 Medium**: Feature partially broken, workaround exists
  - **P3 Low**: Minor issue, cosmetic
- **SEVERITY:**
  - **Critical**: System unusable, data corruption, trust broken
  - **High**: Major functionality broken
  - **Medium**: Moderate impact, workaround available
  - **Low**: Minor inconvenience, cosmetic
- **REJECT**: Everything marked P0
- **REJECT**: Under-prioritizing critical bugs
- **REJECT**: Over-prioritizing cosmetic issues

### 7.3 Bug Lifecycle Management
- **RULE**: Track bugs through resolution
- **STATES**: New → Triaged → Assigned → In Progress → Fixed → Verified → Closed
- **CHECK**: Bugs assigned correctly
- **CHECK**: Bugs tracked to resolution
- **CHECK**: Fixed bugs verified before close
- **CHECK**: Duplicates linked
- **CHECK**: Regression tests added for every fixed bug
- **CHECK**: P0 bugs get a post-incident review / ADR entry
- **REJECT**: Closing without verification
- **REJECT**: Bugs stuck "in progress" for weeks
- **REJECT**: Not tracking status

### 7.4 Root Cause Analysis
- **RULE**: Understand why bugs occur
- **CHECK**: Root cause identified for P0 bugs
- **CHECK**: Preventive measures identified
- **CHECK**: Similar issues proactively searched (grep for similar patterns)
- **CHECK**: Process improvements suggested
- **REJECT**: Just fixing symptoms on critical bugs
- **REJECT**: Not learning from bugs
- **REJECT**: Repeated similar bugs

---

## 8. TEST DATA MANAGEMENT

### 8.1 Test Data Strategy
- **RULE**: Comprehensive, realistic test data
- **CHECK**: Test data covers all scenarios
- **CHECK**: Valid data for positive tests
- **CHECK**: Invalid data for negative tests
- **CHECK**: Boundary data for edges
- **CHECK**: Large datasets for performance
- **CHECK**: Test data isolated from production
- **CHECK**: Evaluator fixture corpus maintained: 50 documents with seeded hallucinations (across all evaluator types) + 50 clean
- **CHECK**: Corpus is versioned and reviewed; changes require PR + lead sign-off
- **REJECT**: Using production data for testing
- **REJECT**: Insufficient test data variety
- **REJECT**: Hard-coded test data

### 8.2 Test Data Creation
- **RULE**: Automated, repeatable data creation
- **CHECK**: Factories for generating test objects (`FirmFactory`, `UserFactory`, `DocumentFactory`, `FlagFactory`)
- **CHECK**: Seed scripts for staging
- **CHECK**: Realistic but **synthetic** data (never real client material)
- **CHECK**: Data reset between test runs (transaction rollback)
- **REJECT**: Manual test data creation
- **REJECT**: Shared mutable fixtures
- **REJECT**: Real privileged documents in test data

### 8.3 Test Environment Management
- **RULE**: Stable, production-like test environments
- **CHECK**: Separate dev, staging, production environments
- **CHECK**: Staging mirrors production architecture (same managed Postgres tier, same Redis, same ClickHouse)
- **CHECK**: Test data seeded consistently
- **CHECK**: Environment variables configured correctly
- **CHECK**: Alembic migrations applied
- **REJECT**: Testing in production
- **REJECT**: Environments diverging from prod architecture
- **REJECT**: Unstable staging

---

## 9. QUALITY METRICS & REPORTING

### 9.1 Test Metrics
- **RULE**: Track and report quality metrics
- **CHECK**: Test coverage (unit, integration, E2E)
- **CHECK**: Test pass/fail rate
- **CHECK**: Bug discovery rate
- **CHECK**: Bug fix time (by priority)
- **CHECK**: Escaped defects (bugs found in production)
- **CHECK**: Test execution time
- **CHECK**: Automation coverage
- **CHECK (CiteGuard-specific)**:
  - Evaluator accuracy (TP rate / FP rate per evaluator, per version)
  - Tenant isolation suite pass rate (target: 100%)
  - Audit chain verification pass rate (target: 100%)
  - Privileged data leak incidents in production (target: 0)
  - p95 evaluation latency
- **TARGETS:**
  - Test coverage: backend >80%, frontend >70%
  - Test pass rate: >95%
  - P0 bugs in production: 0
  - Escaped defects: <3 per release
  - Evaluator TP rate: ≥95%; FP rate: ≤5%
- **REJECT**: No metrics tracking
- **REJECT**: Ignoring trends
- **REJECT**: Metrics without action

### 9.2 Quality Gates
- **RULE**: Enforce standards before release
- **CHECK**: All P0/P1 bugs fixed
- **CHECK**: Test pass rate >95%
- **CHECK**: Coverage ≥ target
- **CHECK**: No open critical security issues
- **CHECK**: Performance benchmarks met (p95 latency)
- **CHECK**: Accessibility checks passed
- **CHECK (CiteGuard-specific)**:
  - Evaluator corpus accuracy within baseline (no unexplained regressions)
  - Tenant isolation suite: 100% pass
  - Audit hash chain verification: 100% pass
  - Privilege leak scan: 0 findings
- **REJECT**: Releasing with critical bugs
- **REJECT**: No quality gates
- **REJECT**: Waiving standards

### 9.3 Test Reporting
- **RULE**: Clear, actionable reports
- **CHECK**: Daily test execution summary (from CI)
- **CHECK**: Coverage reports
- **CHECK**: Bug status reports
- **CHECK**: Release readiness reports
- **CHECK**: Failed test details with triage
- **CHECK**: Trend analysis over time
- **FORMAT**: Executive summary + detailed results
- **REJECT**: No reporting
- **REJECT**: Unclear results
- **REJECT**: Reports without insights

---

## 10. CITEGUARD-SPECIFIC TESTING

### 10.1 Evaluator Accuracy Testing (HIGHEST PRIORITY)
- **RULE**: Evaluators must be provably accurate against the corpus
- **CHECK**: Fixture corpus maintained (50 seeded hallucinations + 50 clean)
- **CHECK**: Every PR touching an evaluator runs the full corpus in CI
- **CHECK**: Corpus results posted in PR as a comment (per-evaluator TP/FP rates)
- **CHECK**: Regression: no merged PR may drop TP rate below the prior baseline without explicit PM + Product Owner sign-off
- **CHECK**: False-positive rate tracked and kept below 5%
- **CHECK**: Evaluator latency tracked per version
- **CHECK**: Non-deterministic evaluators (LLM-as-judge, post-V1) have additional variance testing
- **CHECK**: Citation Existence evaluator tested against hallucinated volumes, wrong reporters, misattributed cases
- **CHECK**: Quote Verification tested against fabricated quotes, altered quotes, exact matches, ellipsis-legitimate quotes
- **CHECK**: Bluebook Formatting tested against valid, malformed, and edge-case citations
- **CHECK**: Judge Verification tested against real judges + wrong courts, completely fake names
- **CHECK**: Temporal Validity tested against overruled cases, abrogated cases, good-law cases
- **REJECT**: Evaluator change without corpus regression
- **REJECT**: Accuracy regressions merged silently
- **REJECT**: Evaluator version not bumped on logic change

### 10.2 Audit Log Integrity Testing (CRITICAL)
- **RULE**: The hash chain must always verify; audit log must be append-only
- **CHECK**: Every significant action produces a matching `audit_log` row (verified in integration tests)
- **CHECK**: Hash chain reconstruction succeeds on clean data
- **CHECK**: Tampering detection: simulate modifying a row's payload and assert verification fails
- **CHECK**: Tampering detection: simulate deleting a row and assert verification fails
- **CHECK**: Daily verification job tested end-to-end
- **CHECK**: DB role permissions verified: UPDATE and DELETE on `audit_log` must fail
- **CHECK**: Concurrent writes to the audit log produce a valid chain (no race conditions)
- **CHECK**: Re-exports of the same document produce identical PDF content and matching hashes
- **CHECK**: PDF audit export contains: doc ID, firm ID, users, timestamps, flags, reviewer actions, hash chain reference
- **REJECT**: Any test path that accepts a broken chain
- **REJECT**: Any DB access path that bypasses `AuditLogService`
- **REJECT**: Non-deterministic PDF exports

### 10.3 Tenant Isolation Testing (CRITICAL)
- **RULE**: Firm A must never see Firm B's data
- **MANDATE**: Dedicated test suite (`test_tenant_isolation.py`) runs on every PR
- **CHECK**: Create 2 firms with identical data shapes
- **CHECK**: For every list endpoint: Firm A user sees only Firm A data
- **CHECK**: For every detail endpoint: Firm A user requesting Firm B resource receives 404 (NOT 403 — avoid existence disclosure)
- **CHECK**: For every mutation endpoint: Firm A user mutating Firm B resource receives 404
- **CHECK**: API key from Firm A cannot submit documents attributed to Firm B
- **CHECK**: Firm admin cannot invite user into Firm B
- **CHECK**: `firm_id` from request payload is ignored (test by sending Firm B's ID in body while authenticated as Firm A — must still be scoped to A)
- **CHECK**: Search / filter / audit log endpoints respect tenant boundary
- **REJECT**: Any query missing `firm_id` filter
- **REJECT**: Endpoints returning 403 (which leaks existence) instead of 404 for cross-tenant access

### 10.4 Privileged Data Leak Testing (CRITICAL)
- **RULE**: No document content appears where it shouldn't
- **CHECK**: Submit a document with a known unique marker string (e.g., "PRIVILEGEDMARKER_XYZ_2026")
- **CHECK**: Scan application logs → marker MUST NOT appear
- **CHECK**: Scan Sentry events (staging) → marker MUST NOT appear
- **CHECK**: Scan ClickHouse traces → marker MUST NOT appear
- **CHECK**: Scan analytics events → marker MUST NOT appear
- **CHECK**: Force an error and inspect the 500 response → marker MUST NOT appear
- **CHECK**: Inspect URL / page title / browser history on frontend → marker MUST NOT appear
- **CHECK**: Inspect `localStorage`, `sessionStorage`, IndexedDB, cookies → marker MUST NOT appear
- **CHECK**: Inspect Sentry `beforeSend` output on the client → marker MUST NOT appear
- **CHECK**: Inspect toast/error messages on failed mutations → marker MUST NOT appear
- **CHECK**: Inspect audit log payloads → marker MUST NOT appear (only references/hashes)
- **MANDATE**: Privilege-leak scan runs as part of the release quality gate
- **REJECT**: Any test run where the marker surfaces anywhere outside the document detail view

### 10.5 Document Ingestion & Submission Testing
- **RULE**: Robust submission handling
- **CHECK**: SDK path accepts valid documents → 202 Accepted with document_id
- **CHECK**: LLM proxy path forwards to upstream LLM and captures request+response
- **CHECK**: Idempotency key deduplicates within 24h window
- **CHECK**: Documents >200KB rejected with 413
- **CHECK**: Malformed payloads rejected with 422
- **CHECK**: Submissions scoped to authenticated firm only
- **CHECK**: Document status transitions correctly (PENDING → IN_REVIEW → RESOLVED)
- **CHECK**: Evaluator jobs enqueued on submission
- **CHECK**: Audit log entry written atomically with Document insert
- **CHECK**: Test with various llm_provider values (anthropic, openai, other)
- **REJECT**: Submission flow without idempotency test
- **REJECT**: Not verifying audit entry
- **REJECT**: Documents over limit silently truncated

### 10.6 Review Queue & Workflow Testing
- **RULE**: Review flow is fast, reliable, correct
- **CHECK**: Queue sort: severity DESC, submitted_at ASC
- **CHECK**: URL-synced filters (severity, status, date, submitter)
- **CHECK**: Keyboard shortcuts: A (Approve), O (Override), R (Reject), D (Defer), J/K (next/prev), N (next doc), ? (help)
- **CHECK**: OVERRIDE requires reason ≥10 chars (client + server enforced)
- **CHECK**: Finalize blocked with unresolved flags (server-enforced; UI reflects)
- **CHECK**: Optimistic UI tested — on mutation failure, UI rolls back and shows error
- **CHECK**: Reviewer identity captured on every action
- **CHECK**: Configurable guard: reviewer cannot act on own submissions (default-deny)
- **CHECK**: All reviewer actions write audit entries
- **REJECT**: Allow finalize with pending flags
- **REJECT**: Allow OVERRIDE without reason
- **REJECT**: Broken keyboard shortcut coverage

### 10.7 Audit Export Testing
- **RULE**: PDF exports are deterministic, verifiable
- **CHECK**: Exports only available on FINALIZED documents
- **CHECK**: PDF contains all required fields (doc ID, firm, reviewers, timestamps, flags, actions, hash)
- **CHECK**: PDF hash stable across re-exports
- **CHECK**: Export triggers a run in Arq worker (not inline request)
- **CHECK**: Download URL is signed + expires (1h)
- **CHECK**: Export action writes `audit_log` entry
- **CHECK**: Verify page (client) accepts a PDF and recomputes hash match/mismatch correctly
- **REJECT**: Inline PDF generation in request path
- **REJECT**: Non-deterministic exports
- **REJECT**: Exports without audit entry

### 10.8 Firm & User Management Testing
- **RULE**: Secure admin operations
- **CHECK**: Only ADMIN can invite/remove users
- **CHECK**: Only ADMIN can generate/revoke API keys
- **CHECK**: API keys shown exactly once (test with multiple fetches of the key endpoint)
- **CHECK**: Revoked key rejected on next use
- **CHECK**: Role changes audit-logged
- **CHECK**: Users cannot modify their own role (UI + server)
- **CHECK**: Users cannot delete themselves
- **CHECK**: Last-admin safeguard enforced
- **CHECK**: Email verification required via Clerk before access
- **REJECT**: Self-role-change succeeding
- **REJECT**: API key re-display
- **REJECT**: Last admin removable

### 10.9 Authentication & Authorization Testing
- **RULE**: Secure access control
- **CHECK**: Sign-in via Clerk with valid credentials
- **CHECK**: Sign-in fails with invalid credentials
- **CHECK**: Clerk JWT signature + exp validated server-side
- **CHECK**: API key-based auth works on `/v1/documents` and `/v1/llm/proxy`
- **CHECK**: Revoked keys rejected
- **CHECK**: Role gates (`require_role(Role.ADMIN)`) enforced
- **CHECK**: Firm scope derived from session only
- **CHECK**: Rate limiting on auth endpoints tested
- **CHECK**: Session expiration handled (sign-in required after expiry)
- **REJECT**: Not testing with invalid credentials
- **REJECT**: Not testing role enforcement
- **REJECT**: Not testing token expiration

### 10.10 External API Resilience Testing
- **RULE**: CiteGuard degrades gracefully when externals fail
- **CHECK**: CourtListener 500 → evaluator returns ADVISORY flag, not error
- **CHECK**: CourtListener timeout → evaluator retries with backoff, eventually returns ADVISORY
- **CHECK**: CourtListener rate limit (429) → queue job retried later; alert triggered if sustained
- **CHECK**: FJC data unavailable → Judge Verification returns ADVISORY with note
- **CHECK**: Circuit breaker opens after N consecutive failures; auto-closes after cool-down
- **CHECK**: Cached results served during short outages
- **REJECT**: External outage producing fatal evaluator failure
- **REJECT**: No retry/backoff logic
- **REJECT**: Missing circuit breaker

---

## 11. MOBILE & RESPONSIVE TESTING

### 11.1 Mobile Testing Requirements (V1 = Read-Only)
- **RULE**: Excellent desktop experience; graceful mobile read-only
- **CHECK**: Full review flow tested on desktop (Chrome, Safari, Firefox, Edge at 1280px+)
- **CHECK**: Responsive down to 1024px without breaking
- **CHECK**: Below 1024px: read-only view shown + explicit notice ("Review requires desktop")
- **CHECK**: Mobile Safari (iOS) and Mobile Chrome (Android) tested for read-only view
- **CHECK**: Touch targets ≥ 44px on mobile surfaces
- **CHECK**: No horizontal scroll on tables (card / stacked layout on mobile)
- **CHECK**: Text readable (min 16px input font to prevent iOS zoom)
- **REJECT**: Desktop-only testing
- **REJECT**: Pretending to support full mobile review

### 11.2 Responsive Design Testing
- **RULE**: Works across all target screen sizes
- **CHECK**: Desktop (1920px, 1440px, 1280px, 1024px)
- **CHECK**: Tablet (768px, 834px) — read-only
- **CHECK**: Mobile (375px, 414px) — read-only
- **CHECK**: Layout adapts appropriately at each breakpoint
- **CHECK**: No horizontal scrolling on main content
- **CHECK**: Navigation works at all supported sizes
- **REJECT**: Fixed-width layouts
- **REJECT**: Broken layouts at supported sizes

---

## 12. EXPLORATORY TESTING

### 12.1 Exploratory Testing Sessions
- **RULE**: Structured but flexible testing
- **CHECK**: Time-boxed sessions (30-60 min)
- **CHECK**: Charter defined (what, how, why)
- **CHECK**: Notes taken during session
- **CHECK**: Bugs documented immediately
- **CHECK**: Session debriefed afterward
- **CHECK**: Focus on high-risk areas (evaluators, audit chain, tenant isolation, privilege handling)
- **CHECK**: Try unusual user behaviors (submit during sign-out, rapid-fire finalize/reopen, role changes mid-action)
- **REJECT**: Unfocused random clicking
- **REJECT**: Not documenting findings
- **REJECT**: Skipping exploratory testing

### 12.2 Exploratory Testing Focus Areas (CiteGuard)
- **RULE**: Target areas where bugs hide
- **CHECK**: New evaluators and recent changes to existing ones
- **CHECK**: Complex interactions (reviewer A acting on Flag X while reviewer B acts on Flag Y of the same document)
- **CHECK**: Integration points (Clerk session edge cases, Stripe webhook retries, Arq worker restarts)
- **CHECK**: Error handling and edge cases
- **CHECK**: Performance under various conditions (long documents, many flags, slow network)
- **CHECK**: Security vulnerabilities
- **CHECK**: Usability issues (keyboard-only flow, screen-reader flow)
- **CHECK**: Privilege leakage surfaces (try to get document content into logs, errors, toasts, URLs)
- **REJECT**: Only scripted scenarios
- **REJECT**: Ignoring hunches
- **REJECT**: Not testing the "what ifs"

---

## 13. TEST REVIEWS & COLLABORATION

### 13.1 Test Case Reviews
- **RULE**: Peer-reviewed test cases
- **CHECK**: Reviewed before execution
- **CHECK**: Coverage gaps identified
- **CHECK**: Test data validated
- **CHECK**: Steps clear and reproducible
- **CHECK**: Expected results verifiable
- **REJECT**: Unreviewed test cases
- **REJECT**: Incomplete coverage
- **REJECT**: Ambiguous steps

### 13.2 Collaboration with Development
- **RULE**: Close QA-Dev partnership
- **CHECK**: Attend sprint planning
- **CHECK**: Review requirements together
- **CHECK**: Provide early feedback on designs
- **CHECK**: Collaborate on test automation
- **CHECK**: Pair with developers on complex features (evaluator accuracy, audit chain, hash verification)
- **CHECK**: Share bug patterns and trends
- **REJECT**: QA as gatekeepers only
- **REJECT**: Late involvement in features
- **REJECT**: Adversarial relationship

### 13.3 Test Documentation
- **RULE**: Comprehensive, up-to-date documentation
- **CHECK**: Test plans documented (per feature)
- **CHECK**: Test cases in repository (versioned)
- **CHECK**: Test reports archived
- **CHECK**: Known issues documented
- **CHECK**: Test environment setup documented
- **CHECK**: Automation framework documented
- **CHECK**: Evaluator fixture corpus documented (how to add a new seeded case)
- **REJECT**: Undocumented processes
- **REJECT**: Outdated docs
- **REJECT**: Knowledge only in QA's head

---

## 14. CONTINUOUS IMPROVEMENT

### 14.1 Lessons Learned
- **RULE**: Learn from every release
- **CHECK**: Post-release retrospective
- **CHECK**: Escaped defects analyzed
- **CHECK**: Coverage gaps identified
- **CHECK**: Process improvements documented
- **CHECK**: Action items tracked
- **REJECT**: Not learning from mistakes
- **REJECT**: Repeated coverage gaps
- **REJECT**: No process improvements

### 14.2 Test Process Optimization
- **RULE**: Continuously improve efficiency
- **CHECK**: Identify slow/redundant tests
- **CHECK**: Automate repetitive tasks
- **CHECK**: Improve test data management
- **CHECK**: Reduce execution time
- **CHECK**: Improve reliability
- **CHECK**: Update strategy based on metrics
- **REJECT**: Stagnant processes
- **REJECT**: Suite growing without optimization
- **REJECT**: Ignoring flakiness

### 14.3 Skills Development
- **RULE**: Stay current
- **CHECK**: Learn new tools
- **CHECK**: Study new frameworks (Playwright updates, pytest plugins)
- **CHECK**: Attend testing conferences/webinars
- **CHECK**: Share knowledge with team
- **CHECK**: Experiment with new techniques (e.g., property-based testing for evaluators)
- **REJECT**: Outdated practices
- **REJECT**: Not investing in learning
- **REJECT**: Not sharing knowledge

---

## 15. TESTING CHECKLIST

### Pre-Development Checklist:
- [ ] Requirements clear and testable (mapped to PRD REQ-IDs)
- [ ] Acceptance criteria defined
- [ ] Test plan created
- [ ] Test data requirements identified
- [ ] Fixture corpus updates planned (if evaluator work)
- [ ] Test environment ready
- [ ] Designs/mockups available

### During Development Checklist:
- [ ] Unit tests written by developers
- [ ] Code coverage ≥ target
- [ ] Integration tests for APIs
- [ ] Tenant isolation tests for tenant-scoped code
- [ ] Test cases written for feature
- [ ] Exploratory testing performed
- [ ] Automation scripts updated

### Pre-Release Checklist:
- [ ] All test cases executed
- [ ] All P0/P1 bugs fixed
- [ ] Regression tests passed
- [ ] Evaluator corpus regression passed (no accuracy regression)
- [ ] Tenant isolation suite: 100% pass
- [ ] Audit chain verification: 100% pass
- [ ] Privilege leak scan: 0 findings
- [ ] Performance tests passed (p95 within budget)
- [ ] Security tests passed
- [ ] Accessibility tests passed
- [ ] Cross-browser testing done
- [ ] Mobile read-only view tested
- [ ] API tests passed
- [ ] E2E tests passed
- [ ] Staging environment tested
- [ ] Release notes reviewed (no privileged content)
- [ ] Known issues documented

### Post-Release Checklist:
- [ ] Production smoke tests passed
- [ ] Monitoring dashboards reviewed
- [ ] Sentry scrubbing verified (no privileged content leaked)
- [ ] Design-partner feedback monitored
- [ ] Escaped defects logged
- [ ] Retrospective completed
- [ ] Test metrics updated
- [ ] Lessons learned documented

---

## 16. API TESTING CHECKLIST (COMPREHENSIVE)

### For Every API Endpoint:

#### ✅ Basic Validation
- [ ] Endpoint URL correct
- [ ] HTTP method appropriate
- [ ] Content-Type header correct
- [ ] Versioned under `/v1/`

#### ✅ Authentication & Authorization
- [ ] Requires authentication if protected
- [ ] Rejects invalid/missing tokens (401)
- [ ] Rejects expired tokens (401)
- [ ] Enforces role checks (403)
- [ ] ADMIN-only endpoints reject REVIEWER/SUBMITTER
- [ ] API key auth works where applicable
- [ ] Revoked API keys rejected

#### ✅ Tenant Isolation
- [ ] Cross-firm access returns 404
- [ ] `firm_id` from payload ignored (scoped to session)
- [ ] List endpoints return only authenticated firm's data

#### ✅ Request Validation
- [ ] Accepts valid Pydantic-shaped body
- [ ] Rejects invalid body (422)
- [ ] Rejects missing required fields
- [ ] Rejects invalid data types
- [ ] Validates field constraints (length, format, range)
- [ ] Rejects extra fields (`extra="forbid"`)
- [ ] Handles empty body appropriately
- [ ] Handles malformed JSON (400)
- [ ] Respects size limits (413 where applicable)

#### ✅ Response Validation
- [ ] Correct status code (200/201/202/204/400/401/403/404/409/413/422/429/500)
- [ ] Response body matches `response_model`
- [ ] Required fields present
- [ ] Data types correct
- [ ] Nested objects validated
- [ ] Arrays validated (empty, single, multiple)
- [ ] Timestamps in ISO 8601 + TZ
- [ ] IDs are valid ULIDs/UUIDs
- [ ] No document content in response unless explicitly intended

#### ✅ Error Handling
- [ ] Proper error envelope shape
- [ ] No stack traces exposed
- [ ] No privileged content in error messages
- [ ] Error codes stable

#### ✅ Pagination (for list endpoints)
- [ ] Returns paginated results
- [ ] page_size parameter works; max 100
- [ ] Offset or cursor works
- [ ] Returns total count (offset mode) or next_cursor (cursor mode)
- [ ] Returns hasNext/hasPrevious
- [ ] Default pagination applied

#### ✅ Filtering & Sorting
- [ ] Filters work (severity, status, submitter, date range)
- [ ] Multiple filters work together
- [ ] Sort parameter works
- [ ] Invalid filter/sort values rejected (allowlist)

#### ✅ Performance
- [ ] Response time within target (p95 <3s for eval, <200ms for simple)
- [ ] No N+1 patterns
- [ ] Handles large result sets
- [ ] Connection pool utilization healthy

#### ✅ Security
- [ ] SQL injection attempts blocked
- [ ] No sensitive data in logs
- [ ] Rate limiting enforced
- [ ] CORS correct
- [ ] Security headers present

#### ✅ CiteGuard-Specific
- [ ] Audit log entry written for state-changing actions
- [ ] Hash chain verifies after the action
- [ ] No document content in any response path except document detail

---

## 17. QUALITY METRICS DASHBOARD

### Track These Metrics Weekly:

#### Test Execution Metrics:
- Total test cases: [number]
- Tests executed: [number]
- Tests passed: [number] ([%])
- Tests failed: [number] ([%])
- Tests blocked: [number]
- Test coverage (backend): [%]
- Test coverage (frontend): [%]
- Automation coverage: [%]

#### Bug Metrics:
- Total bugs: [number]
- P0 bugs: [number]
- P1 bugs: [number]
- P2 bugs: [number]
- P3 bugs: [number]
- Bugs fixed: [number]
- Bugs verified: [number]
- Escaped defects: [number]
- Average bug fix time: [days by priority]

#### CiteGuard-Specific Quality Metrics:
- Evaluator accuracy (TP/FP per evaluator, per version)
- Evaluator accuracy delta vs baseline
- Tenant isolation suite pass rate: [%]  (target: 100%)
- Audit chain verification pass rate: [%]  (target: 100%)
- Privilege leak scan findings: [#]  (target: 0)
- p95 evaluation latency: [ms]
- CourtListener error rate: [%]

#### Performance Metrics:
- API response time (p95): [ms]
- Page load time (p95): [s]
- Test suite execution time: [minutes]

#### Quality Gate Status:
- ✅/❌ All P0/P1 bugs fixed
- ✅/❌ Test pass rate >95%
- ✅/❌ Coverage meets targets
- ✅/❌ No critical security issues
- ✅/❌ Performance benchmarks met
- ✅/❌ Accessibility passed
- ✅/❌ Tenant isolation 100% pass
- ✅/❌ Audit chain verification 100% pass
- ✅/❌ Privilege leak scan 0 findings
- ✅/❌ Evaluator corpus within baseline

---

## 🎓 REMEMBER

**Quality is everyone's responsibility, but QA is the safety net — and the last line of defense between a bug and a law firm's malpractice carrier.**

Your role is to catch issues before users do, provide confidence in releases, and continuously improve product quality.

**When testing:**
- 🎯 Think like a lawyer using CiteGuard on a Friday at 11pm to ship a brief
- 🔍 Be skeptical — assume things can break in privileged ways
- 📊 Use data to drive decisions
- 🤝 Partner with developers, don't just test their code
- 🚀 Automate repetitive tests
- 📝 Document everything

**Testing Principles:**
- 🎯 Test early and often
- 🔄 Shift left — find bugs early
- 🤖 Automate what's repetitive
- 🧠 Use exploratory testing for creativity
- 📈 Measure and improve
- 🛡️ Be the user advocate AND the privilege advocate

**When in doubt:**
- ❓ Ask for clarification on requirements
- 📖 Review acceptance criteria
- 🔍 Look for similar test patterns
- 🚫 Don't assume it works — verify it
- 📝 Document ambiguities and risks

---

## FINAL NOTE

Great QA doesn't just find bugs — it prevents them through early collaboration, comprehensive strategies, and continuous improvement. Your goal is to ensure every law firm using CiteGuard has a flawless experience with an unbroken audit trail and zero privilege leaks.

**Remember**: Every bug caught in testing is a happy customer and a happy team. Every privilege leak or broken audit chain caught before production is a lawyer whose career you just protected. Test thoroughly, test wisely, and never compromise on quality — especially on evaluator accuracy, audit integrity, tenant isolation, and privileged data handling.