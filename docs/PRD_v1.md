# CiteGuard V1 — Product Requirements Document

| | |
|---|---|
| **Document status** | DRAFT v0.1 |
| **Product** | CiteGuard |
| **Release** | V1 (MVP / Public Launch) |
| **Target launch** | Week 12 from project start |
| **Owner** | Founder |
| **Last updated** | Day 0 |

---

## 1. Executive Summary

CiteGuard V1 is an AI verification and audit platform for U.S. law firms. It sits between a firm's AI tools (Claude, Harvey, Casetext, internal RAG) and the lawyer reviewing the output. On every AI-generated document, V1 runs five deterministic verification checks, surfaces issues in a review queue, and produces a tamper-evident audit trail exportable as a PDF.

V1's job is narrow and deliberate: catch the five highest-frequency, highest-severity failure modes of legal AI output (hallucinated citations, fabricated quotes, fake judges, bad citation format, and stale precedent) for **federal case law**, and prove that the audit record is compliant-grade. State law, advanced evaluators, and complex orchestration are explicitly deferred to V1.1+.

---

## 2. Problem Statement

Lawyers using generative AI for drafting face a real, quantifiable risk of bar sanctions, malpractice exposure, and reputation damage from AI hallucinations that reach filed documents. The reference case (*Mata v. Avianca*, 2023) sanctioned a lawyer $5,000 and sparked 40+ subsequent published opinions on lawyer AI misuse. Existing horizontal AI observability tools (Braintrust, LangSmith, Galileo) do not know how to verify legal content; existing legal AI platforms (Harvey, Casetext) produce the outputs but have a conflict-of-interest in flagging their own errors.

**No tool today:**
- Verifies AI-generated legal citations against a ground-truth database
- Verifies that quoted language actually appears in cited opinions
- Produces a tamper-evident audit record suitable for bar-compliance evidence
- Works across multiple AI providers (provider-agnostic)

---

## 3. V1 Goals & Non-Goals

### 3.1 Goals (in scope)

| # | Goal |
|---|------|
| G1 | Accept AI-generated legal text via SDK or HTTP proxy |
| G2 | Run 5 deterministic evaluators on federal U.S. case law references |
| G3 | Surface issues in a priority-sorted review queue with approve/override/reject actions |
| G4 | Produce a cryptographically verifiable PDF audit export per document |
| G5 | Support 3+ paying firms by end of V1 (public launch) |
| G6 | Achieve <3 second p95 end-to-end evaluation latency for briefs up to 20 pages |

### 3.2 Non-Goals (explicitly OUT of V1 scope — deferred to V1.1+)

| # | Non-goal |
|---|----------|
| NG1 | State-level case law or statute coverage (federal only in V1) |
| NG2 | LLM-as-judge evaluators (Holding Accuracy) |
| NG3 | PII/privilege scanning |
| NG4 | Opposing authority detection |
| NG5 | Jurisdiction-match logic |
| NG6 | Statutory currency checks |
| NG7 | SSO/SAML (use email+password + Google OAuth only) |
| NG8 | On-premise / self-hosted deployment |
| NG9 | Multi-language support (English only) |
| NG10 | Customer-defined custom evaluators |
| NG11 | Mobile app |
| NG12 | Integration marketplace (Zapier, etc.) |

---

## 4. Success Metrics

### 4.1 Primary metrics (must hit for V1 to be considered successful)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Paying firms at launch (week 12) | ≥ 3 | Stripe dashboard |
| MRR at launch | ≥ $5,000 | Stripe dashboard |
| p95 evaluation latency | < 3,000 ms | Application telemetry |
| Evaluator true-positive rate on seeded hallucinations | ≥ 95% | Internal test corpus of 100 seeded cases |
| Evaluator false-positive rate | < 5% | Reviewer override rate on genuine citations |
| Uptime (week 10–12) | ≥ 99.5% | Uptime monitoring |

### 4.2 Secondary metrics (indicators, track but do not gate launch)

- Documents verified per firm per week
- Reviewer throughput (flags reviewed per lawyer-hour)
- Audit export download rate
- Time-to-first-document for new customers

---

## 5. Target Users & Personas

### 5.1 Ideal Customer Profile (ICP)

- **Firm size:** 20–200 attorneys
- **Practice area:** Litigation-heavy (personal injury, commercial litigation, insurance defense, family law)
- **AI adoption:** Already using at least one AI tool for drafting (Claude, Harvey, CoCounsel, internal GPT wrapper, etc.)
- **Geography (V1):** United States, federal practice focus
- **Buyer role:** Managing Partner, General Counsel, or Chair of Risk/Ethics Committee

