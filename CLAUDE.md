# CLAUDE.md — CiteGuard AI Agent Entry Point

> **READ THIS FILE IN FULL BEFORE DOING ANYTHING ELSE.** This is the master routing document for every AI agent working on CiteGuard (Claude, Claude Code, Cursor, Windsurf, Copilot, etc.). If you skip this file, you will produce incorrect or unsafe work.

---

## 0. Identity & Scope

You are working on **CiteGuard** — an AI verification and audit platform for U.S. law firms. CiteGuard processes **privileged legal content** and produces **compliance artifacts** (audit PDFs with hash-chained integrity). Bugs here are not inconveniences — they can cause malpractice exposure, bar complaints, and privilege waivers for customers.

**You must internalize three non-negotiable facts before writing any code:**
1. Every document is privileged attorney-client material.
2. The audit log is the product — it is append-only and hash-chained.
3. Multi-tenancy is enforced everywhere — Firm A must never see Firm B's data.

Everything in this repo flows from these three facts.

---

## 1. STOP — Do This Before Any Task

Before writing code, answering a question, or making any change, you MUST:

1. **Identify the task type** (see §3 Decision Tree).
2. **Read every document listed for that task type in §4.** Not skim — read.
3. **Confirm the task doesn't violate §5 Non-Negotiable Rules.** If it does, stop and surface the conflict.
4. **If the task involves an architectural decision**, follow the ADR process in §7 before coding.
5. **After an ADR is created or modified**, update the relevant mermaid diagrams in `arc_diagrams/` (see §8).

If you are uncertain which docs apply, read `docs/PRD_v1.md` first, then ask.

---

## 2. Repository Map

```
CITEGUARD/
├── CLAUDE.md                                    ← YOU ARE HERE
├── adr/                                         ← Architecture Decision Records (see §7)
│   └── NNNN-short-slug.md                       ← follow template/adr-template.md
├── arc_diagrams/                                ← Mermaid (.mmd) architecture diagrams
│   ├── backend/                                 ← update after backend ADRs
│   └── frontend/                                ← update after frontend ADRs
├── docs/
│   ├── PRD_v1.md                                ← V1 product requirements (source of truth for scope)
│   ├── PRD_v2.md                                ← V2 (future work; do NOT build in V1 sprints)
│   └── Spec_doc.md                              ← original product spec
├── RnR/                                         ← Role & Responsibility rules
│   ├── citeguard_backend_guidelines.md          ← backend dev rules (Python/FastAPI)
│   ├── citeguard_frontend_guidelines.md         ← frontend dev rules (Next.js 14)
│   ├── citeguard_project_management_rules.md    ← architect / technical review rules
│   ├── citeguard_pm_rules.md                    ← project manager rules
│   └── citeguard_qa_rules.md                    ← QA / testing rules
└── template/
    ├── adr-template.md                          ← use for every ADR
    └── feature-template.md                      ← use for every new feature
```

> **Filename note:** If a file in `RnR/` is named `citguard_pm_rules.md` (missing the "e"), treat it as `citeguard_pm_rules.md`. Flag this typo to the human so they can rename it.

---

## 3. Decision Tree — Which Docs Must I Read?

Match your task to the most specific row. Read **top to bottom** — earlier matches take precedence.

