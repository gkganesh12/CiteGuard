# Architecture Decision Record (ADR)

**Status: Accepted**

## ADR-0004: Tenant Isolation Strategy

### Decision

We have decided to enforce multi-tenant isolation by deriving **`firm_id` exclusively from the authenticated session** (Clerk JWT), never from request body or URL parameters. All tenant-scoped queries are routed through a **`BaseRepository[T]`** abstract class that requires `firm_id` on every method. Cross-tenant access attempts return **404 (not 403)** to prevent existence disclosure.

### Context

- CiteGuard processes privileged attorney-client material. A tenant isolation failure — where Firm A can see Firm B's data — is an existential risk. It could cause privilege waivers, malpractice exposure, bar complaints, and regulatory action.
- The `firm_id` must be tamper-proof: if it comes from the request body or URL, an attacker can substitute another firm's ID. Deriving it from the authenticated session (server-verified JWT) eliminates this attack vector.
- Returning 403 ("Forbidden") on cross-tenant access attempts discloses that the resource exists but belongs to another firm. Returning 404 ("Not Found") reveals nothing about the resource's existence.
- Every developer touching tenant-scoped code must find it impossible to accidentally forget `firm_id` filtering. The repository pattern makes omission a compile-time (or at minimum, a test-time) error rather than a silent bug.
- Admin and analytics features that legitimately need cross-firm data require a separate, explicitly approved code path.

### Rationale

#### firm_id from Authenticated Session
- The Clerk JWT contains the user's `firm_id` in its claims, verified by the server on every request.
- The `get_current_user` FastAPI dependency extracts `firm_id` from the JWT and makes it available to all downstream code.
- Since `firm_id` never comes from user-controlled input (request body, URL, query params), request forgery attacks cannot alter tenant context.

#### 404 Instead of 403
- A 403 response tells an attacker "this resource exists, but you don't have access." This leaks information about other firms' data.
- A 404 response is indistinguishable from "this resource doesn't exist at all," preventing existence probing.
- This is a standard security practice for multi-tenant SaaS applications handling sensitive data.

#### BaseRepository Pattern
- The `BaseRepository[T]` abstract class requires `firm_id` as a parameter on every query method: `get()`, `list()`, `create()`, `update()`, `delete()`.
- Every concrete repository (DocumentRepository, FlagRepository, etc.) inherits from BaseRepository and includes `WHERE firm_id = :firm_id` in every query.
- This makes it structurally impossible to write a tenant-scoped query without providing `firm_id`. The omission is a method signature violation, not a logic bug.

#### CI Lint for Missing firm_id
- A CI grep lint rule scans all raw SQL and ORM queries on tenant-scoped tables and flags any that do not include a `firm_id` filter.
- This catches edge cases where developers bypass the repository pattern (e.g., raw SQL for performance optimization or one-off scripts).

### Implementation Details

#### get_current_user Dependency
- **Location**: FastAPI dependency, injected into all authenticated endpoints.
- **Behavior**: Decodes and verifies the Clerk JWT, extracts `user_id` and `firm_id` from claims, and returns a `CurrentUser` dataclass.
- **Failure modes**: Invalid JWT returns 401. Missing `firm_id` claim returns 401 (misconfigured account).
- **Usage**: `current_user: CurrentUser = Depends(get_current_user)` on every endpoint.

#### BaseRepository[T] Abstract Class
- **Generic type parameter**: `T` is the SQLAlchemy model class.
- **Required methods** (all take `firm_id: UUID` as first parameter after `self`):
  - `get(firm_id, entity_id) -> T | None`: Returns entity if it belongs to the firm, else None.
  - `list(firm_id, filters, pagination) -> list[T]`: Returns paginated list filtered by firm.
  - `create(firm_id, data) -> T`: Creates entity with firm_id set.
  - `update(firm_id, entity_id, data) -> T | None`: Updates entity if it belongs to the firm, else None.
  - `delete(firm_id, entity_id) -> bool`: Soft-deletes entity if it belongs to the firm, else False.
- **Endpoint pattern**: When `get()` or `update()` returns None, the endpoint returns 404.

#### Tenant Isolation Test Suite
- **Setup**: Each test creates data for two firms (Firm A and Firm B) with separate users and documents.
- **Assertions**:
  - Firm A user accessing Firm A documents: 200 with correct data.
  - Firm A user accessing Firm B document IDs: 404 (not 403).
  - Firm A user listing documents: returns only Firm A documents (zero Firm B documents).
  - Firm A user creating a document: `firm_id` is set from session, not from request body.
  - If request body includes a `firm_id` field, it is ignored (session `firm_id` takes precedence).
- **Coverage**: Every tenant-scoped endpoint has at least one cross-tenant isolation test.

#### Admin/Analytics Cross-Firm Access
- Cross-firm queries are NOT allowed through the standard BaseRepository.
- A separate `AdminAnalyticsService` with its own repository exists for cross-firm aggregation (e.g., platform-wide metrics).
- This service requires:
  - An explicit ADR approving the specific cross-firm query.
  - A dedicated admin role check (not just any authenticated user).
  - Aggregation-only access (no individual document content).
  - Audit log entry for every cross-firm query.

#### CI Lint Configuration
- **Rule**: Grep for SQLAlchemy queries or raw SQL on tenant-scoped tables (`documents`, `flags`, `reviewer_actions`, `audit_log`, `exports`, `users`, `api_keys`) that do not include `firm_id` in the WHERE clause.
- **Exceptions**: Migration files, test fixtures, and the AdminAnalyticsService (which has its own ADR).
- **Enforcement**: CI fails if any violations are found.

### Consequences

**Positive:**
- Impossible to forget firm_id: the BaseRepository pattern makes tenant scoping a structural requirement, not a convention.
- Existence not disclosed: 404 responses prevent cross-tenant information leakage.
- Tamper-proof tenant context: firm_id from JWT cannot be forged by request manipulation.
- Testable isolation: dedicated test suite verifies cross-tenant access returns 404 for every endpoint.
- Defense in depth: session-level firm_id + repository pattern + CI lint + test suite provides four layers of protection.

**Challenges:**
- Adds boilerplate to every query: every repository method takes `firm_id` as a required parameter, even when it feels redundant. This is intentional — the boilerplate is the safety mechanism.
- Makes debugging harder: developers cannot easily query across firms without the AdminAnalyticsService. This is also intentional — convenience must not compromise isolation.
- Admin analytics require separate code path: legitimate cross-firm queries (platform metrics, usage analytics) need their own service with explicit ADR approval, which adds development overhead.
- CI lint may produce false positives: raw SQL in comments or strings may trigger the lint rule. Whitelist patterns handle known false positives.

---

**Related Documents:**
- `docs/PRD_v1.md` — V1 product requirements (tenant isolation as non-negotiable)
- `adr/0002-database-schema.md` — firm_id on every tenant-scoped table
- `adr/0003-audit-log-hash-chain.md` — audit log scoped by firm_id
- `RnR/citeguard_backend_guidelines.md` — backend coding standards
- `RnR/citeguard_qa_rules.md` — testing requirements for tenant isolation
