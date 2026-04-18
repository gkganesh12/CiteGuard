# CiteGuard Phase 3: V2 Implementation Guide

| | |
|---|---|
| **Phase** | Phase 3 — V2 "From Verifier to Platform" |
| **Duration** | 6 months (13 two-week sprints) |
| **Sprint cadence** | 2-week sprints (Sprints 17–29) |
| **Prerequisite** | Phase 1 (V1) + Phase 2 (V1.1/V1.2) complete and stable |
| **PRD reference** | `docs/PRD_v2.md` |
| **Target** | ≥5 AmLaw 200 firms, $500K ARR, SOC 2 Type II |
| **Last updated** | 2026-04-18 |

---

## 1. Phase Overview

V2 transitions CiteGuard from "AI citation verifier for mid-market firms" to "AI compliance platform for law firms of any size." Three strategic bets:

1. **Meet lawyers where they work** — native surfaces in Google Docs, Microsoft Word, and Outlook
2. **Go upmarket** — SOC 2 Type II, SAML SSO, SCIM, single-tenant VPC deployments for AmLaw 100/200
3. **Become the platform** — firm-defined policy engine, court-admissible audit packages, malpractice carrier integration

### What V2 Ships

| Feature | PRD Ref | Description |
|---------|---------|-------------|
| F11: Google Docs Add-on | REQ-F11.* | Sidebar verification inside Google Docs |
| F12: Microsoft Word Plugin | REQ-F12.* | Taskpane add-in for Word Online/Desktop |
| F13: Outlook Plugin | REQ-F13.* | Pre-send citation verification for emails |
| F14: Firm Policy Engine | REQ-F14.* | Declarative policy-as-code (YAML DSL / OPA) |
| F15: Custom Evaluator SDK (Enterprise) | REQ-F15.* | gVisor-sandboxed Python runtime for custom evaluators |
| F16: SAML SSO + SCIM | REQ-F16.* | Enterprise auth with Okta, Azure AD, OneLogin, Ping |
| F17: Single-Tenant VPC | REQ-F17.* | Dedicated AWS deployment via Terraform |
| F18: Court-Admissible Audit Package | REQ-F18.* | RFC 3161 timestamps, signed PDFs, evaluator version hashes |
| F19: Malpractice Carrier Reporting API | REQ-F19.* | Outbound aggregated metrics to ALPS, Aon, CNA, etc. |
| F20: Multi-Firm Support | REQ-F20.* | Workspace switching for of-counsel / multi-firm lawyers |
| F21: Analytics & Firm Reporting | REQ-F21.* | Firm-wide dashboard, peer benchmarking, scheduled reports |

### What Does NOT Ship in V2

- New verticals (healthcare, accounting) — V3
- International jurisdictions (EU, UK, Canada) — V3
- Proactive draft generation — V3
- FedRAMP certification
- Mobile native apps
- Contract-specific evaluator pack

---

## 2. ADRs Required (12 ADRs)

| ADR | File | Scope |
|-----|------|-------|
| ADR-0019 | `adr/0019-auth-migration.md` | Clerk → WorkOS migration for enterprise SAML/SCIM |
| ADR-0020 | `adr/0020-google-docs-addon.md` | Google Docs add-on architecture (Apps Script, OAuth, sidebar) |
| ADR-0021 | `adr/0021-word-plugin.md` | Word Office Add-in (TypeScript taskpane, AppSource cert) |
| ADR-0022 | `adr/0022-outlook-plugin.md` | Outlook add-in (pre-send scan, fast-path evaluators) |
| ADR-0023 | `adr/0023-policy-engine.md` | Firm Policy Engine (OPA/Rego vs YAML DSL, versioning, simulation) |
| ADR-0024 | `adr/0024-custom-evaluator-sandbox.md` | gVisor sandboxing for customer evaluators in VPC |
| ADR-0025 | `adr/0025-courtlistener-mirror.md` | Local CourtListener mirror (~160GB, daily sync, full-text index) |
| ADR-0026 | `adr/0026-vpc-deployment.md` | Single-tenant VPC (Terraform, PrivateLink, CMK) |
| ADR-0027 | `adr/0027-court-admissible-audit.md` | RFC 3161 timestamps, evaluator hashes, reviewer credentials, DocuSign |
| ADR-0028 | `adr/0028-malpractice-api.md` | Outbound carrier reporting API, aggregation, privacy controls |
| ADR-0029 | `adr/0029-multi-firm-users.md` | Multi-firm user support, workspace switching, session scoping |
| ADR-0030 | `adr/0030-analytics-warehouse.md` | ClickHouse scaling, rollups, peer benchmarking, data retention |

