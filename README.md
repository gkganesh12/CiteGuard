<p align="center">
  <img src="https://img.shields.io/badge/CiteGuard-AI%20Verification-1a1a1a?style=for-the-badge" alt="CiteGuard" />
</p>

<h1 align="center">CiteGuard</h1>

<p align="center">
  <strong>The verification layer for AI-generated legal documents.</strong><br/>
  5 deterministic evaluators. Zero AI in the verification loop. Tamper-evident audit trails.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=next.js&logoColor=white" alt="Next.js 15" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/TypeScript-5.6-3178c6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169e1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License" />
</p>

---

## The Problem

Lawyers are using AI (ChatGPT, Claude, Harvey, Casetext) to draft briefs and motions. These models hallucinate — they invent case citations that don't exist, fabricate quotes, and name judges who never served on a court. When hallucinated content reaches a courtroom, attorneys face sanctions, malpractice liability, and bar complaints.

Asking another LLM to verify the first one doesn't work. LLMs don't have access to truth — they have access to probability distributions over tokens.

## The Solution

CiteGuard sits between AI tools and lawyer review. It runs **5 deterministic evaluators** against **real-world authoritative databases** and returns structured verification results in under 3 seconds. No AI in the verification loop.

```
Your AI Tool ──→ CiteGuard API ──→ 5 Evaluators (parallel)
                      │                   │
                      ▼                   ▼
                  Audit Log ←──── Flags Created
                  (SHA-256 chain)       │
                                        ▼
                                Review Queue (UI)
                                [A] [O] [R] [D]
                                        │
                                        ▼
                                Audit PDF Export
```

---

## Evaluators

| # | Evaluator | What It Checks | Source | Severity |
|---|-----------|---------------|--------|----------|
| 1 | **Citation Existence** | Is this case citation real? | CourtListener (8M+ opinions) | CRITICAL if fake |
| 2 | **Quote Verification** | Did the court actually say this? | Fuzzy match against opinion text (85% threshold) | CRITICAL if fabricated |
| 3 | **Judge Verification** | Did this judge serve on this court? | FJC Biographical Directory | CRITICAL if fake |
| 4 | **Bluebook Format** | Is the citation formatted correctly? | 500+ rules, 21st edition | MEDIUM / HIGH |
| 5 | **Temporal Validity** | Has this case been overruled? | Citation graph analysis | CRITICAL / HIGH |

All evaluators are:
- **Deterministic** — same input always produces the same flags
- **Versioned** — every logic change bumps the version number
- **Independent** — each runs in isolation, failures produce ADVISORY flags (not crashes)
- **Regression-tested** — mandatory corpus test (50 hallucinations + 50 clean docs) before any change ships

---

## Features

### Verification Engine
- 5 parallel evaluators, sub-3-second p95 latency
- Structured flag output with severity, confidence scores, character offsets, and suggested corrections
- Circuit breakers on all external API calls — external failures produce advisory flags, not errors
- SDK + REST API for pipeline integration

### Audit Trail
- SHA-256 hash-chained append-only log
- Every state-changing action recorded in the same database transaction
- Daily chain integrity verification
- Tamper-evident PDF exports with cryptographic proof of due diligence
- 7-year minimum retention

### Review Interface
- Keyboard-first workflow: `J`/`K` navigate, `A` approve, `O` override, `R` reject, `D` defer
- Severity-coded highlights mapped to exact character offsets in the document
- Override requires written justification (minimum 10 characters, logged in audit chain)
- Finalize only when all flags are resolved

### Multi-Tenancy
- `firm_id` scoping enforced at the database query level from authenticated sessions
- Cross-firm requests return 404 (not 403) to prevent existence disclosure
- Complete data isolation — Firm A cannot see, probe, or infer Firm B's data

### Severity System
- **CRITICAL** (red) — citation/quote/judge may be fabricated
- **HIGH** (orange) — serious issue requiring attention
- **MEDIUM** (amber) — formatting or minor issues
- **ADVISORY** (blue) — informational, no action needed
- Always conveyed as color + icon + text (never color alone, never green)

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Workers | ARQ + Redis 7 |
| Auth | Clerk (JWT verification) |
| Citation Parsing | eyecite |
| Fuzzy Matching | rapidfuzz |
| PDF Export | WeasyPrint |
| Payments | Stripe |
| Observability | structlog + Sentry |
| Linting | Ruff + mypy (strict) |
| Testing | pytest + pytest-asyncio (80% coverage target) |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript 5.6 (strict) |
| Runtime | React 19 |
| Styling | Tailwind CSS 3.4 |
| Auth | Clerk (@clerk/nextjs) |
| Data Fetching | TanStack React Query 5 |
| Animation | GSAP |
| Icons | Lucide React |
| Testing | Vitest + Playwright |

