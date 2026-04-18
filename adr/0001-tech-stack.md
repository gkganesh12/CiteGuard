# Architecture Decision Record (ADR)

**Status: Accepted**

## ADR-0001: Tech Stack Selection

### Decision

We have decided to use **Python 3.12/FastAPI** for the backend, **Next.js 14/TypeScript/Tailwind CSS/shadcn/ui** for the frontend, **PostgreSQL 16** for the primary database, **Redis + Arq** for the job queue, **ClickHouse Cloud** for traces and telemetry, **Clerk** for authentication, **Stripe** for payments, **Fly.io** for backend hosting, **Vercel** for frontend hosting, and **Cloudflare** for CDN/WAF.

### Context

- CiteGuard is an AI verification and audit platform for U.S. law firms that processes privileged legal content and produces compliance artifacts (audit PDFs with hash-chained integrity).
- The platform needs fast iteration speed suitable for a solo-founder team while maintaining production-grade reliability for legal compliance.
- Mature legal ML and NLP libraries are essential for evaluator accuracy (citation parsing, quote verification, Bluebook formatting).
- The primary database must provide ACID guarantees for the append-only, hash-chained audit log — the core product artifact.
- A cost-efficient trace store is needed for high-cardinality telemetry data without blowing up infrastructure costs.
- Hosting must be solo-founder-friendly: minimal DevOps overhead, fast deploys, and reasonable cost at low-to-moderate scale.

### Rationale

#### Backend: Python 3.12 / FastAPI
- Python has the best ecosystem for legal NLP: `eyecite` for citation extraction, `rapidfuzz` for fuzzy quote matching, and mature ML libraries for future evaluator enhancements.
- FastAPI is async-first, provides automatic OpenAPI schema generation, and has excellent Pydantic v2 integration for request/response validation.
- Python 3.12 offers significant performance improvements and better error messages for developer productivity.

#### Frontend: Next.js 14 / TypeScript / Tailwind CSS / shadcn/ui
- Next.js 14 App Router with React Server Components provides optimal performance for the document review interface.
- TypeScript strict mode catches type errors at compile time, critical for a compliance product.
- Tailwind CSS enables rapid UI development with a custom severity color palette (CRITICAL=red, HIGH=orange, MEDIUM=amber, ADVISORY=blue).
- shadcn/ui provides accessible, unstyled component primitives that can be customized to CiteGuard's professional, no-emoji design language.

#### Database: PostgreSQL 16
- ACID guarantees are non-negotiable for the audit log hash chain — partial writes or read anomalies would break chain integrity.
- PostgreSQL 16 offers JSONB for flexible evaluator output storage, composite indexes for tenant-scoped queue queries, and mature RLS support.
- Strong ecosystem for migrations (Alembic), monitoring, and backups.

#### Job Queue: Redis + Arq
- Arq is a lightweight async job queue built on Redis, significantly simpler than Celery for a small team.
- Redis also serves as the caching layer, reducing infrastructure components.
- Sufficient throughput for V1 document processing volumes.

#### Telemetry: ClickHouse Cloud
- Cost-efficient storage for high-cardinality trace data (per-evaluator timing, per-document metrics).
- Column-oriented storage provides fast analytical queries on telemetry without impacting the primary Postgres database.
- Cloud-managed version eliminates operational overhead.

#### Auth: Clerk
- Fast integration for authentication, including magic links, social login, and JWT-based sessions.
- Provides firm_id extraction from JWT for tenant isolation.
- Acceptable trade-off: may not support enterprise SAML at scale, but suitable for V1 and can be migrated later.

#### Payments: Stripe
- Industry standard for SaaS billing with excellent documentation and webhook reliability.

#### Hosting: Fly.io (backend) + Vercel (frontend) + Cloudflare (CDN/WAF)
- Fly.io provides container-based hosting with global edge deployment, suitable for FastAPI apps.
- Vercel is the canonical hosting platform for Next.js with zero-config deploys.
- Cloudflare provides CDN, DDoS protection, and WAF in front of both services.

### Implementation Details

#### Backend Stack
- **Runtime**: Python 3.12 with `pyproject.toml` for dependency management
- **Framework**: FastAPI with Pydantic v2 for request/response validation
- **ORM**: SQLAlchemy 2.0 async with typed models
- **Migrations**: Alembic with auto-generation from SQLAlchemy models
- **Job Queue**: Arq workers connected to Redis
- **Testing**: pytest with pytest-asyncio, httpx for API tests

#### Frontend Stack
- **Framework**: Next.js 14 App Router with React Server Components
- **Language**: TypeScript in strict mode (`"strict": true` in tsconfig)
- **Styling**: Tailwind CSS with custom severity palette (no green for severity)
- **Components**: shadcn/ui primitives, customized for professional legal UI
- **State Management**: Zustand for client state (no persist for privileged data)
- **API Client**: Generated from OpenAPI schema

#### Infrastructure
- **Primary DB**: PostgreSQL 16 on Fly.io (or managed provider)
- **Cache/Queue**: Redis on Fly.io (or Upstash for managed)
- **Telemetry DB**: ClickHouse Cloud
- **Auth Provider**: Clerk (JWT-based, firm_id in claims)
- **Payments**: Stripe with webhook verification
- **CDN/WAF**: Cloudflare in front of both Fly.io and Vercel origins

### Consequences

**Positive:**
- Fast iteration speed: Python + FastAPI + Next.js is a well-documented, widely-adopted stack with strong community support.
- Mature legal NLP ecosystem: eyecite, rapidfuzz, and Python ML libraries give evaluators a strong foundation.
- Cost-efficient at V1 scale: Fly.io + Vercel + Cloudflare is affordable for low-to-moderate traffic.
- Strong type safety: Pydantic v2 on backend + TypeScript strict on frontend catches errors early.
- ACID guarantees: PostgreSQL 16 provides the reliability needed for the hash-chained audit log.

**Challenges:**
- Fly.io is a smaller hosting provider: less battle-tested at enterprise scale than AWS/GCP, but sufficient for V1 and migration is straightforward.
- Clerk may not scale to enterprise SAML requirements: plan for auth provider migration path if large firms require SSO/SCIM.
- Two hosting providers to manage: Fly.io for backend and Vercel for frontend adds operational surface area, but both are low-ops platforms.
- Python GIL limits CPU-bound parallelism: mitigated by async I/O for evaluator fan-out and Arq workers for CPU-heavy tasks.

**Migration Considerations:**
- Auth migration from Clerk to a self-hosted solution (e.g., Keycloak) should be planned for V2 if enterprise SAML is needed.
- Backend hosting migration from Fly.io to AWS/GCP is straightforward since FastAPI runs in standard containers.
- ClickHouse Cloud can be replaced with self-hosted ClickHouse if cost becomes a concern at scale.

---

**Related Documents:**
- `docs/PRD_v1.md` — V1 product requirements
- `RnR/citeguard_backend_guidelines.md` — backend coding standards
- `RnR/citeguard_frontend_guidelines.md` — frontend coding standards