### 5.2 Personas

**P1: Managing Partner Margaret (Economic Buyer)**
- 52 years old, partner at 80-lawyer commercial litigation firm
- Has heard about *Mata v. Avianca* and is personally afraid of it happening at her firm
- Signs the contract and approves the budget
- Success criteria: "Nothing embarrassing reaches a judge. I can prove to our malpractice carrier we have controls."

**P2: Litigation Associate Dana (End User — Creator)**
- 28 years old, third-year associate
- Uses Claude daily to draft first passes of briefs
- Doesn't want to manually check every citation
- Success criteria: "Tell me what's wrong in my draft fast, so I can fix it before partner review."

**P3: Senior Associate Raj (End User — Reviewer)**
- 35 years old, senior associate who reviews junior drafts before partner review
- Currently spends 40+ minutes per brief just checking cites
- Success criteria: "Show me the flagged items in priority order. Let me approve or override in seconds."

**P4: IT Director Tom (Technical Buyer)**
- 45 years old, manages the firm's tech stack
- Concerned about data security and integration burden
- Success criteria: "Install must take <1 day. Must not break existing AI workflows. Must have an audit trail I can show in a SOC 2 review."

---

## 6. User Stories (V1)

### Epic 1: Capture AI-generated content
- **US-01** As a litigation associate, I want to submit my AI-generated draft to CiteGuard with one API call, so I don't slow down my drafting flow.
- **US-02** As an IT director, I want to configure a proxy endpoint that automatically captures all Claude calls, so my lawyers don't need to change their workflow.

### Epic 2: Detect hallucinations
- **US-03** As a senior associate, I want every citation in a draft verified against a real case database, so I know instantly which cites are fake.
- **US-04** As a senior associate, I want every quoted passage verified against the source opinion, so I catch fabricated quotes.
- **US-05** As a senior associate, I want to see if a cited case has been overturned, so I don't rely on bad precedent.
- **US-06** As a senior associate, I want to see if a named judge actually sat on the cited court, so I catch AI making up judge names.
- **US-07** As a senior associate, I want citation formatting checked against Bluebook rules, so briefs look professional.

### Epic 3: Review and resolve flags
- **US-08** As a senior associate, I want flagged issues sorted by severity, so I handle the highest-risk items first.
- **US-09** As a senior associate, I want to approve, override (with reason), or reject each flag in one click, so I move through queues fast.
- **US-10** As a managing partner, I want to see firm-wide flag statistics on a dashboard, so I understand our AI usage patterns.

### Epic 4: Produce compliant audit trails
- **US-11** As a managing partner, I want to export a PDF audit report per document, so I can demonstrate compliance to our malpractice carrier.
- **US-12** As a managing partner, I want the audit log to be tamper-evident, so the record holds up if a court questions it.

### Epic 5: Get alerted to high-risk issues
- **US-13** As a senior associate, I want a Slack notification when a Critical issue is flagged on a document assigned to me, so I don't miss it.

### Epic 6: Onboarding and team management
- **US-14** As an IT director, I want to create a firm workspace and invite team members, so our whole team uses it.
- **US-15** As a managing partner, I want to assign reviewer and admin roles, so access controls fit our firm structure.

---

## 7. V1 Feature Requirements (Detailed)

### F1 — Ingestion Layer

**REQ-F1.1** SDK support for Python 3.10+ and Node.js 18+. Install via pip/npm. Submission API is a single `citeguard.verify(document, metadata)` call.

**REQ-F1.2** HTTP REST proxy endpoint at `https://api.citeguard.ai/v1/llm/proxy`. Accepts OpenAI-compatible and Anthropic-compatible request payloads. Forwards to the upstream LLM, captures the response, and queues a verification job asynchronously.

**REQ-F1.3** Authentication via bearer API key (format: `cg_live_...` / `cg_test_...`). API keys scoped to a firm workspace.

**REQ-F1.4** Captured fields per submission:
- `id` (server-generated UUID)
- `firm_id`
- `user_id` (submitted by customer)
- `document_text` (raw)
- `prompt` (optional — if submitted via proxy, captured automatically)
- `llm_provider` + `llm_model`
- `timestamp_utc`
- `metadata` (free-form JSON, max 4KB)
- `document_type` (brief, memo, contract, other)

**REQ-F1.5** Rate limits: 100 requests / minute / firm (burst 200). Return 429 with `Retry-After` header on exceed.

**REQ-F1.6** Max document size: 200 KB of text per submission (≈30,000 words). Reject larger with HTTP 413.

**REQ-F1.7** Ingestion must be idempotent on a client-provided `idempotency_key` header.