---

## Project Structure

```
CiteGuard/
├── frontend/                       # Next.js 15 application
│   ├── app/
│   │   ├── page.tsx                # Landing page
│   │   ├── (auth)/                 # Sign-in / Sign-up (Clerk)
│   │   └── (authenticated)/        # Protected routes
│   │       ├── dashboard/          # Document submission + stats
│   │       ├── queue/              # Review queue with filters
│   │       ├── audit/              # Audit exports
│   │       ├── documents/[id]/     # Keyboard-first review interface
│   │       └── firm/               # Team, API keys, settings, billing
│   ├── components/common/          # Shared components
│   └── lib/                        # Utilities
│
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── main.py                 # API entry point
│   │   ├── config.py               # Settings (env-based)
│   │   ├── models/                 # SQLAlchemy models (8 tables)
│   │   ├── documents/              # Document submission & retrieval
│   │   ├── evaluators/             # 5 deterministic evaluators
│   │   │   ├── base.py             # IEvaluator protocol + FlagResult
│   │   │   ├── citation_existence.py
│   │   │   ├── quote_verification.py
│   │   │   ├── judge_verification.py
│   │   │   ├── bluebook_format.py
│   │   │   ├── temporal_validity.py
│   │   │   └── orchestrator.py     # Parallel execution
│   │   ├── flags/                  # Flag management + reviewer actions
│   │   ├── audit/                  # AuditLogService (append-only, hash-chained)
│   │   ├── firms/                  # Firm (tenant) management
│   │   ├── integrations/           # CourtListener, FJC, Stripe clients
│   │   ├── workers/                # ARQ background jobs
│   │   └── db/                     # Database + Alembic migrations
│   └── tests/                      # pytest test suite
│
├── docs/                           # Product requirements
│   ├── PRD_v1.md                   # V1 scope (source of truth)
│   ├── PRD_v2.md                   # Future work
│   └── Spec_doc.md                 # Original product spec
│
├── adr/                            # Architecture Decision Records
│   ├── 0001-tech-stack.md
│   ├── 0002-database-schema.md
│   ├── 0003-audit-log-hash-chain.md
│   ├── 0004-tenant-isolation.md
│   ├── 0005-evaluator-architecture.md
│   ├── 0006-authentication.md
│   ├── 0007-privileged-data-handling.md
│   ├── 0008-external-api-integration.md
│   └── 0009-ci-cd-pipeline.md
│
├── arc_diagrams/                   # Mermaid architecture diagrams
│   ├── backend/                    # System overview, data model, evaluator pipeline, auth, audit
│   └── frontend/                   # App routes, state management
│
├── RnR/                            # Role & responsibility guidelines
│   ├── citeguard_backend_guidelines.md
│   ├── citeguard_frontend_guidelines.md
│   ├── citeguard_project_management_rules.md
│   ├── citeguard_pm_rules.md
│   └── citeguard_qa_rules.md
│
└── template/                       # ADR, feature, QA, task templates
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.12+
- Docker & Docker Compose
- [Clerk](https://clerk.com) account (authentication)
- [CourtListener](https://www.courtlistener.com/api/) API token

### Backend Setup

```bash
# Start PostgreSQL and Redis
cd backend
docker compose up -d postgres redis

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000

# In a separate terminal — start the worker
arq app.workers.arq_app.WorkerSettings
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your Clerk keys and API URL

# Start the development server
npm run dev
```

The app will be available at `http://localhost:3000`.

### Docker (Full Stack)

```bash
cd backend
docker compose up
```

This starts PostgreSQL, Redis, the API server, and the worker.

---

## API Usage

### Verify a Document

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "In Smith v. Jones, 123 F.3d 456 (9th Cir. 2019), the court held...",
    "document_type": "brief"
  }'
```

### Response

```json
{
  "document_id": "01HXYZ...",
  "status": "evaluated",
  "flags": [
    {
      "id": "01HXYZ...",
      "evaluator": "citation_existence",
      "evaluator_version": "1.0.0",
      "severity": "CRITICAL",
      "confidence": 0.95,
      "explanation": "Citation '123 F.3d 456 (9th Cir. 2019)' does not match any opinion in CourtListener.",
      "start_offset": 22,
      "end_offset": 54,
      "suggested_correction": null
    }
  ],
  "summary": {
    "critical": 1,
    "high": 0,
    "medium": 0,
    "advisory": 0
  }
}
```

### Health Check

```bash
curl http://localhost:8000/healthz     # Liveness
curl http://localhost:8000/readyz      # Readiness (DB + Redis)
```

---

## Database Schema

```
firms ──────────── users
  │                  │
  ├── documents ─────┤
  │     │            │
  │     ├── flags    │
  │     │     │      │
  │     │     └── reviewer_actions
  │     │
  │     └── exports
  │
  ├── api_keys
  │
  └── audit_log (append-only, hash-chained)