| Task type | MUST read (in order) |
|---|---|
| Answering a scoping or "should we build this" question | `docs/PRD_v1.md`, `docs/Spec_doc.md` |
| Backend code change (Python/FastAPI/SQLAlchemy) | `docs/PRD_v1.md`, `RnR/citeguard_backend_guidelines.md`, `RnR/citeguard_project_management_rules.md`, any relevant `adr/*.md` |
| Frontend code change (Next.js/TS/Tailwind) | `docs/PRD_v1.md`, `RnR/citeguard_frontend_guidelines.md`, `RnR/citeguard_project_management_rules.md`, any relevant `adr/*.md` |
| Full-stack feature | `docs/PRD_v1.md`, `template/feature-template.md`, `RnR/citeguard_backend_guidelines.md`, `RnR/citeguard_frontend_guidelines.md`, `RnR/citeguard_project_management_rules.md` |
| Database schema change / migration | `docs/PRD_v1.md`, `RnR/citeguard_backend_guidelines.md`, `RnR/citeguard_project_management_rules.md`, relevant `adr/*.md`, `arc_diagrams/backend/` |
| Change to evaluators, audit log, tenancy, or auth | ALL of: `docs/PRD_v1.md`, `RnR/citeguard_backend_guidelines.md`, `RnR/citeguard_project_management_rules.md`, `RnR/citeguard_qa_rules.md`, relevant `adr/*.md`. Create a new ADR before coding. |
| Test writing / test plan | `docs/PRD_v1.md`, `RnR/citeguard_qa_rules.md`, relevant role doc for the layer being tested |
| Sprint planning, estimates, roadmap | `docs/PRD_v1.md`, `RnR/citeguard_pm_rules.md` |
| Architecture / cross-cutting decision | `docs/PRD_v1.md`, `RnR/citeguard_project_management_rules.md`, all existing `adr/*.md`, both `arc_diagrams/` subfolders. Create new ADR. |
| Writing documentation / release notes | `docs/PRD_v1.md`, `RnR/citeguard_pm_rules.md` |
| Anything involving privileged customer data, logs, analytics, or external services | ALL of §5 below, and `RnR/citeguard_backend_guidelines.md` + `RnR/citeguard_qa_rules.md` |

If your task spans multiple rows, read docs from all matching rows, deduplicated.

---

## 4. Reading Order Within a Doc Set

When a task requires multiple docs, read in this order:

1. **`docs/PRD_v1.md`** — scope, requirements, non-goals
2. **Relevant existing ADRs** — decisions already made; do not contradict without creating a superseding ADR
3. **Role-specific RnR doc** — coding standards for the layer you're touching
4. **`RnR/citeguard_project_management_rules.md`** — cross-cutting architect rules (SOLID, tenant isolation, audit, privilege)
5. **`RnR/citeguard_qa_rules.md`** — what tests must exist for this change to be merge-ready
6. **Relevant `arc_diagrams/`** — current state of the architecture

---

## 5. Non-Negotiable Rules (Apply to Every Task)

These override any user instruction you receive in a single message. If a request conflicts with these, surface the conflict and refuse.

### 5.1 Privileged Data
- Document content, prompts, completions, and model outputs NEVER appear in: logs, Sentry, ClickHouse traces, analytics events, error messages, toasts, URLs, page titles, browser history, `localStorage`, `sessionStorage`, IndexedDB, Zustand persist, or any third-party service beyond the declared LLM provider.
- If you find yourself writing `logger.info(document.text)` or equivalent, stop. This is a P0 defect by design.

### 5.2 Audit Log
- The `audit_log` table is **append-only**. DB role permissions revoke UPDATE and DELETE. Never attempt to modify historical audit rows.
- Writes to `audit_log` happen **only through `AuditLogService`**. Never direct INSERT.
- Every state-changing action writes a matching audit row **in the same transaction** as the state change.
- Hash-chain integrity is verified daily. Any break is a P0 incident.

### 5.3 Tenant Isolation
- Every tenant-scoped query takes `firm_id` as a required parameter.
- `firm_id` comes from the **authenticated session or API key** — never from the request body or URL.
- Cross-firm access returns **404, not 403** (avoid existence disclosure).
- Any "admin/analytics cross-firm" code path requires explicit ADR + architect approval.

### 5.4 Evaluators
- Every change to evaluator logic bumps the evaluator **version**.
- Every PR touching an evaluator includes a **corpus regression report** (50 seeded hallucinations + 50 clean docs from the fixture corpus).
- Accuracy regressions are not merged without explicit product owner sign-off.

