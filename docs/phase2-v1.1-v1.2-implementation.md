# CiteGuard Phase 2: V1.1 + V1.2 Implementation Guide

| | |
|---|---|
| **Phase** | Phase 2 — V1.1 + V1.2 (Post-Launch Expansion) |
| **Duration** | 20 weeks (10 two-week sprints) |
| **Sprint cadence** | 2-week sprints (Sprints 7–16) |
| **Prerequisite** | Phase 1 (V1) complete and stable |
| **PRD reference** | `docs/PRD_v1.md` §19 (Post-V1 Roadmap) |
| **Last updated** | 2026-04-18 |

---

## 1. Phase Overview

Phase 2 bridges V1 (MVP) to V2 (Enterprise Platform). It delivers:

- **V1.1 (Weeks 13–20):** State case law, 3 new evaluators, dark mode, SSO/OIDC
- **V1.2 (Weeks 21–32):** PII/Privilege scan, Opposing Authority, custom rules UI, customer evaluator SDK, analytics dashboard, Chrome extension

### What V1.1 Ships

| Feature | Description |
|---------|-------------|
| State case law | CA, NY, TX, FL state court opinions via CourtListener |
| Jurisdiction Match evaluator | Cited precedent must be controlling/persuasive in filing court |
| Statutory Currency evaluator | Flags repealed, amended, or superseded statutes |
| Holding Accuracy evaluator | LLM-as-judge using Claude — verifies AI's characterization of holdings |
| Dark mode | Tailwind dark mode across all UI |
| SSO/OIDC | Google Workspace SSO, Microsoft SSO via Clerk Enterprise |

### What V1.2 Ships

| Feature | Description |
|---------|-------------|
| PII/Privilege Scan evaluator | Detects client PII, privileged material in AI outputs |
| Opposing Authority evaluator | Flags likely missing adverse controlling precedent (ABA 3.3(a)(2)) |
| Custom rules UI | Firm-level regex + keyword rules for practice-specific flags |
| Customer evaluator SDK | Python SDK for customer-defined evaluators |
| Analytics dashboard | Firm-wide flag trends, evaluator breakdown, reviewer throughput |
| Chrome extension | Capture from Google Docs / Word Online directly |

---

## 2. ADRs Required

### V1.1 ADRs

| ADR | File | Scope |
|-----|------|-------|
| ADR-0011 | `adr/0011-state-case-law.md` | State case law data sources, CourtListener state coverage, supplementary sources, court hierarchy for CA/NY/TX/FL |
| ADR-0012 | `adr/0012-llm-as-judge.md` | LLM-as-judge architecture for Holding Accuracy — provider selection (Claude), prompt engineering, non-determinism handling, confidence calibration, document content handling |
| ADR-0013 | `adr/0013-sso-oidc.md` | SSO/OIDC strategy — Clerk Enterprise tier vs WorkOS evaluation, supported providers, session management |

### V1.2 ADRs

| ADR | File | Scope |
|-----|------|-------|
| ADR-0014 | `adr/0014-custom-rules-engine.md` | Firm-level custom rules — storage schema, evaluation integration, rule lifecycle (create/enable/disable/delete), regex + keyword matching |
| ADR-0015 | `adr/0015-customer-evaluator-sdk.md` | Customer-defined evaluators — Python SDK, sandboxed execution, timeout policy (5s), available context, VPC-only restriction |
| ADR-0016 | `adr/0016-pii-privilege-scan.md` | PII/privilege detection — NER model selection, rule patterns, sensitivity levels, false-positive management |
| ADR-0017 | `adr/0017-opposing-authority.md` | Opposing authority detection — semantic search approach, ABA Model Rule 3.3(a)(2), data sources, confidence calibration |
| ADR-0018 | `adr/0018-chrome-extension.md` | Chrome extension architecture — manifest v3, content scripts, communication with CiteGuard API, Google Docs/Word Online DOM interaction |

---