---

## 3. Pricing Tiers (V2 Restructure)

| Tier | Target | Price | Key Features |
|------|--------|-------|--------------|
| Solo | Sole practitioners (1 user) | $79/mo + $1/doc | Core evaluators, web dashboard, email alerts, basic audit |
| Team | 2–20 lawyer firms | $499/mo + $2/doc | + team workspace, Google Docs add-on, Slack alerts |
| Firm | 20–200 lawyer firms | $1,500/mo + $2/doc | + all native surfaces, custom policies, full audit, analytics |
| Enterprise | 200+ lawyer firms | $50K/yr floor + usage | + SSO/SAML, SCIM, VPC, custom evaluator SDK, SLA |

---

## 4. Month-by-Month Implementation

### Month 7 (Sprints 17–18): Foundation

#### Sprint 17 (Weeks 33–34): Auth Migration + CourtListener Mirror

**Sprint Goal:** Migrate from Clerk to WorkOS for enterprise auth. Deploy local CourtListener mirror.

**Backend Components:**

**Auth migration (Clerk → WorkOS):**
- ADR-0019 committed before implementation
- WorkOS SDK integration: `app/common/auth/workos.py`
- SAML 2.0 configuration support
- Existing user migration plan: map Clerk user IDs to WorkOS, maintain sessions
- Feature flag: `USE_WORKOS=true` for gradual rollout
- Fallback: Clerk remains functional during transition
- Update `get_current_user` dependency to support both Clerk and WorkOS

**Local CourtListener mirror:**
- ADR-0025 committed before implementation
- Database: dedicated Postgres schema or separate DB for opinion full-texts
- Storage: ~160GB of opinion text (compressed)
- Sync: daily bulk download from CourtListener bulk data API
- Full-text search: Postgres full-text index (tsvector) on opinion text
- Update evaluators to query local mirror first, CourtListener API as fallback
- Performance: >95% of citation lookups served from local data

**SOC 2 Type II:**
- Engage auditor (Vanta/Drata) — not engineering work, but track as a sprint item
- Begin control documentation

**Marketplace submissions:**
- Submit Google Docs add-on to Google Workspace Marketplace (review takes weeks)
- Submit Word add-in to Microsoft AppSource (cert takes 4-8 weeks)

#### Sprint 18 (Weeks 35–36): API v2 + Multi-Firm Support

**Sprint Goal:** API v2 versioning layer. Multi-firm user support.

**Backend Components:**

**API v2 versioning:**
- URL versioning: `/v2/` prefix for new endpoints
- `/v1/` remains stable (backward compatible)
- New response shapes for native surface optimization (lighter payloads, streaming flags)

**Multi-firm support** (F20):
- ADR-0029 committed
- `user_firm_memberships` table: user_id, firm_id, role, joined_at
- Workspace switching: `POST /v2/auth/switch-firm` — changes active firm context
- Session includes `active_firm_id`
- Documents and audit trails scoped to firm context at submission time
- Solo plan: single-user workspace, $79/mo self-serve signup
- Visual banner in UI showing active firm context

**Frontend:**
- Workspace switcher in top nav (firm name dropdown)
- Active firm banner (prominent, prevents cross-firm accidents)
- Solo plan sign-up flow (credit card, no sales contact, <5 min to first doc)

#### Month 7 Acceptance Criteria