**Acceptance:** Customer can install SDK in <10 minutes and submit first document. Proxy can be configured via one environment variable swap. All submissions appear in the dashboard within 10 seconds.

---

### F2 — Evaluator: Citation Existence

**REQ-F2.1** Parse all case citations from the submitted document using a citation parser (e.g., `eyecite` library, hardened). Support the five most common formats: Supreme Court (`410 U.S. 113`), Federal Reporter (`304 F.3d 451`), Federal Supplement, Federal Rules Decisions, and generic reporter cites.

**REQ-F2.2** For each parsed citation, resolve against the CourtListener `/api/rest/v3/opinions/` endpoint by volume/reporter/page.

**REQ-F2.3** Assign severity:
- `CRITICAL` — no matching opinion found (likely hallucination)
- `HIGH` — match found but case name in document does not match database case name (likely misattribution)
- `ADVISORY` — match found, everything consistent (no issue)

**REQ-F2.4** Output per flagged citation: cited text, parsed citation, resolved opinion (or null), severity, explanation, confidence score (0–1).

**REQ-F2.5** Handle CourtListener rate limits with exponential backoff + in-memory cache (24h TTL for hits, 1h for misses).

**Acceptance:** On a 100-document test corpus (50 with seeded fake citations, 50 with clean citations), achieve ≥95% true-positive rate and <5% false-positive rate.

---

### F3 — Evaluator: Quote Verification

**REQ-F3.1** For every passage surrounded by quotation marks followed by a case citation (within 200 chars), perform verification.

**REQ-F3.2** Fetch the full text of the cited opinion from CourtListener.

**REQ-F3.3** Normalize whitespace/punctuation. Perform fuzzy substring match (threshold: 85% similarity via Levenshtein or rapidfuzz partial ratio).

**REQ-F3.4** Assign severity:
- `CRITICAL` — quoted passage does not appear in the cited opinion (fabricated quote)
- `HIGH` — passage appears but with significant alterations
- `ADVISORY` — passage matches within threshold

**REQ-F3.5** Output: quoted text, cited opinion, match result, closest matching passage from opinion, similarity score.

**Acceptance:** ≥95% true-positive on seeded fabricated quotes; <8% false-positive (quotes often have minor punctuation/ellipsis variation, so threshold is higher).

---

### F4 — Evaluator: Bluebook Formatting

**REQ-F4.1** Implement a rule engine for Bluebook 21st edition citation format validation covering:
- Required elements (volume, reporter, page, year for case cites)
- Signal words (See, Cf., But see, etc.) — format only, not semantic correctness
- Pincites (rule B10.1.4)
- Parentheticals (court + year)
- Common abbreviations (reporter names, court names)

**REQ-F4.2** Severity:
- `HIGH` — missing required element
- `MEDIUM` — format error (e.g., wrong abbreviation)
- `ADVISORY` — style preference (e.g., recommended pincite)

**REQ-F4.3** Output: exact citation span, rule violated, suggested correction.

**Acceptance:** Reproduces ≥90% of human Bluebook-editor corrections on a 50-brief test set.

---

### F5 — Evaluator: Judge Verification

**REQ-F5.1** Extract judge names from document (regex patterns + NER fallback). Support formats: "Judge John Smith", "the Honorable J. Smith", "Smith, J.", etc.

**REQ-F5.2** For each detected judge, resolve against a local copy of the Federal Judicial Center "Biographical Directory of Federal Judges" (public dataset, ~4,000 judges, updated quarterly).

**REQ-F5.3** If the judge name is associated with a court, verify that the judge served on that court during the relevant time period.

**REQ-F5.4** Severity:
- `CRITICAL` — no federal judge with this name ever existed
- `HIGH` — judge exists but did not sit on the cited court during the cited period
- `ADVISORY` — match confirmed

**REQ-F5.5** Known ambiguity handling: common names with multiple matches return `ADVISORY` with a note.

**Acceptance:** Detects 100% of seeded fake judge names; <10% false-positive rate on real judges (due to name ambiguity).

---

### F6 — Evaluator: Temporal Validity (Overruled/Superseded)

**REQ-F6.1** For each citation that resolves in F2, query the CourtListener citation graph for negative treatment (overruled, abrogated, superseded).

**REQ-F6.2** Severity:
- `CRITICAL` — cited case is expressly overruled by a higher court
- `HIGH` — cited case is abrogated in relevant jurisdiction
- `MEDIUM` — cited case has significant negative treatment (>3 negative-treatment cites)
- `ADVISORY` — no negative treatment found

**REQ-F6.3** Output: treatment type, overruling case (if any), link to CourtListener page for more detail.