## 3. V1.1 Implementation (Weeks 13–20)

### Sprint 7 (Weeks 13–14): State Case Law + Jurisdiction Match

#### Sprint Goal

State case law support for CA, NY, TX, FL. Jurisdiction Match evaluator live.

#### Backend Components

**State case law integration:**
- Extend CourtListener client for state court reporters (Cal.App, N.Y.S., Tex.App, Fla.App, etc.)
- State court hierarchy mapping: `app/integrations/courtlistener/court_hierarchy.py`
  - Supreme Court > Circuit Courts > District Courts (federal)
  - State Supreme Court > Appellate > Trial (per state)
- Controlling vs persuasive precedent logic
- Update Citation Existence evaluator to handle state reporters

**Jurisdiction Match evaluator** (`app/evaluators/jurisdiction_match.py`):
- **Version:** 1.0.0
- Extract filing court from document metadata or text analysis
- For each citation, determine if cited court is controlling authority in filing jurisdiction
- Court hierarchy database with federal + state (CA/NY/TX/FL) mappings
- **Severity:**
  - HIGH — citing a different circuit's precedent as binding
  - MEDIUM — citing persuasive authority without acknowledging it
  - ADVISORY — properly cited controlling authority
- **Output:** cited court, filing court, relationship (binding/persuasive/irrelevant), explanation

**Database migration:**
- `court_hierarchies` table: court_id, parent_court_id, jurisdiction, level
- Seed data for federal courts + CA/NY/TX/FL state courts

#### Frontend

- State/jurisdiction filter in queue
- Jurisdiction Match flag display in document detail
- Court hierarchy visualization in flag explanation

#### Acceptance Criteria

- [ ] CourtListener returns state court opinions for CA, NY, TX, FL
- [ ] Citation Existence works for state reporters
- [ ] Jurisdiction Match evaluator detects cross-jurisdiction citations
- [ ] Court hierarchy correctly models federal + 4 state systems
- [ ] ADR-0011 committed

---

### Sprint 8 (Weeks 15–16): Statutory Currency + Holding Accuracy

#### Sprint Goal

Statutory Currency and Holding Accuracy (LLM-as-judge) evaluators live.

#### Backend Components

**Statutory Currency evaluator** (`app/evaluators/statutory_currency.py`):
- **Version:** 1.0.0
- Parse statutory citations from document (USC, CFR, state statute formats)
- Check against public statute databases (LegInfo, GovInfo, state legislature APIs)
- **Severity:**
  - CRITICAL — statute repealed
  - HIGH — statute substantially amended after cited version
  - MEDIUM — minor amendments since cited version
  - ADVISORY — current and valid
- **Output:** statute citation, current status, effective dates, amendment history summary

**Holding Accuracy evaluator** (`app/evaluators/holding_accuracy.py`):
- **Version:** 1.0.0
- **LLM-as-judge architecture:**
  - Extract AI's characterization of a case's holding from the document
  - Fetch actual opinion text from CourtListener
  - Send both to Claude (Opus) with a carefully engineered prompt
  - Claude compares the characterization against the actual holding
  - Return a structured assessment (accurate/misleading/fabricated)
- **Prompt engineering:**
  - System prompt establishes the evaluator role
  - User prompt presents the characterization + source opinion
  - Structured output via tool use (JSON schema response)
  - Temperature: 0 for maximum determinism
- **Variance testing:** Run each comparison 3x, require 2/3 consensus for non-ADVISORY severity
- **Severity:**
  - CRITICAL — holding is fabricated or inverted
  - HIGH — holding is materially misleading
  - MEDIUM — holding is overstated or oversimplified
  - ADVISORY — holding accurately represents the opinion
- **Privileged data handling:** Only the characterization + cited opinion text sent to Claude — never the full document
- **Cost management:** Only run on citations where the AI explicitly characterizes a holding (not all citations)