- [ ] WorkOS auth functional alongside Clerk (feature-flagged)
- [ ] Local CourtListener mirror serving >95% of lookups
- [ ] Google Docs add-on submitted to marketplace
- [ ] Word add-in submitted to AppSource
- [ ] Multi-firm workspace switching functional
- [ ] Solo plan self-serve signup working
- [ ] SOC 2 Type II auditor engaged

---

### Month 8 (Sprints 19–20): Native Surfaces Alpha

#### Sprint 19 (Weeks 37–38): Google Docs Add-on

**Sprint Goal:** Google Docs add-on in beta with 3 design partners.

**Frontend Components:**

**Google Docs add-on** (`extensions/google-docs/`):
- ADR-0020 committed
- **Technology:** Google Apps Script (server-side) + HTML Service (sidebar UI)
- **OAuth flow:** Connect add-on to user's CiteGuard workspace
- **Sidebar UI:**
  - "Verify this document" button
  - Real-time flag list with severity indicators
  - Per-flag details (evaluator, explanation, suggested correction)
  - "Jump to flag" — clicking highlights flagged text in the document
  - "Accept suggestion" — one-click text replacement for suggested corrections
- **Data flow:**
  - Document text extracted via `DocumentApp.getBody().getText()`
  - Sent to CiteGuard backend `POST /v2/documents` with `source: "google_docs"`
  - Evaluator results stream back via polling
  - Flags rendered as inline comments and sidebar items
- **Firm routing:** Respects firm-level data residency settings (VPC endpoint if configured)

**Backend:**
- `POST /v2/documents` accepts `source_type: "google_docs"` for telemetry
- Optimized response format for native surfaces (lighter payloads)

#### Sprint 20 (Weeks 39–40): Word Plugin + Outlook Beta

**Sprint Goal:** Word plugin in internal testing. Outlook plugin in beta.

**Frontend Components:**

**Microsoft Word plugin** (`extensions/word/`):
- ADR-0021 committed
- **Technology:** Office Add-in (TypeScript, React-based taskpane)
- **Runtime:** Modern Add-in runtime targeting Word Online + Word for Windows/Mac (Office 365)
- **Taskpane UI:** Matches Google Docs add-on parity — verify button, flag list, jump-to-flag, accept suggestion
- **Tracked changes:** Flagged spans remain flagged as text is edited, until reviewed
- **Deployment:** Per-user install + firm-wide centralized deployment via Microsoft 365 admin center
- **DMS compatibility:** Metadata flows to iManage and NetDocuments if configured

**Outlook plugin** (`extensions/outlook/`):
- ADR-0022 committed
- **Technology:** Outlook Add-in (TypeScript)
- **Pre-send scan:** On compose → Send, scan email body for legal citations
- **Fast-path evaluators only:** Citation Existence, Judge Verification, Quote Verification (lightweight, <1.5s)
- **CRITICAL flag handling:** If CRITICAL flags found, user is prompted with summary and can cancel or override
- **Lighter scope than Word/Google Docs** — email is a notification, not a brief

#### Month 8 Acceptance Criteria

- [ ] Google Docs add-on functional with 3 design partners
- [ ] "Jump to flag" and "Accept suggestion" working in Google Docs
- [ ] Word plugin functional in internal testing (Word Online + Desktop)
- [ ] Outlook pre-send scan completing in <1.5s
- [ ] Outlook CRITICAL flag prompt blocking send until user decision
- [ ] Multi-firm users can use add-ons across workspaces

---

### Month 9 (Sprints 21–22): Native Surfaces GA + Policy Engine

#### Sprint 21 (Weeks 41–42): Native Surfaces GA

**Sprint Goal:** Google Docs + Word plugins approved and public. Outlook in beta.

**Tasks:**
- Google Docs add-on: address marketplace review feedback, publish
- Word plugin: address AppSource certification feedback, publish
- Outlook: expand beta to 5+ users
- Feature parity verification between web, Google Docs, and Word
- Performance tuning for native surfaces (target: p95 <4s including round-trip)

#### Sprint 22 (Weeks 43–44): Policy Engine

**Sprint Goal:** Firm Policy Engine live with 10+ pre-built templates.

**Backend Components:**