**Acceptance:** Matches ≥90% of CourtListener's negative-treatment flags on a test set of 50 overruled cases.

---

### F7 — Review Queue

**REQ-F7.1** Queue view: list of submitted documents, each with aggregate severity badge (highest-severity flag across all evaluators), flag count, submitter, timestamp, status (Pending / In Review / Resolved).

**REQ-F7.2** Default sort: severity descending, then timestamp ascending.

**REQ-F7.3** Filters: severity, submitter, date range, status, document type.

**REQ-F7.4** Document detail view: rendered document text with inline highlights for each flag. Clicking a flag opens a side panel showing the evaluator's explanation, severity, suggested correction (if any), and action buttons.

**REQ-F7.5** Per-flag actions:
- **Approve** — accept the flag is a real issue; reviewer commits to fixing
- **Override** — reviewer disagrees with the flag; requires a written reason (min 10 chars)
- **Reject** — flag is invalid/noise; feeds back to evaluator tuning
- **Defer** — send back to submitter

**REQ-F7.6** Document-level actions:
- **Finalize** — all flags resolved; generate audit export; document moves to "Resolved"
- **Reopen** — returns a Resolved document to active review

**REQ-F7.7** Keyboard shortcuts for all per-flag actions (A, O, R, D).

**REQ-F7.8** Reviewer attribution: every action records `user_id` + `timestamp_utc`.

**Acceptance:** A reviewer can process a 15-flag document in <5 minutes. All actions are recorded in the audit log.

---

### F8 — Audit Export

**REQ-F8.1** One-click PDF export per document once Finalized.

**REQ-F8.2** PDF contents:
- Document ID, firm name, submitter, reviewers, timestamps
- Original submitted text (full)
- Each flag with severity, evaluator, explanation, reviewer action, reviewer reason (if override)
- Summary table: total flags by severity, resolution counts
- Cryptographic hash chain: SHA-256 hash of this document's audit records, plus the hash of the preceding record in the firm's audit log
- CiteGuard version, evaluator versions

**REQ-F8.3** Export generates via server-side HTML-to-PDF (e.g., WeasyPrint or Puppeteer). Target generation time: <5 seconds.

**REQ-F8.4** Export action logged (who, when, document ID).

**REQ-F8.5** Re-exports must produce identical content for the same document state (deterministic).

**REQ-F8.6** Append-only audit log in Postgres: every action (submission, flag creation, reviewer action, finalize, export) is a row. Each row stores a SHA-256 hash of `(prior_row_hash || this_row_content)`. Tamper evidence is verifiable by re-computing the chain.

**Acceptance:** Exported PDF contains all required fields; hash chain verifies; tampering with any intermediate row detectable.

---

### F9 — Onboarding, Auth, and Team Management

**REQ-F9.1** Sign-up flow: email + password OR Google OAuth. Create a firm workspace on first sign-up.

**REQ-F9.2** Firm workspace settings: firm name, billing contact, default reviewer, alert channels.

**REQ-F9.3** Invite team members by email. Roles: `admin`, `reviewer`, `submitter`.
- `admin` — all permissions including billing, settings, user management
- `reviewer` — can review flags, finalize documents, view all firm documents
- `submitter` — can submit documents and view their own; cannot finalize

**REQ-F9.4** API key management: admins can generate, revoke, and list API keys. Keys display once at generation; never shown again.

**REQ-F9.5** Email verification required for all accounts before access.

**REQ-F9.6** Password requirements: min 12 chars, require 3 of {upper, lower, digit, symbol}. Argon2id hashing.

**REQ-F9.7** Session management: JWT with 24h expiry, refresh token with 30-day expiry. Logout invalidates tokens.

**Acceptance:** New firm can be created, team invited, API key generated, and first document submitted within 15 minutes of sign-up.

---

### F10 — Alerts

**REQ-F10.1** Per-firm Slack webhook configuration. When configured, alerts for `CRITICAL` flags send to Slack with: document ID, submitter, summary of flagged issues, direct link.

**REQ-F10.2** Per-user email alerts. Configurable severity threshold (default: `CRITICAL` + `HIGH`). Batched every 10 minutes to avoid spam.

**REQ-F10.3** Alert preferences respected per role: submitters alerted on their own docs; reviewers alerted on docs assigned to them or in their queue.

**Acceptance:** Critical flag on a document triggers Slack alert within 60 seconds of evaluation completing.

---

## 8. Non-Functional Requirements

### 8.1 Performance
- **NFR-P1** p50 evaluation latency: <1,500 ms
- **NFR-P2** p95 evaluation latency: <3,000 ms
- **NFR-P3** p99 evaluation latency: <7,000 ms
- **NFR-P4** Review queue page load: <500 ms p95
- **NFR-P5** PDF export generation: <5,000 ms