**Key implementation notes:**
- Claude API calls must use the customer's own LLM billing (not CiteGuard's)
- Timeout: 15s per holding comparison (longer than deterministic evaluators)
- Non-determinism documented: results may vary between runs (this is inherent to LLM-as-judge)

#### Acceptance Criteria

- [ ] Statutory Currency detects repealed/amended statutes
- [ ] Holding Accuracy correctly identifies fabricated holdings on test corpus
- [ ] LLM-as-judge variance testing implemented (3x runs, 2/3 consensus)
- [ ] Claude API integration with structured output
- [ ] Document content never sent to Claude beyond the cited passage + opinion
- [ ] ADR-0012 committed

---

### Sprint 9 (Weeks 17–18): SSO/OIDC + Dark Mode

#### Sprint Goal

SSO/OIDC available for enterprise customers. Dark mode shipped.

#### Backend Components

**SSO/OIDC support:**
- Evaluate Clerk Enterprise tier capabilities vs WorkOS migration
- Configure Google Workspace SSO (OIDC)
- Configure Microsoft Entra ID SSO (OIDC)
- Session management: SSO sessions respect firm-level timeout settings
- Audit log: record SSO authentication events

**Enhanced analytics endpoints:**
- `GET /v1/analytics/firm-summary` — firm-wide flag statistics by evaluator, severity, time period
- `GET /v1/analytics/evaluator-breakdown` — per-evaluator accuracy and flag distribution

#### Frontend Components

**Dark mode:**
- Tailwind `dark:` variant classes across all components
- shadcn/ui dark mode variants
- Severity colors maintained in dark mode (contrast verified)
- Theme toggle in user settings (system/light/dark)
- Preference persisted in user profile (not localStorage — avoid cross-device confusion)

**SSO login flow:**
- OIDC provider selection on sign-in page
- "Sign in with Google Workspace" / "Sign in with Microsoft" buttons
- Firm-level SSO configuration in admin settings

**Enhanced dashboard:**
- Firm-wide flag statistics chart (severity distribution over time)
- Top evaluators by flag count
- Reviewer throughput metrics

#### Acceptance Criteria

- [ ] Google Workspace SSO functional end-to-end
- [ ] Microsoft Entra ID SSO functional end-to-end
- [ ] Dark mode renders correctly across all pages
- [ ] Severity colors maintain WCAG AA contrast in dark mode
- [ ] Theme toggle persists across sessions
- [ ] Dashboard shows firm-wide stats
- [ ] ADR-0013 committed

---

### Sprint 10 (Weeks 19–20): V1.1 Stabilization + Corpus Expansion

#### Sprint Goal

V1.1 stabilization, evaluator corpus expansion for new evaluators, design partner validation.

#### Backend

- Evaluator corpus expansion: add state case law test cases, jurisdiction match scenarios, statutory currency cases, holding accuracy examples
- Target corpus: 200 documents (100 original + 100 new covering V1.1 evaluators)
- Performance testing with 8 evaluators running in parallel
- Latency budget review — LLM-as-judge adds significant latency

#### Frontend

- V1.1 release notes page
- Evaluator documentation updates (8 evaluators now)
- Design partner feedback integration

#### Acceptance Criteria

- [ ] 8 evaluators running in parallel, p95 latency within budget
- [ ] Expanded corpus (200 docs) passing accuracy targets
- [ ] State case law (CA/NY/TX/FL) verified with design partners
- [ ] V1.1 release notes published

---

## 4. V1.2 Implementation (Weeks 21–32)

### Sprint 11 (Weeks 21–22): PII/Privilege Scan Evaluator

#### Sprint Goal

PII/Privilege Scan evaluator live.

#### Backend Components

**PII/Privilege Scan evaluator** (`app/evaluators/pii_privilege_scan.py`):
- **Version:** 1.0.0
- **Detection categories:**
  - Client PII: names, addresses, SSN patterns, phone numbers, email addresses
  - Privileged content markers: "attorney-client privileged", "work product", "confidential"
  - Sealed/restricted content: sealed case references, in camera materials
  - Opposing party PII that shouldn't be in AI prompts