```

All tables are scoped by `firm_id`. The `audit_log` table has database-level restrictions: `UPDATE` and `DELETE` are revoked at the role level.

---

## Architecture Decisions

All significant decisions are documented as ADRs in `adr/`:

| ADR | Decision |
|-----|----------|
| [0001](adr/0001-tech-stack.md) | Tech stack selection (FastAPI + Next.js + PostgreSQL) |
| [0002](adr/0002-database-schema.md) | Database schema design |
| [0003](adr/0003-audit-log-hash-chain.md) | SHA-256 hash-chained audit log |
| [0004](adr/0004-tenant-isolation.md) | Multi-tenant isolation strategy |
| [0005](adr/0005-evaluator-architecture.md) | Evaluator interface and versioning |
| [0006](adr/0006-authentication.md) | Clerk-based authentication |
| [0007](adr/0007-privileged-data-handling.md) | Privileged data scrubbing |
| [0008](adr/0008-external-api-integration.md) | External API resilience patterns |
| [0009](adr/0009-ci-cd-pipeline.md) | CI/CD pipeline design |

---

## Scripts

### Backend

```bash
pytest                              # Run tests
pytest -m tenant_isolation          # Run tenant isolation tests
pytest -m corpus                    # Run evaluator corpus tests
pytest --cov=app --cov-fail-under=80  # Coverage check
mypy app/                           # Type checking
ruff check app/                     # Linting
ruff format app/                    # Formatting
alembic upgrade head                # Run migrations
alembic revision --autogenerate -m "description"  # Create migration
```

### Frontend

```bash
npm run dev                         # Development server
npm run build                       # Production build
npm run lint                        # ESLint
npm run type-check                  # TypeScript check
npm run test                        # Vitest unit tests
npm run test:e2e                    # Playwright e2e tests
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `CLERK_SECRET_KEY` | Yes | Clerk API secret key |
| `CLERK_JWKS_URL` | Yes | Clerk JWKS endpoint |
| `CLERK_ISSUER` | Yes | Clerk issuer URL |
| `COURTLISTENER_API_TOKEN` | Yes | CourtListener API token |
| `STRIPE_SECRET_KEY` | Yes | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |
| `SENTRY_DSN` | No | Sentry error tracking DSN |
| `S3_BUCKET_NAME` | No | S3 bucket for PDF exports |
| `CORS_ORIGINS` | No | Allowed CORS origins (default: `["http://localhost:3000"]`) |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Yes | Clerk publishable key |

---

## Security

CiteGuard handles privileged attorney-client material. The following invariants are enforced at every layer:

- **No document content in logs** — Sentry event scrubbing removes `text`, `document_text`, `prompt`, `completion`, and `content` fields before transmission
- **Append-only audit log** — Database role permissions revoke `UPDATE` and `DELETE` on `audit_log`
- **Tenant isolation** — Every query is scoped by `firm_id` from the authenticated session, never from request parameters
- **Existence disclosure prevention** — Cross-firm requests return 404, not 403
- **Hash-chain integrity** — Daily verification, any break is a P0 incident
- **Non-root containers** — Docker images run as unprivileged user `citeguard`
- **Rate limiting** — 100 documents/minute sustained, 200 burst; 10 auth attempts/minute

---

## Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| **V1** | 5 evaluators, review queue, audit trail, SDK, billing | In Progress |
| **V1.1** | State court support, bulk upload, enhanced Bluebook | Planned |
| **V1.2** | Opposing authority detection, PII/privilege scanning | Planned |
| **V2** | Custom evaluators, LLM-as-judge, SSO/SAML, on-prem | Future |

See [docs/PRD_v1.md](docs/PRD_v1.md) for the complete V1 specification.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Read the relevant docs (see `CLAUDE.md` section 3 for which docs apply to your change)
4. If making an architectural decision, create an ADR first (`cp template/adr-template.md adr/NNNN-slug.md`)
5. Write tests alongside your code (see `RnR/citeguard_qa_rules.md`)
6. Ensure all checks pass (`pytest`, `mypy`, `ruff`, `npm run lint`, `npm run type-check`)
7. Submit a pull request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>AI writes the brief. CiteGuard makes sure it's not lying.</sub>
</p>