### 8.2 Availability
- **NFR-A1** API uptime target: 99.5% (max ~3.6 hours downtime/month)
- **NFR-A2** Graceful degradation: if CourtListener is down, queue jobs for retry instead of failing
- **NFR-A3** Planned maintenance windows: Sundays 02:00–05:00 UTC, pre-announced

### 8.3 Security
- **NFR-S1** All traffic over TLS 1.2+
- **NFR-S2** All data at rest encrypted (AES-256 via managed Postgres encryption)
- **NFR-S3** API keys stored as bcrypt hashes; plaintext keys never stored
- **NFR-S4** SOC 2 Type I readiness by end of V1 (controls documented; full audit deferred to V1.5)
- **NFR-S5** No PII/customer document text leaves the hosting region (US only in V1)
- **NFR-S6** Dependency vulnerability scanning in CI (GitHub Dependabot)
- **NFR-S7** No LLM calls to external providers use customer document text (except the customer's own upstream LLM via proxy, which is their own provider)

### 8.4 Data retention & residency
- **NFR-D1** Document text retained for 90 days by default; firm admins can extend to 1/3/7 years
- **NFR-D2** Audit log retained minimum 7 years
- **NFR-D3** Customers can request hard-delete within 30 days of request (excluding audit log for billing/legal)
- **NFR-D4** All data in US AWS regions (us-east-1 primary, us-west-2 standby)

### 8.5 Compliance posture (V1)
- **NFR-C1** DPA available on request
- **NFR-C2** Privacy policy + ToS explicitly disclaiming: we are a verification assistant, not a legal opinion; reviewer must be a licensed attorney
- **NFR-C3** Explicit "we are not a law firm" disclosure
- **NFR-C4** E&O insurance in force by week 10

---

## 9. System Architecture

### 9.1 Components

```
                    ┌───────────────────────────┐
                    │  Customer Law Firm App    │
                    │  (Harvey / Claude / RAG)  │
                    └──────────────┬────────────┘
                                   │
                  ┌────────────────┼───────────────┐
                  ▼                                ▼
         ┌──────────────────┐           ┌──────────────────┐
         │  SDK (Py/Node)   │           │  REST Proxy      │
         │  POST /verify    │           │  /v1/llm/proxy   │
         └────────┬─────────┘           └────────┬─────────┘
                  └─────────────┬─────────────────┘
                                ▼
                    ┌──────────────────────┐
                    │  API Gateway (FastAPI│
                    │  + Cloudflare)       │
                    │  auth, rate-limit,   │
                    │  validation          │
                    └───────────┬──────────┘
                                │
           ┌────────────────────┼────────────────────┐
           ▼                    ▼                    ▼
  ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐
  │ Job Queue      │  │ Postgres (RDS)   │  │ ClickHouse     │
  │ (Redis +       │  │ - documents      │  │ - traces       │
  │  Arq workers)  │  │ - flags          │  │ - telemetry    │
  └────────┬───────┘  │ - audit_log      │  └────────────────┘
           │          │   (hash chain)   │
           │          │ - users / firms  │
           │          └──────────────────┘
           ▼
  ┌──────────────────┐
  │ Evaluator Workers│──┐
  │ (parallel fan-out│  │
  │  per evaluator)  │  │
  └──────────────────┘  │
                        ▼
              ┌──────────────────┐
              │ External APIs    │
              │ - CourtListener  │
              │ - FJC Directory  │
              └──────────────────┘
                        │
                        ▼
            ┌─────────────────────────────┐
            │  Review UI (Next.js)        │
            │  - Queue                    │
            │  - Document detail          │
            │  - Audit export trigger     │
            └──────────────┬──────────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │  PDF Export Service      │
            │  (WeasyPrint on worker)  │
            └──────────────────────────┘
```

### 9.2 Tech stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend | Python 3.12 + FastAPI | Fast iteration; mature legal ML libraries |
| Workers | Arq (Redis-backed) | Simple async Python job queue |
| Primary DB | Postgres 16 (AWS RDS) | ACID for audit log; well-understood |
| Trace store | ClickHouse Cloud | Cost-efficient for high-volume traces |
| Frontend | Next.js 14, TypeScript, Tailwind, shadcn/ui | Productive, deployable to Vercel |
| Auth | Clerk | Faster than rolling our own; migrate later if needed |
| Hosting | Fly.io (backend), Vercel (frontend), ClickHouse Cloud | Solo-founder-friendly |
| CDN/WAF | Cloudflare | Standard; free tier suffices |
| Email | Resend or Postmark | Transactional reliability |
| Payments | Stripe + Stripe Billing | Meter per-doc via usage records |
| PDF gen | WeasyPrint (server-side) | Pure Python; deterministic |
| Citation parsing | `eyecite` | Best-in-class legal citation parsing |
| Court data | CourtListener REST API | Free, comprehensive, well-documented |
| Fuzzy match | `rapidfuzz` | Fast Levenshtein |

---

## 10. Data Model (Core Tables)

### 10.1 Key entities

```
firms                           users
────────────────                ──────────────
id PK                           id PK
name                            firm_id FK
created_at                      email
billing_email                   role ENUM(admin,reviewer,submitter)
stripe_customer_id              created_at
settings JSONB                  last_login

api_keys                        documents
──────────────                  ───────────────
id PK                           id PK
firm_id FK                      firm_id FK
name                            submitter_user_id FK
key_hash (bcrypt)               text (large)
created_by FK                   document_type
last_used_at                    llm_provider, llm_model
revoked_at                      prompt (nullable)
                                metadata JSONB
                                status ENUM(pending,in_review,resolved)
                                submitted_at
                                resolved_at

flags                           reviewer_actions
──────────────                  ───────────────
id PK                           id PK
document_id FK                  flag_id FK
evaluator (enum, 5 values)      user_id FK
severity ENUM                   action ENUM(approve,override,reject,defer)
explanation                     reason (text, required on override)
confidence FLOAT                created_at
start_offset, end_offset INT
suggested_correction
raw_evaluator_output JSONB
created_at

audit_log                       exports
───────────────                 ───────────────
id PK (ULID, time-ordered)      id PK
firm_id FK                      document_id FK
document_id FK (nullable)       user_id FK
event_type ENUM                 created_at
actor_user_id FK                pdf_path
payload JSONB                   pdf_hash (SHA-256)
prior_hash CHAR(64)             
this_hash CHAR(64)              
created_at
```

### 10.2 Hash-chain invariant

For every `audit_log` row `n`:
```
this_hash = sha256(prior_hash_n || canonical_json(payload_n))
```
Where `prior_hash_0 = sha256("")` (genesis). A verifier can re-compute the chain from scratch given the log; any altered payload yields a diverging hash.

---

## 11. External API Specification

### 11.1 POST /v1/documents

**Purpose:** Submit a document for verification.

**Auth:** Bearer API key

**Request:**
```json
{
  "idempotency_key": "uuid-optional",
  "user_id": "string (firm-assigned)",
  "document_type": "brief|memo|contract|other",
  "text": "string (max 200KB)",
  "prompt": "string (optional)",
  "llm_provider": "anthropic|openai|other",
  "llm_model": "string",
  "metadata": {}
}
```

**Response (201):**
```json
{
  "document_id": "cg_doc_01HZ...",
  "status": "pending",
  "submitted_at": "2026-06-01T12:34:56Z",
  "review_url": "https://app.citeguard.ai/documents/cg_doc_01HZ..."
}
```

### 11.2 GET /v1/documents/{id}

**Purpose:** Retrieve document status + flags.

**Response (200):**
```json
{
  "id": "cg_doc_01HZ...",
  "status": "in_review",
  "submitted_at": "...",
  "flags": [
    {
      "id": "cg_flag_...",
      "evaluator": "citation_existence",
      "severity": "CRITICAL",
      "explanation": "Case citation '123 F.3d 456 (9th Cir. 2019)' does not exist in CourtListener",
      "confidence": 0.97,
      "start_offset": 512,
      "end_offset": 548,
      "suggested_correction": null,
      "reviewer_action": null
    }
  ],
  "summary": {
    "critical": 2,
    "high": 3,
    "medium": 1,
    "advisory": 0
  }
}
```

### 11.3 POST /v1/llm/proxy (Anthropic-compatible)

**Purpose:** Drop-in proxy. Customer points their Claude SDK base URL here. CiteGuard captures request+response and queues verification.

Same schema as Anthropic's `/v1/messages`. Adds header: `X-CiteGuard-Document-Type: brief` (optional).

### 11.4 POST /v1/documents/{id}/export

**Purpose:** Generate audit PDF export.

**Response (200):**
```json
{
  "export_id": "cg_exp_...",
  "pdf_url": "https://...signed url, 1h expiry",
  "pdf_hash": "sha256:...",
  "generated_at": "..."
}
```

### 11.5 POST /v1/flags/{id}/actions

**Purpose:** Submit reviewer action.

**Request:**
```json
{
  "action": "approve|override|reject|defer",
  "reason": "string (required if action=override, min 10 chars)"
}
```

---

## 12. User Flows (Key Paths)

### 12.1 First-time customer onboarding
1. Admin signs up → creates firm workspace
2. Admin generates first API key → copies it
3. Admin installs SDK OR configures proxy in one app
4. Admin submits a test document via the dashboard's "Paste & Test" form
5. First verification result returned in dashboard
6. Admin invites reviewers and submitters
7. Admin connects Slack for alerts
8. Done — firm is live

**Target time from sign-up to first real document: <15 minutes.**

### 12.2 Submitter daily flow
1. Associate drafts brief in Word/Google Docs with AI assistance (Claude, Harvey, etc.)
2. Associate clicks browser extension / copies text / uses firm's internal tool that calls CiteGuard
3. CiteGuard returns a link to the review dashboard; associate sees flag summary
4. Associate fixes obvious issues (fake cites, fabricated quotes) in source doc
5. Re-submits if needed
6. Passes doc to senior associate for review

### 12.3 Reviewer flow
1. Reviewer opens the queue; filters to "assigned to me" or "severity CRITICAL"
2. Picks a document; reads the inline-flagged view
3. For each flag: Approve (real issue — note to submitter), Override (disagree with reason), Reject (false positive — feeds evaluator improvement)
4. Finalizes document → audit PDF generated

### 12.4 Audit request flow (rare but critical)
1. Managing partner receives a question from malpractice carrier or court
2. Opens dashboard → searches by date/user/document
3. Finds the document → downloads audit PDF
4. Shares with carrier; hash chain verifies integrity

---

## 13. UI/UX Requirements (V1)

### 13.1 Screens

| Screen | Purpose |
|--------|---------|
| Sign up / Sign in | Account creation |
| Firm setup | First-time onboarding wizard |
| Dashboard home | Summary stats, recent activity |
| Queue | List of documents, filters, sorts |
| Document detail | Inline-flagged document view + action panel |
| Audit exports | List of past exports, re-download |
| Team management | Invite / manage users, roles |
| API keys | Generate, revoke, list |
| Settings | Firm settings, Slack, retention, billing |
| Billing | Current usage, invoice history |

### 13.2 Design principles (V1)
- **Density over whitespace.** Lawyers review high-volume content; queues should show 20+ items per screen.
- **Keyboard-first.** Every action accessible via shortcuts. Target: a senior associate can clear a 20-flag document in under 3 minutes.
- **Professional tone.** No gamification. No emoji in UI. No "Great job!" micro-copy. This is a compliance tool.
- **Severity color language:** Critical = red, High = orange, Medium = amber, Advisory = blue. Never green (no "good job" vibe — just neutral).
- **Accessibility:** WCAG 2.1 AA minimum. Lawyers skew older; font sizes and contrast matter.

### 13.3 Out of scope for V1 UI
- Custom themes
- Dark mode (ship in V1.1)
- Mobile responsive beyond "it doesn't break" (lawyers use desktops)

---

## 14. Dependencies & Third-Party Services

| Dependency | Purpose | Risk | Mitigation |
|------------|---------|------|-----------|
| CourtListener API | Citation/opinion/judge data | Medium — nonprofit, could rate-limit us | Cache aggressively; donate for higher quota; have 2-week buffer plan |
| Federal Judicial Center | Judge biographical data | Low — public dataset, rarely updated | Snapshot locally; refresh quarterly |
| Anthropic Claude API | LLM for future LLM-as-judge (V1.1), not V1 | N/A | N/A in V1 |
| Clerk | Auth | Low | Standard vendor; export plan if needed |
| Stripe | Payments | Low | Standard |
| AWS (RDS, S3) | Infra | Low | Standard; backups daily |
| Fly.io | Hosting | Medium — smaller provider | Keep infra in Terraform; migration path to AWS documented |
| ClickHouse Cloud | Traces | Low | Postgres fallback possible if needed |

---

## 15. Risks & Mitigations

| # | Risk | Severity | Mitigation |
|---|------|---------|------------|
| R1 | Evaluator misses a real hallucination → customer gets sanctioned | High | ToS makes us a "verification assistant"; every flag says "review required"; E&O insurance; never claim 100% |
| R2 | CourtListener rate-limits or changes API | Medium | Cache + donate for higher tier; build paid Westlaw fallback in V1.1 |
| R3 | Harvey/Casetext adds similar feature | Medium | Tool-agnostic positioning; focus on audit/compliance angle they won't prioritize |
| R4 | Evaluator false positives annoy customers | Medium | Every reject action is data; tune thresholds weekly in V1; `reject_rate` is a core health metric |
| R5 | We can't sign 3 paying firms in 12 weeks | High | Start sales in week 1 (discovery), not week 12; have 5 design partners in pipeline by week 4 |
| R6 | PDF export gets challenged as "not real evidence" | Low-Med | Hash chain verifiable; align format with California Rules documentation; get one design partner to present to their malpractice carrier for pre-validation |

---

## 16. V1 Release Criteria (Definition of Done)

### 16.1 Functional
- [ ] All 10 F-requirements implemented and have passing end-to-end tests
- [ ] 5 evaluators produce correct results on the internal 100-document test corpus
- [ ] Review queue supports the full approve/override/reject/defer/finalize flow
- [ ] Audit PDF generated, hash chain verifiable
- [ ] Slack alerting working end-to-end

### 16.2 Non-functional
- [ ] All NFR performance targets hit in load test (sustained 10 docs/sec submissions)
- [ ] Security review completed: TLS everywhere, keys hashed, encryption at rest verified
- [ ] DPA and Privacy Policy drafted by legal counsel
- [ ] E&O policy bound and in force

### 16.3 Business
- [ ] ≥3 firms on paid contracts ($1,500/mo minimum each)
- [ ] Onboarding doc + API reference published at docs.citeguard.ai
- [ ] Landing page live at citeguard.ai
- [ ] Stripe billing working with per-doc metering
- [ ] Support channel (email + shared Slack for design partners) active

### 16.4 Operational
- [ ] Uptime monitoring + alerting configured (BetterStack/UptimeRobot)
- [ ] Error tracking configured (Sentry)
- [ ] Daily DB backups verified via restore test
- [ ] Runbook for top 5 operational incidents
- [ ] On-call rotation defined (even if it's a rotation of one)

---

## 17. Milestones

| Week | Milestone | Exit criteria |
|------|-----------|---------------|
| 1 | Discovery + technical scaffold | 10 customer calls done; stack deployed; "hello world" shipped |
| 2 | Ingestion + auth | SDK + proxy accept documents; Clerk integrated; 2 design partners signed |
| 3 | First evaluator live | F2 (Citation Existence) works end-to-end on real documents |
| 4 | Evaluators F3 + F4 | Quote Verification + Bluebook Formatting live |
| 5 | Evaluators F5 + F6 | Judge Verification + Temporal Validity live |
| 6 | Review queue | F7 UI complete; design partners actively reviewing |
| 7 | Audit export | F8 PDF generation + hash chain live |
| 8 | Alerts + polish | F10 Slack/email alerts; end-to-end UX pass |
| 9 | Load testing + hardening | NFR targets verified; security review complete |
| 10 | Paid conversion | ≥2 design partners converted to paid |
| 11 | Additional customers | 3rd and 4th paying firms closed |
| 12 | Public launch | Website live, press outreach, 5+ paying firms ideally |

---

## 18. Open Questions

- [ ] Does CourtListener's rate-limit policy support our scale? **Action:** Email their team by week 1 to discuss quotas and paid tier options.
- [ ] Do we need a BAA equivalent for attorney-client privileged data? **Action:** Get a legal-ethics opinion by week 4.
- [ ] What's the right price for firms with >100 lawyers? **Action:** Test at design-partner stage.
- [ ] Should the audit PDF include evaluator version hashes for reproducibility? **Likely yes; confirm with first design partner.**
- [ ] How do we handle multi-firm users (lawyers who consult across firms)? **Defer to V1.1.**
- [ ] Do we need to store the full source opinion texts (~8M opinions × avg 20KB ≈ 160GB) locally for speed, or hit CourtListener on every quote-verification request? **Decision needed by week 3.** Recommend local mirror; storage is cheap; API round-trips dominate latency.

---

## 19. Post-V1 Roadmap Preview (V1.1, V1.2)

**V1.1 (weeks 13–20):**
- State case law support (CA, NY, TX, FL first)
- Evaluator F7: Jurisdiction Match
- Evaluator F8: Statutory Currency
- Evaluator F9: Holding Accuracy (LLM-as-judge)
- Dark mode
- SSO/SAML

**V1.2 (weeks 21–32):**
- Evaluator F10: PII/Privilege Scan
- Evaluator F11: Opposing Authority Detection
- Chrome extension (capture from Google Docs / Word Online directly)
- Firm-level custom rules (e.g., "always flag cases outside 9th Circuit")
- API for customer-defined evaluators

**V2 (Q3 2026+):**
- Additional verticals: healthcare (clinical guideline adherence), accounting (GAAP evidence)
- SOC 2 Type II
- On-premise deployment option for AmLaw 100 firms

---

*End of V1 PRD. This document is the source of truth for V1 scope. Changes require a review and version bump.*