- **Implementation:**
  - Rule-based patterns (regex) for structured PII (SSN, phone, email)
  - spaCy NER for person names, organizations, locations
  - Keyword matching for privilege markers
  - Context-aware: only flag PII that appears to be leaked INTO AI output (not legitimate references in legal text)
- **Severity:**
  - CRITICAL — SSN, financial account numbers, sealed content
  - HIGH — client name + address combination, privileged material markers
  - MEDIUM — individual PII elements without clear leak context
  - ADVISORY — potential PII that may be legitimate legal references
- **False-positive management:** Legal documents legitimately contain names, addresses, etc. Context scoring reduces false positives.

#### Acceptance Criteria

- [ ] Detects seeded PII in test corpus (SSN patterns, phone, email)
- [ ] Detects privilege markers ("attorney-client privileged")
- [ ] Context-aware scoring reduces false positives on legitimate legal references
- [ ] ≥90% true-positive on seeded PII, <15% false-positive
- [ ] ADR-0016 committed

---

### Sprint 12 (Weeks 23–24): Opposing Authority + Custom Rules Engine

#### Sprint Goal

Opposing Authority evaluator live. Custom rules engine with basic regex/keyword support.

#### Backend Components

**Opposing Authority evaluator** (`app/evaluators/opposing_authority.py`):
- **Version:** 1.0.0
- **Approach:** For each legal argument in the document, identify the relevant legal issue and search for likely adverse authority that the document doesn't cite
- **Implementation:**
  - Extract legal issues/arguments from document (LLM-assisted extraction)
  - For each cited case, query CourtListener for cases with negative treatment
  - Identify commonly cited adverse cases for the same legal issue
  - Compare against the document's citations — flag missing adverse authority
- **Severity:**
  - CRITICAL — well-known mandatory adverse authority missing (e.g., controlling adverse case in same circuit)
  - HIGH — significant adverse authority from same jurisdiction not cited
  - MEDIUM — persuasive adverse authority not mentioned
  - ADVISORY — minor adverse authority (unlikely to be required under 3.3(a)(2))
- **ABA Rule 3.3(a)(2) context:** "A lawyer shall not knowingly fail to disclose to the tribunal legal authority in the controlling jurisdiction known to the lawyer to be directly adverse to the position of the client"

**Custom rules engine** (`app/rules/`):
- `app/rules/models.py` — CustomRule model: id, firm_id, name, description, pattern_type (regex/keyword), pattern, scope (document_type filter), severity, enabled, created_by, created_at
- `app/rules/service.py` — RuleService: CRUD operations, rule evaluation
- `app/rules/evaluator.py` — CustomRulesEvaluator: runs all enabled firm rules against document
- `app/rules/router.py` — `GET/POST/PATCH/DELETE /v1/rules` (admin-only)
- Integration: CustomRulesEvaluator registered in EvaluatorOrchestrator, runs alongside built-in evaluators
- Rules scoped by firm_id (tenant isolation applies)
- Rule flags appear in review queue with rule name as attribution

#### Frontend Components

**Custom rules UI** (`app/(authenticated)/firm/rules/`):
- Rule list with name, pattern, severity, enabled toggle
- Create rule modal: name, description, pattern type (regex/keyword), pattern input with preview, scope (document type), severity
- Edit/delete rules
- Rule test: paste sample text, see if rule matches
- Admin-only access

#### Acceptance Criteria

- [ ] Opposing Authority detects missing adverse cases on test corpus
- [ ] Custom rules: admin can create regex rule, submit document, see rule-generated flag
- [ ] Custom rules: keyword matching functional
- [ ] Rules scoped to firm (Firm A's rules don't apply to Firm B)
- [ ] Rule flags attributed to rule name in review queue
- [ ] ADR-0014, ADR-0017 committed

---

### Sprint 13 (Weeks 25–26): Customer Evaluator SDK

