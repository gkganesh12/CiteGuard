# Architecture Decision Record (ADR)

**Status: Accepted**

## ADR-0006: Authentication and Authorization

### Decision

We have decided to use Clerk for user authentication (JWT via JWKS), bcrypt-hashed API keys for SDK/proxy authentication, and RBAC with three roles (admin, reviewer, submitter) for authorization. Rate limiting is set at 100 req/min/firm for document submissions.

### Context

CiteGuard needs two authentication paths: interactive users (web dashboard) and programmatic access (SDK/proxy). All access must be scoped to a firm. Roles control who can review, finalize, and manage the workspace.

- CiteGuard processes privileged attorney-client material, making authentication and authorization critical to preventing unauthorized access.
- Interactive users authenticate through the web dashboard using standard identity provider flows (Google OAuth, email/password).
- Programmatic access (SDK, proxy integrations) requires a separate credential mechanism that does not depend on browser sessions.
- Authorization must enforce firm-level scoping and role-based permissions to match law firm hierarchies (managing partner, senior associate, junior associate).
- Rate limiting is necessary to prevent abuse and protect shared infrastructure across tenants.

### Rationale

#### Authentication Provider (Clerk)
- Clerk provides Google OAuth, email/password, and email verification out of the box, eliminating the need to build and maintain custom auth infrastructure.
- Clerk handles password policy enforcement (min 12 chars, require 3 of {upper, lower, digit, symbol}, Argon2id hashing) without custom implementation.
- JWT-based authentication via JWKS endpoint allows stateless verification with automatic public key rotation.
- Faster time-to-ship for a solo founder compared to rolling a custom auth system.

#### API Key Authentication
- API keys provide a stateless credential for SDK/proxy access that does not require browser-based OAuth flows.
- bcrypt hashing of stored keys ensures that a database compromise does not expose plaintext credentials.
- Prefix convention (`cg_live_...` / `cg_test_...`) makes it easy to distinguish environments and audit key usage.
- Plaintext shown once at creation, never again — follows industry best practice (Stripe, GitHub).

#### RBAC with Three Roles
- Three roles (admin, reviewer, submitter) map directly to law firm hierarchy: managing partner = admin, senior associate = reviewer, junior associate = submitter.
- Minimal role set reduces complexity while covering all V1 access patterns.
- Role is embedded in JWT claims, enabling endpoint-level authorization without additional database lookups.

### Implementation Details

#### JWT Verification
- **JWKS Endpoint**: Clerk publishes rotating public keys; `get_current_user` FastAPI dependency fetches and caches these keys.
- **JWT Claims**: Each token includes `user_id`, `firm_id`, and `role`.
- **Session Expiry**: JWT with 24h expiry, refresh token with 30-day expiry.
- **FastAPI Dependency**: `get_current_user` verifies JWT signature, checks expiry, and extracts claims into the request context.

#### Role-Based Authorization
- **Dependency Factory**: `require_role(role)` returns a FastAPI dependency that checks the authenticated user's role against the required role.
- **Role Hierarchy**: admin > reviewer > submitter. Higher roles inherit permissions of lower roles.
- **Endpoint Mapping**: Document submission requires submitter+. Review/finalize requires reviewer+. Firm settings, user management, and API key management require admin.

#### API Key Authentication
- **Format**: `cg_live_` or `cg_test_` prefix + 32-byte random value, base62 encoded.
- **Storage**: bcrypt hash of the key stored in the database. Plaintext displayed once at creation.
- **Lookup**: Hash incoming key with bcrypt, compare against stored hashes.
- **Performance Mitigation**: Redis cache of recently validated key hashes to avoid repeated bcrypt comparisons on every request.

#### Rate Limiting
- **Document Submission**: 100 req/min/firm (burst 200).
- **Auth Endpoints**: 10 req/min to prevent credential stuffing.
- **Response**: HTTP 429 with `Retry-After` header indicating seconds until the limit resets.
- **Implementation**: Redis-backed sliding window counter keyed by `firm_id`.

### Consequences

**Positive:**
- Fast to ship: Clerk handles password policy, OAuth, email verification, and key rotation out of the box.
- Google OAuth included: Firms can use existing Google Workspace accounts without additional setup.
- Handles password policy: Argon2id hashing, complexity requirements, and brute-force protection managed by Clerk.
- Stateless JWT verification: No session store required for interactive auth; scales horizontally.
- Firm-scoped rate limiting: Prevents any single firm from degrading service for others.

**Challenges:**
- Clerk dependency: Vendor lock-in on a critical path. If Clerk has an outage, no interactive user can authenticate. Mitigation: evaluate WorkOS or Auth0 as fallback options; keep JWT verification logic abstracted behind an interface.
- Enterprise SAML: Clerk does not natively support SAML/SCIM for enterprise SSO. May need to migrate to WorkOS in V2 for firms requiring SAML. Mitigation: abstract auth provider behind a service interface to ease future migration.
- API key bcrypt comparison is slow: Each bcrypt comparison takes ~100ms. Mitigation: Redis cache of recently validated key hashes (TTL 5 min), so repeat requests within the window skip bcrypt.
- API key revocation latency: Cached valid key hashes mean a revoked key may remain valid for up to 5 minutes. Mitigation: on revocation, explicitly delete the cache entry.

---

**Date:** 2026-04-18
**Supersedes:** None
**Related ADRs:** ADR-0007 (Privileged Data Handling)