**Policy Engine** (`app/policies/`):
- ADR-0023 committed
- **Rule language:** YAML-based DSL (simpler than OPA/Rego for non-technical users)
  ```yaml
  policy: NinthCircuitFirst
  scope: document_type == "appellate_brief"
  rule:
    when: citation.court NOT IN ["9th_Cir", "SCOTUS"]
    and: document.is_appellate == true
    flag: HIGH
    message: "Non-9th Circuit cite in appellate brief"
  ```
- **Policy lifecycle:** Draft → Simulation → Active → Disabled → Archived
- **Versioning:** Git-style version history per policy, one-click rollback
- **Simulation mode:** Test policy against historical document data, preview flag count and false-positive rate before enabling
- **Evaluation:** Policies run in parallel with built-in evaluators. Policy flags appear in review queue with policy name as attribution.
- **Access control:** Only `admin` or `policy_author` role can create/edit policies

**Pre-built templates (10+):**
1. NinthCircuitFirst — flag non-9th Circuit cites in appellate briefs
2. RecentCasesOnly — flag cases older than 20 years
3. NoUnpublishedOpinions — flag unpublished/unreported opinions
4. RequirePincites — flag citations without pincites
5. FederalOnly — flag state court citations in federal filings
6. RequireParallelCites — flag missing parallel citations
7. NoBlockQuotesWithout Attribution — flag long quotes without clear attribution
8. TexasSpecific — flag non-Texas authority in state filings
9. CaliforniaSpecific — flag non-California authority in state filings
10. HighConfidenceOnly — flag evaluator results below 80% confidence

**Frontend Components:**

**Policy management** (`app/(authenticated)/firm/policies/`):
- Policy library: browse pre-built templates, customize, save
- Policy editor: YAML editor with syntax highlighting and validation
- Policy versioning: version history list, diff view, one-click rollback
- Policy simulation: select date range, see projected flag count and FP rate
- Policy list: name, status (draft/simulation/active/disabled), last updated, flag count
- Admin/policy_author access only

#### Month 9 Acceptance Criteria

- [ ] Google Docs add-on published in Google Workspace Marketplace
- [ ] Word plugin published in Microsoft AppSource
- [ ] Outlook plugin in beta with 5+ users
- [ ] Policy engine live with YAML DSL
- [ ] 10+ pre-built policy templates available
- [ ] Policy simulation functional on historical data
- [ ] Policy versioning with rollback working
- [ ] Managing partner can author a policy in <10 minutes

---

### Month 10 (Sprints 23–24): Enterprise Foundation

#### Sprint 23 (Weeks 45–46): SAML SSO + SCIM

**Sprint Goal:** SAML SSO and SCIM provisioning GA.

**Backend Components:**

**SAML SSO** (F16):
- ADR committed as part of ADR-0019
- WorkOS SAML 2.0 integration
- Tested with: Okta, Azure AD / Entra ID, Google Workspace, OneLogin, Ping Identity
- Just-in-time user creation on first SAML login
- Role mapping: SAML `groups` attribute → CiteGuard roles (admin, reviewer, submitter, policy_author)
- Session policies: configurable duration, IP allowlisting (Enterprise tier)
- Every authentication event logged in audit_log

**SCIM 2.0 provisioning:**
- `POST/GET/PATCH/DELETE /scim/v2/Users` — user provisioning/deprovisioning
- `POST/GET/PATCH/DELETE /scim/v2/Groups` — group-to-role mapping
- Joiners/leavers automatically granted/revoked
- Tested with 500-user firm simulation

#### Sprint 24 (Weeks 47–48): VPC Deployment + Custom Evaluator Sandbox

**Sprint Goal:** First VPC deployment in progress. Custom evaluator SDK with gVisor sandbox.

**Backend Components:**