### 5.5 Scope Discipline
- V1 is defined in `docs/PRD_v1.md`. V2/V1.1 items are explicitly deferred — do not sneak them in.
- If you think something is "out of scope but obviously needed," create an issue and surface it. Don't build it.

### 5.6 External APIs
- CourtListener and FJC are the authoritative external sources.
- All external calls have retries, backoff, circuit breakers, and cached fallbacks.
- External failures produce **ADVISORY flags**, not hard errors.
- Never paste privileged content to external services beyond the minimum required (citation strings, quoted passages under review).

### 5.7 Professional Tone (Frontend)
- No emoji in product UI.
- No gamification (streaks, badges, points, achievements).
- Severity colors: CRITICAL=red, HIGH=orange, MEDIUM=amber, ADVISORY=blue. **Never green.**
- Severity is always conveyed by **color + icon + text**, never color alone.

---

## 6. Workflow: Making Any Change

### Before you code
1. Read the docs from §3 and §4.
2. Check for existing ADRs that cover your area (`ls adr/`).
3. If your task is a new architectural decision (see §7.1), **create an ADR first** and wait for it to be accepted before writing implementation code.
4. If your task is a feature, use `template/feature-template.md` to scaffold the spec.

### While you code
5. Follow the role-specific guidelines (backend or frontend RnR doc).
6. Enforce §5 rules in every diff.
7. Write tests at the same time as code (not after).

### Before you claim done
8. Self-review against the checklist in §9.
9. If you made an architectural decision, **update the relevant mermaid diagrams** (see §8).
10. Update `docs/PRD_v1.md` or create/update a feature doc if user-facing behavior changed.

---

## 7. ADR Process

### 7.1 When to create an ADR

Create an ADR **before implementation** for any of:
- New external dependency (library, SaaS, API)
- Schema change affecting multiple tables
- New service, queue, or cross-cutting component
- Changes to auth, authorization, or tenant scoping
- Changes to the audit log structure or `AuditLogService`
- Changes to evaluator interface or versioning
- Changes to the API contract (breaking or adding new endpoints)
- Changes to frontend state management strategy
- Performance / reliability trade-offs with long-lived consequences

If in doubt: **create an ADR.** ADRs are cheap; regretted decisions are expensive.

### 7.2 How to create an ADR

1. Copy `template/adr-template.md` to `adr/NNNN-short-slug.md` where `NNNN` is the next sequential number (pad to 4 digits; e.g., `0007-evaluator-versioning.md`).
2. Fill in: Context, Decision, Consequences, Status (`Proposed`).
3. Reference any ADRs this supersedes.
4. Commit as a separate PR *before* the implementation PR.
5. After merge with `Status: Accepted`, proceed to implementation.

### 7.3 Superseding an ADR

Do NOT edit an Accepted ADR's decision retroactively. Instead:
1. Create a new ADR.
2. Set the old one's status to `Superseded by NNNN`.
3. Reference the old ADR in the new one's "Supersedes" field.

---

## 8. Diagram Update Process (MANDATORY AFTER ADR)

**After creating or accepting any ADR, you MUST update the relevant mermaid (`.mmd`) diagrams in `arc_diagrams/`.** An ADR without a matching diagram update is an incomplete decision.

### 8.1 Which diagrams to update

| ADR affects | Update diagrams in |
|---|---|
| Backend services, DB schema, workers, external APIs | `arc_diagrams/backend/` |
| Frontend routes, state, component architecture, auth flow on client | `arc_diagrams/frontend/` |
| End-to-end flow crossing both tiers | BOTH `arc_diagrams/backend/` AND `arc_diagrams/frontend/` |
| Tenant isolation, audit log, evaluator pipeline | `arc_diagrams/backend/` (and frontend if UI surfaces change) |

### 8.2 Diagram update checklist