#### Sprint Goal

Customer-defined evaluators via Python SDK.

#### Backend Components

**Customer Evaluator SDK** (`app/evaluators/custom/`):
- `app/evaluators/custom/sdk.py` — Python SDK base classes:
  ```python
  from citeguard import Evaluator, Severity, Flag

  class ClientConflictCheck(Evaluator):
      name = "client_conflict"
      version = "1.0.0"

      async def evaluate(self, document, context):
          # Custom logic here
          return [Flag(severity=Severity.CRITICAL, ...)]
  ```
- `app/evaluators/custom/runner.py` — Sandboxed execution environment:
  - Subprocess isolation with resource limits
  - 5-second timeout per custom evaluator (hard kill on exceed)
  - Timeout → ADVISORY flag, not document failure
  - Available context: document text, parsed citations, metadata, firm API endpoints
- `app/evaluators/custom/registry.py` — Registration of customer evaluators per firm
- **Security:** Customer evaluators have network access only to allowlisted endpoints (firm's own CRM, etc.)
- **Availability:** Only on Enterprise/VPC tier (not multi-tenant SaaS)

#### Documentation

- `docs/customer-evaluator-sdk.md` — Full SDK documentation with examples
- Example evaluators: conflict check, jurisdiction filter, firm-specific citation style

#### Acceptance Criteria

- [ ] Customer can write, register, and run a custom evaluator
- [ ] 5-second timeout enforced (timeout → ADVISORY, not failure)
- [ ] Custom evaluator results appear in review queue alongside built-in flags
- [ ] Sandboxed execution prevents resource abuse
- [ ] ADR-0015 committed

---

### Sprint 14 (Weeks 27–28): Analytics Dashboard

#### Sprint Goal

Firm-level analytics dashboard with trend charts and CSV export.

#### Backend Components

**Analytics service** (`app/analytics/`):
- `app/analytics/service.py` — Aggregate queries for firm-level reporting
- Endpoints:
  - `GET /v1/analytics/overview` — docs verified, flags by severity, over time
  - `GET /v1/analytics/evaluators` — per-evaluator flag rate, accuracy trends
  - `GET /v1/analytics/reviewers` — reviewer throughput, override rate, time-to-resolution
  - `GET /v1/analytics/export` — CSV download of all flags + actions
- ClickHouse for performance on large firms (>10K documents)
- Caching: Redis with 5-minute TTL for dashboard queries

#### Frontend Components

**Analytics dashboard** (`app/(authenticated)/analytics/`):
- **Overview tab:** documents verified over time (line chart), flags by severity (stacked bar), recent trends
- **Evaluators tab:** per-evaluator flag distribution, false-positive rate (override rate), flag rate trends
- **Reviewers tab:** reviewer throughput (flags/hour), override rate by reviewer, time-to-resolution distribution
- **Export tab:** date range selector, CSV download button
- All charts: admin-only access, firm-scoped data

**Libraries:** Recharts or Chart.js for charts (lightweight, accessible)

#### Acceptance Criteria

- [ ] Dashboard loads in <800ms for firms with >10K documents
- [ ] Overview shows document count, flag distribution, trends
- [ ] Evaluator breakdown shows per-evaluator stats
- [ ] Reviewer throughput metrics accurate
- [ ] CSV export includes all flags + actions with dates
- [ ] Admin-only access enforced

---

### Sprint 15 (Weeks 29–30): Chrome Extension

#### Sprint Goal

Chrome extension for capturing documents from Google Docs and Word Online.

#### Frontend Components

**Chrome extension** (`extensions/chrome/`):
- **Manifest v3** — service worker, content scripts, popup
- **Content scripts:**
  - Google Docs: extract document text via DOM API
  - Word Online: extract document text via DOM API
- **Popup UI:**
  - "Verify this document" button
  - Auth: OAuth flow connecting to user's CiteGuard workspace
  - Flag summary display after verification
  - Link to full review in CiteGuard dashboard
- **Background service worker:**
  - API calls to CiteGuard backend
  - Auth token management
  - Badge notification for CRITICAL flags

#### Backend

- No backend changes needed — extension uses existing `POST /v1/documents` API
- Optional: `POST /v1/documents` accepts source_type: "chrome_extension" for telemetry

#### Acceptance Criteria

- [ ] Extension installs from Chrome Web Store (or dev sideload)
- [ ] Extracts text from Google Docs accurately
- [ ] Extracts text from Word Online accurately
- [ ] Submit → verify → see flag summary in popup
- [ ] Link to full review in dashboard
- [ ] ADR-0018 committed

---

### Sprint 16 (Weeks 31–32): V1.2 Stabilization + Release

#### Sprint Goal

V1.2 stabilization, expanded test corpus, release.

#### Tasks

- Evaluator corpus expansion: 300 documents (200 from V1.1 + 100 new for PII, opposing authority, custom rules)
- All 10 evaluators running in parallel — latency verification
- Full regression testing
- V1.2 release notes
- Updated API documentation (new endpoints for rules, analytics)
- Design partner feedback review and bug fixes

#### Acceptance Criteria

- [ ] 10 evaluators running in parallel, p95 latency within budget
- [ ] 300-document corpus passing all accuracy targets
- [ ] Custom rules functional for 3+ design partners
- [ ] Analytics dashboard validated with real firm data
- [ ] Chrome extension validated with 3+ users
- [ ] V1.2 release notes published

---

## 5. Architecture Diagram Updates

After Phase 2, update these diagrams:

| Diagram | Updates |
|---------|---------|
| `arc_diagrams/backend/evaluator-pipeline.mmd` | Add 5 new evaluators, custom rules engine, customer evaluator runner |
| `arc_diagrams/backend/system-overview.mmd` | Add custom rules engine, analytics service, Chrome extension |
| `arc_diagrams/frontend/app-routes.mmd` | Add rules, analytics, and Chrome extension routes |
| New: `arc_diagrams/backend/custom-rules-engine.mmd` | Custom rules storage, evaluation, management |
| New: `arc_diagrams/backend/customer-evaluator-sdk.mmd` | Customer evaluator registration, sandboxed execution |
| New: `arc_diagrams/frontend/analytics-dashboard.mmd` | Analytics component architecture |

---

## 6. Key Risks (Phase 2)

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM-as-judge non-determinism causes inconsistent Holding Accuracy results | Medium | Variance testing (3x runs, 2/3 consensus), explicit confidence scoring, document non-determinism for users |
| Customer evaluator SDK security surface | Medium | Sandboxed execution, timeout enforcement, VPC-only, allowlisted network access |
| Chrome extension Google Docs DOM instability | Medium | Test against multiple Doc versions, graceful degradation if extraction fails |
| PII/Privilege Scan false-positive rate on legal text | High | Context-aware scoring, configurable sensitivity, firm-level tuning |
| SSO provider compatibility issues | Low | Test with Okta, Azure AD, Google Workspace before release |

---

## 7. Success Criteria (Phase 2 Complete)

- [ ] 8 evaluators live (V1.1) → 10 evaluators live (V1.2)
- [ ] State case law operational for CA, NY, TX, FL
- [ ] SSO/OIDC available for enterprise customers
- [ ] Dark mode shipped
- [ ] Custom rules UI functional with 3+ firms using rules
- [ ] Analytics dashboard live with real firm data
- [ ] Chrome extension published
- [ ] Customer evaluator SDK documented and tested
- [ ] 300-document test corpus passing all targets
- [ ] No regression in V1 evaluator accuracy

---

*End of Phase 2 Implementation Guide. Phase 2 bridges V1 (MVP) to V2 (Enterprise Platform). Scope discipline applies: V2 features (native Word/Outlook plugins, policy-as-code engine, SAML SSO, VPC deployment) are NOT in Phase 2.*