**Single-tenant VPC deployment** (F17):
- ADR-0026 committed
- **Terraform modules** (`infra/terraform/`):
  - VPC + subnets + security groups
  - RDS Postgres (customer's AWS account or CiteGuard-managed)
  - Redis (ElastiCache)
  - ECS Fargate for API + workers
  - S3 for PDF exports
  - PrivateLink endpoint for customer connectivity
- **Customer-managed encryption keys (CMK):** AWS KMS integration
- **Deployment automation:**
  - `deploy.sh` script for new tenant provisioning
  - Status dashboard for CiteGuard engineering visibility
  - Target: <15 business days for first deployment, <5 days ongoing
- **Data isolation:** No data leaves customer's AWS region
- **External data:** CourtListener mirror inside VPC, OR via CiteGuard shared cache (customer's choice)

**Custom evaluator sandbox** (F15):
- ADR-0024 committed
- **gVisor runtime:** Sandboxed Python environment for customer evaluators
- **Security:** No filesystem access, restricted network (allowlisted endpoints only), 5s timeout, memory limits
- **Available context:** document text, parsed citations, metadata, firm API endpoints
- **Deployment:** Only in VPC deployments (Enterprise tier)
- **SDK:** Extends V1.2 Python SDK with gVisor execution wrapper

#### Month 10 Acceptance Criteria

- [ ] SAML SSO working end-to-end with Okta and Azure AD
- [ ] SCIM provisioning verified with 500-user simulation
- [ ] Role mapping from SAML groups functional
- [ ] First VPC deployment in progress (Terraform applied)
- [ ] Custom evaluator gVisor sandbox running customer code
- [ ] 5s timeout enforced in sandbox
- [ ] All auth events in audit log

---

### Month 11 (Sprints 25–26): Court-Admissible Audit + Carrier Integration

#### Sprint 25 (Weeks 49–50): Court-Admissible Audit Package

**Sprint Goal:** Court-admissible audit package GA.

**Backend Components:**

**Court-admissible audit package** (F18):
- ADR-0027 committed
- Extends V1 audit PDF export with:
  - **RFC 3161 cryptographic timestamp** via trusted timestamp authority (FreeTSA or DigiCert)
  - **Evaluator version hashes** — code fingerprint (git SHA) at time of verification
  - **Reviewer bar credentials** — bar number, jurisdiction, captured at firm setup
  - **CourtListener snapshot reference** — CourtListener opinion ID + retrieval timestamp for reproducibility
  - **Notarized PDF signing** — DocuSign CLM or equivalent eIDAS-compliant signing
- **Retention:** Court-admissible packages stored minimum 7 years (regardless of firm settings)
- **Re-verification:** Given historical package + inputs, any party can re-run evaluators at same version → identical output
- **Export formats:** PDF (signed), JSON (machine-readable), CSV (summary)

**Frontend:**
- Enhanced export UI: format selector (PDF/JSON/CSV)
- Bar credentials management in firm settings
- Audit package history with RFC 3161 timestamp display

#### Sprint 26 (Weeks 51–52): Malpractice Carrier API + Analytics

**Sprint Goal:** Malpractice carrier reporting API live. Analytics with peer benchmarking.

**Backend Components:**

**Malpractice carrier reporting API** (F19):
- ADR-0028 committed
- Outbound API: firm opts in to share anonymized, aggregated metrics
- Metrics shared: flag counts by severity, review rates, override rates (monthly)
- **No client-identifying data** — aggregates only
- Pre-built integration templates for top 5 carriers: ALPS, Aon, CNA, Markel, Ironshore
- Firm controls: opt-in, revoke, preview report before sending
- Monthly scheduled job for report generation and delivery

**Analytics with peer benchmarking** (F21):
- `GET /v2/analytics/benchmarking` — anonymized peer comparison
- "Firms of your size have an average critical-flag rate of X; you're at Y"
- Requires 20+ firms per size bracket for statistical validity
- Scheduled reports: monthly PDF/email summary to managing partner
- Personal analytics: each lawyer sees own flag rate (private, opt-out possible)

**Frontend:**
- Carrier reporting settings: opt-in toggle, carrier selection, preview report
- Benchmarking chart on analytics dashboard
- Scheduled report configuration (monthly email to specified recipients)

#### Month 11 Acceptance Criteria

- [ ] Court-admissible audit package with RFC 3161 timestamp
- [ ] Evaluator version hashes in audit package
- [ ] Reviewer bar credentials in audit package
- [ ] Signed PDF via DocuSign CLM or equivalent
- [ ] Re-verification produces identical output
- [ ] Malpractice carrier API live with 1+ carrier integrated
- [ ] Peer benchmarking chart functional (with sufficient data)
- [ ] Scheduled monthly reports configured and delivering

---

### Month 12 (Sprints 27–29): V2 Launch

#### Sprint 27 (Weeks 53–54): Solo Tier + Polish

**Sprint Goal:** Solo tier ($79/mo) live. UX polish across all surfaces.

**Backend:**
- Solo tier Stripe billing: $79/mo + $1/doc
- Team tier: $499/mo + $2/doc (new tier)
- Tier-based feature gating middleware
- Rate limits adjusted per tier

**Frontend:**
- Solo sign-up flow: credit card → workspace → first doc in <5 minutes
- Tier upgrade/downgrade flow
- Feature gating UI (locked features show upgrade CTA)

#### Sprint 28 (Weeks 55–56): Security + Compliance Finalization

**Sprint Goal:** SOC 2 Type II report, penetration test, bug bounty.

**Tasks:**
- SOC 2 Type II audit completion with Vanta/Drata
- Penetration test by independent third party — remediate all high/critical findings
- Bug bounty program launch (HackerOne or equivalent)
- Multi-region active-passive failover test (us-east-1 → us-west-2)
- Enterprise SLA documentation: 99.9% uptime with credits
- Written DPA finalized

#### Sprint 29 (Weeks 57–58): V2 Launch

**Sprint Goal:** All V2 release criteria met. Public launch.

**Tasks:**
- All release criteria verified (PRD_v2.md §13)
- Enterprise customer case studies published
- Enterprise sales playbook documented
- Training materials + certification for design partners
- Customer success process live (dedicated CSM for Enterprise)
- Public announcement: LinkedIn, Legaltech News, ABA Journal
- On-call rotation of ≥3 engineers

---

## 5. Infrastructure Changes (V2 vs V1)

| Component | V1 | V2 |
|-----------|----|----|
| Auth | Clerk | WorkOS (SAML/SCIM) |
| CourtListener | Live API + Redis cache | Local mirror (~160GB) + API fallback |
| Hosting | Fly.io (single region) | Fly.io multi-region + VPC deployments (AWS) |
| DB | Single Postgres (Fly.io/RDS) | Multi-tenant Postgres + per-tenant VPC Postgres |
| Analytics | ClickHouse Cloud (basic) | ClickHouse cluster (scaled, rollups) |
| PDF signing | None | RFC 3161 + DocuSign CLM |
| Custom evaluators | Process isolation (V1.2) | gVisor sandbox (V2) |
| Regions | us-east-1 only | us-east-1 + us-west-2 (active-passive) |

---

## 6. Architecture Diagram Updates (V2)

| Diagram | Content |
|---------|---------|
| New: `arc_diagrams/backend/vpc-deployment.mmd` | VPC architecture: Terraform, ECS, RDS, PrivateLink |
| New: `arc_diagrams/backend/courtlistener-mirror.mmd` | Local mirror sync, full-text index, fallback flow |
| New: `arc_diagrams/backend/policy-engine.mmd` | Policy lifecycle, evaluation, versioning |
| New: `arc_diagrams/backend/custom-evaluator-sandbox.mmd` | gVisor runtime, security boundaries |
| New: `arc_diagrams/backend/court-admissible-audit.mmd` | RFC 3161, signing, re-verification flow |
| New: `arc_diagrams/frontend/native-surfaces.mmd` | Google Docs, Word, Outlook add-in architecture |
| Updated: `arc_diagrams/backend/system-overview.mmd` | Full V2 component diagram |
| Updated: `arc_diagrams/backend/auth-flow.mmd` | WorkOS SAML + SCIM flow |

---

## 7. Team Requirements (V2)

V2 cannot be executed by a solo founder. Minimum team:

| Role | Count | Focus |
|------|-------|-------|
| CEO / Founder | 1 | AmLaw sales, vision, fundraising |
| Head of Engineering | 1 | Architecture, platform expansion |
| Backend Engineers | 2 | API v2, policy engine, mirror sync, VPC |
| Frontend Engineer | 1 | Native surfaces (Google Docs, Word, Outlook) |
| Platform/DevOps Engineer | 1 | VPC deployments, SOC 2, SSO infrastructure |
| Designer | 1 | Native surface UX (contract or FT) |
| Enterprise AE | 1 | AmLaw sales cycle management |
| Customer Success Manager | 1 | Enterprise onboarding |

**Total: 9 people.** Annual burn: ~$1.35M. Requires seed round ($2–4M) before V2 execution.

---

## 8. Key Risks (Phase 3)

| Risk | Severity | Mitigation |
|------|----------|------------|
| Google/Microsoft marketplace approval delays | Medium | Submit in Month 7 Week 1; have web fallback always |
| SOC 2 Type II reveals control gaps | Medium-High | Engage auditor at V2 start (not end) via Vanta/Drata |
| Enterprise deal cycles 9–12 months | High | Start sales motion in Month 7, not at V2 launch |
| WorkOS migration disrupts existing customers | Medium | Feature-flagged rollout, session migration, rollback path |
| VPC deployment ops overhead | High | Limit to 1–2 deals, $50K floor, full automation before scaling |
| Policy engine false positives drive frustration | Medium | Mandatory simulation mode before any policy goes live |
| Native surface DOM instability | Medium | Test against multiple versions, graceful degradation |

---

## 9. V2 Release Criteria (Definition of Done)

### Functional (PRD_v2.md §13.1)
- [ ] Google Docs add-on published and approved
- [ ] Word plugin published and approved
- [ ] Outlook plugin published and approved
- [ ] Policy engine live with 10+ pre-built templates
- [ ] Custom evaluator SDK tested with 1 design partner
- [ ] SAML SSO working with Okta and Azure AD
- [ ] SCIM provisioning verified with 2 design partners
- [ ] VPC deployment completed for ≥1 enterprise customer
- [ ] Court-admissible audit package accepted by ≥1 malpractice carrier
- [ ] Malpractice carrier reporting API live
- [ ] Multi-firm user support shipped
- [ ] Analytics dashboard with benchmarking live

### Non-Functional (PRD_v2.md §13.2)
- [ ] SOC 2 Type II report issued
- [ ] Penetration test completed, high/critical remediated
- [ ] Bug bounty program launched
- [ ] Local CourtListener mirror serving ≥95% of lookups
- [ ] p95 native-surface latency <4s
- [ ] Active-passive multi-region tested via failover drill

### Business (PRD_v2.md §13.3)
- [ ] ≥5 AmLaw 200 firms signed
- [ ] ≥100 total paying firms
- [ ] MRR ≥ $40K
- [ ] ≥1 malpractice carrier public endorsement
- [ ] Written SLAs live on Enterprise tier
- [ ] Enterprise sales playbook documented

### Operational (PRD_v2.md §13.4)
- [ ] On-call rotation ≥3 engineers
- [ ] Runbooks for top 15 incidents
- [ ] Customer success process live
- [ ] Training materials for design partners

---

## 10. Post-V2: V3 Preview

V3 is where CiteGuard expands beyond legal. NOT for V2 execution:

- **Healthcare vertical** — clinical guideline adherence, ICD-10/CPT validation, HIPAA audit trails
- **Accounting vertical** — GAAP compliance checks, SOX evidence, audit trail for AI-assisted attestation
- **International expansion** — UK (Bar Standards Board), EU (DAC7/MiCA)
- **Proactive mode** — autocomplete with verified citations as lawyers draft
- **Potential acquisition target** — Thomson Reuters, LexisNexis, malpractice carrier

---

*End of Phase 3 Implementation Guide. V2 is the "prove the platform" release. Scope discipline is critical — resist the urge to add healthcare/accounting in V2. Legal TAM is large enough.*