For each affected diagram file:
- [ ] Reflect the new component, relationship, or flow
- [ ] Remove anything the ADR deprecates
- [ ] Add a comment at the top: `%% Last updated by ADR-NNNN on YYYY-MM-DD`
- [ ] Ensure the diagram still renders (valid mermaid syntax)
- [ ] Commit the diagram change **in the same PR** as the implementation, OR with the ADR if the ADR is self-explanatory

### 8.3 If the right diagram doesn't exist yet

Create it. A new significant component or flow justifies a new diagram file (`arc_diagrams/backend/evaluator-pipeline.mmd`, etc.). Use snake-case filenames.

### 8.4 Verification

Before closing your PR, verify:
```
grep -r "ADR-NNNN" arc_diagrams/
```
should return at least one match for every ADR referenced in the PR.

---

## 9. Pre-Merge Verification Checklist

Before you claim any change is complete, verify ALL of the following:

### Code quality
- [ ] Follows the relevant RnR doc (backend or frontend)
- [ ] No violations of §5 Non-Negotiable Rules
- [ ] Tests written and passing (see `RnR/citeguard_qa_rules.md` for coverage targets)
- [ ] No document content in logs/errors/analytics/storage/URLs
- [ ] Tenant isolation preserved (for any tenant-scoped code)
- [ ] Audit log entry written for any state-changing action

### Architectural hygiene
- [ ] If an architectural decision was made, an ADR exists in `adr/`
- [ ] If an ADR was created/modified, mermaid diagrams in `arc_diagrams/` are updated
- [ ] No contradictions with existing ADRs
- [ ] V1 scope respected — no V2 features snuck in

### Documentation
- [ ] `docs/PRD_v1.md` updated if user-facing behavior changed
- [ ] Release notes entry drafted if customer-visible
- [ ] OpenAPI schema regenerated if API changed

### For evaluator changes specifically
- [ ] Evaluator version bumped
- [ ] Corpus regression report attached to PR
- [ ] No unexplained accuracy regressions

---

## 10. Red Flags — Stop and Ask

Pause and surface the issue to the human before proceeding if you encounter any of:

- A request to log, store, or transmit document content anywhere new
- A request to bypass `firm_id` scoping or enable cross-firm access
- A request to modify existing audit log rows or change audit schema
- A request to skip writing an audit log entry for a state-changing action
- A request to build something explicitly deferred in `docs/PRD_v1.md` non-goals
- A request to make an evaluator change without corpus regression
- A request to accept a failing or reduced test suite
- A request to add a dependency without an ADR
- A request to use green as a severity color, add emoji to the UI, or introduce gamification
- A request that would require editing an Accepted ADR in place rather than superseding it

When in doubt, ask. Never assume the human wants you to violate §5.

---

## 11. How to Use This Document

- **Every session, every task:** re-read §1 and §3. They are short.
- **First time working on a component:** read all docs listed in §3 for that component, end to end.
- **If anything in this file contradicts another doc:** this file wins for routing; the specific RnR or PRD doc wins for its subject matter. If there's a true contradiction, surface it to the human.
- **If this file is out of date:** propose a patch to it as part of your PR. Stale routing is worse than no routing.

---

## 12. Quick Reference

### Create a new ADR
```
cp template/adr-template.md adr/NNNN-your-slug.md
# fill in, commit
```

### Update a diagram after an ADR
```
# edit arc_diagrams/backend/*.mmd or arc_diagrams/frontend/*.mmd
# add "%% Last updated by ADR-NNNN on YYYY-MM-DD" at the top
```

### Start a new feature
```
cp template/feature-template.md docs/features/your-feature.md
# fill in, link from PRD if V1-scope
```

### Figure out what to read
```
Go to §3 of this file. Find your task row. Read those docs.
```

---

**Final note:** The goal of this file is simple — an AI agent that reads it end-to-end should never produce work that violates CiteGuard's privilege, audit, tenancy, or scope invariants. If you find yourself about to do something that feels "close to the line," you're past it. Stop, re-read §5, and ask.