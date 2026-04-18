# CiteGuard V2 — Product Requirements Document

| | |
|---|---|
| **Document status** | DRAFT v0.1 |
| **Product** | CiteGuard |
| **Release** | V2 — "From Verifier to Platform" |
| **Target launch** | Month 12 from project start (~6 months post-V1 launch) |
| **Owner** | Founder / Head of Product |
| **Last updated** | Day 0 |
| **Predecessor** | V1 PRD, V1.1 + V1.2 releases |

---

## 1. Executive Summary

V2 is the transition release — the moment CiteGuard stops being "the AI citation verifier for mid-market firms" and becomes "the AI compliance platform for law firms of any size." The three bets:

1. **Meet lawyers where they work.** Native surfaces in Google Docs, Microsoft Word, and Outlook — because lawyers don't want to copy/paste into another app.
2. **Go upmarket.** Land AmLaw 100/200 firms with SOC 2 Type II, SSO/SAML, and single-tenant VPC deployments.
3. **Become the platform, not the point tool.** Let firms define their own rules, plug in custom evaluators, and wire CiteGuard's audit trail into their malpractice carrier, bar association, and internal GRC workflows.

V2 does **not** add new verticals (healthcare, accounting). Those are V3. V2's job is to *own* legal end-to-end and make CiteGuard the standard referenced in AmLaw RFPs and malpractice insurance questionnaires.

---

## 2. Context — What V1, V1.1, and V1.2 Shipped

Before scoping V2, assume the following is live and stable:

| Release | Shipped |
|---------|---------|
| V1 | 5 deterministic evaluators (federal), SDK + proxy, review queue, audit PDF, Slack alerts, Clerk auth |
| V1.1 | 5 additional evaluators (Jurisdiction, Statutory Currency, Holding Accuracy [LLM-judge], PII, Opposing Authority); state case law for CA/NY/TX/FL; dark mode; SSO via OIDC |
| V1.2 | Custom rules UI (firm-defined regex + keyword flags); customer-defined evaluator SDK (Python); analytics dashboard |

V2 extends these. Not a re-architecture.

**Assumed V2 starting state:**
- ~30–60 paying firms, ~$80–150K MRR
- Team of 3–6 (founder + 2–3 engineers + 1 designer + 1 legal-ops lead)
- 18 months of production evaluator tuning data
- 2–3 reference customers willing to speak publicly

---

## 3. Problem Statement — What's Still Broken After V1

Even with V1.2 shipped, three user frustrations persist:

**Friction 1: Workflow interruption.**
Associates draft in Word/Google Docs. They finish a section, open CiteGuard's web dashboard, paste text, wait, switch back, fix, repeat. This is better than getting sanctioned, but it's still 2-3 minutes of context switching per round. Lawyers drafting at speed abandon the tool after the first week.

**Friction 2: "It doesn't know our rules."**
Boutique firms have practice-specific preferences: a tax controversy firm wants flags on cites to non-tax-court cases; a 9th Circuit specialty firm wants a flag on any 11th Circuit cite. V1.2 shipped a custom-rules UI, but it's basic regex. Firms with $50K+ in annual spend are asking for real policy-as-code.

**Friction 3: AmLaw firms won't sign.**
Five AmLaw 100 firms have had enthusiastic product calls in V1.1–V1.2. All five stalled at procurement with the same blockers: no SOC 2 Type II, no SSO/SAML, no VPC deployment option, data residency concerns, and no written SLAs. Until these ship, the 250 biggest law firms in the U.S. cannot buy CiteGuard.

V2 solves all three.

---

## 4. V2 Goals & Non-Goals

### 4.1 Goals (in scope)

| # | Goal |
|---|------|
| G1 | Native drafting-surface integrations: Google Docs add-on, Microsoft Word plugin, Outlook plugin |
| G2 | Firm-defined policy engine (declarative rules language, not just regex) |
| G3 | Enterprise-grade deployment: SOC 2 Type II, SAML SSO, SCIM user provisioning |
| G4 | Single-tenant VPC deployment option (AWS PrivateLink) for AmLaw/regulated firms |
| G5 | Court-admissible audit package (expanded beyond V1's basic PDF) |
| G6 | Firm-level analytics with AI-usage trend reporting |
| G7 | Malpractice carrier integration API (export audit metrics to carriers like ALPS, Aon, Attorney's Liability Protection) |
| G8 | Multi-firm support for individual lawyers (for sole practitioners / of-counsel roles) |
| G9 | Achieve ≥5 AmLaw 200 firms on contracts by end of V2 |
| G10 | Achieve $500K ARR (up from ~$150K pre-V2) |

### 4.2 Non-Goals (explicitly OUT of V2 scope — deferred to V3 or later)

| # | Non-goal |
|---|----------|
| NG1 | New verticals (healthcare, accounting, insurance). Stay focused on legal. |
| NG2 | Proactive draft generation ("suggest the right citation before they write the wrong one"). V3. |
| NG3 | International jurisdictions (EU, UK, Canada). V3. |
| NG4 | FedRAMP certification. Only pursue if government sales >15% of pipeline. |
| NG5 | Mobile native apps (lawyers work on desktop; mobile is a want, not a need). |
| NG6 | AI-generated argument drafting (not our domain — we verify, not create). |
| NG7 | Contract-specific evaluator pack (defer; firms asking for this are 20% of TAM). |
| NG8 | Deposition transcript verification (interesting but adjacent — V3). |

---

## 5. Success Metrics

### 5.1 Primary metrics (must hit for V2 launch success)

| Metric | Target | Measurement |
|--------|--------|-------------|
| AmLaw 200 firms on contract | ≥ 5 | CRM |
| Total paying firms | ≥ 100 | Stripe |
| MRR | ≥ $40K | Stripe |
| ARR | ≥ $500K | Stripe |
| % of documents submitted via native surface (not web) | ≥ 50% | App telemetry |
| SOC 2 Type II report issued | Yes | Auditor deliverable |
| p95 end-to-end latency (native surface) | < 4,000 ms | App telemetry |
| Net revenue retention (12-month cohort) | ≥ 115% | Stripe + billing |

### 5.2 Secondary metrics (track, don't gate)

- % of firms with custom policies active
- % of firms using VPC deployment
- Documents verified per firm per month
- Logo churn (target: <5% annualized)
- Audit export downloads per firm per month (proxy for real compliance value)
- Mean time from sign-up to first native-surface submission

---

## 6. Target Users & Personas (Expanded for V2)

### 6.1 ICP (evolved)

**Segment A — Mid-market (V1 core):** 20–200 lawyer firms. Already our bread and butter. V2 improves retention and expansion revenue through native surfaces and custom policies.

**Segment B — Enterprise / AmLaw 100-200 (NEW in V2):** 300-3,000 lawyer firms. Multi-office, often multi-country. Strict procurement gates. High ACV potential ($50K–$300K/year).

**Segment C — Sole practitioner / small firm (OPPORTUNISTIC):** 1–20 lawyer firms. Price-sensitive but high volume. Multi-firm support opens this up. Lighter service; self-serve signup.

### 6.2 New personas introduced in V2

**P5: AmLaw CIO / Head of Legal Ops (Elena)**
- 48 years old, runs technology for a 1,200-lawyer firm
- Manages vendor procurement, security reviews, and integration with firm-wide systems (Aderant, iManage, NetDocuments)
- Will not sign without SOC 2 Type II, SAML SSO, DPA, written SLA, and references from peer AmLaw firms
- Success criteria: "Deployable without giving our CISO a panic attack. Integrates with our existing identity provider. Has an SLA with credits."

**P6: Sole Practitioner (Marcus)**
- 38 years old, solo family law practitioner
- Uses ChatGPT daily for first drafts
- Cannot afford $1,500/month, but would pay $79/month for document-level verification
- Represents the long-tail opportunity
- Success criteria: "Cheap. Self-serve. Works with my Google Docs workflow. Doesn't need IT."

### 6.3 Existing personas updated

- **Margaret (Managing Partner):** Now also uses the firm-wide analytics dashboard to report AI-risk posture to the executive committee monthly.
- **Dana (Associate):** Primary use is now the Word plugin, not the web dashboard. Submits to CiteGuard without ever leaving Word.
- **Raj (Senior Associate Reviewer):** Still uses the review queue, but many low-severity flags are auto-resolved by firm custom rules before reaching him.
- **Tom (IT Director):** Promoted role in V2 — he's the primary integration owner for the Word/Google/Outlook plugins, SSO, and SCIM.

---

## 7. User Stories (V2)

### Epic 7: Draft in place, verify in place
- **US-16** As an associate, I want CiteGuard to verify my document inside Google Docs, so I don't copy/paste.
- **US-17** As an associate, I want inline underlines under problematic citations in Word, with a sidebar showing the issue and fix.
- **US-18** As a litigator, I want Outlook to verify any case citations I'm about to email, so I don't send a hallucinated cite to opposing counsel.

### Epic 8: Encode firm-specific rules
- **US-19** As a managing partner, I want to write a policy like "flag any cite to a non-Ninth-Circuit federal case in an appellate brief" and have CiteGuard enforce it, so our firm style is automatic.
- **US-20** As an IT director, I want to version firm policies, so I can roll back a rule that's generating too many false positives.
- **US-21** As a custom-evaluator developer, I want to publish an internal evaluator (e.g., "client conflict check against our CRM") via CiteGuard's SDK, so it runs alongside built-in evaluators.

### Epic 9: Deploy in AmLaw-grade environments
- **US-22** As an AmLaw CIO, I want SAML SSO with my Okta/Azure AD, so access is managed centrally.
- **US-23** As an AmLaw CIO, I want SCIM user provisioning, so joiners/leavers are automatically granted/revoked.
- **US-24** As an AmLaw CISO, I want a single-tenant VPC deployment where our data never leaves our AWS account, so I can sign off in security review.
- **US-25** As an AmLaw CISO, I want SOC 2 Type II and a DPA, so my compliance team can sign.

### Epic 10: Prove compliance externally
- **US-26** As a managing partner, I want to export a court-admissible audit package that includes evaluator version hashes, reviewer credentials, and a notarized timestamp, so it holds up if a judge asks how we reviewed AI output.
- **US-27** As a firm's risk committee chair, I want to send monthly AI-usage reports to our malpractice carrier (ALPS, CNA, etc.), so we get premium discounts.

### Epic 11: Serve the long tail (sole practitioners)
- **US-28** As a sole practitioner, I want to sign up with a credit card at $79/month and start verifying documents immediately, without talking to sales.
- **US-29** As an of-counsel lawyer working across three firms, I want one CiteGuard account that connects to all three firms' workspaces, so I don't juggle logins.

### Epic 12: Analytics and insight
- **US-30** As a managing partner, I want to see trends over time — are our AI hallucinations getting better or worse? Which practice group has the most flags? — so I can allocate training.
- **US-31** As a managing partner, I want anonymized benchmarking against peer firms, so I know where we stand.

---

## 8. V2 Feature Requirements (Detailed)

### F11 — Google Docs Add-on

**REQ-F11.1** Google Workspace Marketplace listing, approved and published.

**REQ-F11.2** Sidebar UI (right-panel add-on) that renders: "Verify this document" button, real-time flag list, severity indicators.

**REQ-F11.3** OAuth flow connects the add-on to the user's CiteGuard workspace.

**REQ-F11.4** On verify: document text is sent (via Google's `DocumentApp` API) to CiteGuard backend. Evaluator results return and render as inline comments and sidebar items.

**REQ-F11.5** "Jump to flag" — clicking a sidebar item highlights the flagged text in the doc.

**REQ-F11.6** "Accept suggestion" — where the evaluator provides a suggested fix, one click replaces the flagged text.

**REQ-F11.7** Respects firm-level data residency settings — if firm is on VPC deployment, add-on routes to the firm's private endpoint.

**Acceptance:** Associate can install, connect, and verify a document without leaving Google Docs in <2 minutes.

---

### F12 — Microsoft Word Plugin (Office Add-in)

**REQ-F12.1** Microsoft AppSource listing, approved and published.

**REQ-F12.2** Taskpane add-in targeting Word Online, Word for Windows/Mac (Office 365 with Modern Add-in runtime).

**REQ-F12.3** Behavior matches F11 (Google Docs parity).

**REQ-F12.4** Supports both per-user install and firm-wide centralized deployment (via Microsoft 365 admin center).

**REQ-F12.5** Works with tracked changes — flagged spans remain flagged as text is edited, until reviewed.

**REQ-F12.6** Compatible with iManage and NetDocuments integrations (metadata flows to the document management system).

**Acceptance:** AmLaw IT can deploy the plugin firm-wide in <30 minutes via admin center. Associate verification flow matches Google Docs parity.

---

### F13 — Outlook Plugin

**REQ-F13.1** Outlook add-in (Office 365) that scans email drafts for legal citations.

**REQ-F13.2** Pre-send scan: on Send, if CRITICAL flags exist, user is prompted with a summary and can cancel.

**REQ-F13.3** Primary use case: lawyer quotes a case in an email to opposing counsel, client, or court staff — prevents hallucinated cites leaving the firm.

**REQ-F13.4** Lighter scope than Word/Google Docs: only citation existence, judge verification, and quote verification run (fast-path evaluators only).

**Acceptance:** Pre-send scan completes in <1.5 seconds; CRITICAL flags block send unless user explicitly overrides.

---

### F14 — Firm Policy Engine (Policy-as-Code)

**REQ-F14.1** Declarative rule language (YAML-based DSL or Open Policy Agent / Rego). Example:

```yaml
policy: NinthCircuitFirst
scope: document_type == "appellate_brief"
rule:
  when: citation.court NOT IN ["9th_Cir", "SCOTUS"]
  and: document.is_appellate == true
  flag: HIGH
  message: "Non-9th Circuit cite in appellate brief"
```

**REQ-F14.2** Policy library in UI: browse pre-built templates (state-specific, practice-specific), customize, save.

**REQ-F14.3** Policies versioned (Git-style). Rollback to prior version is a single click.

**REQ-F14.4** Policy simulation: test a policy against historical document data before enabling, to preview false-positive rate.

**REQ-F14.5** Active policies are evaluated in parallel with built-in evaluators. Policy flags appear in the review queue with the policy name as attribution.

**REQ-F14.6** Policy editing access control: only users with `admin` or `policy_author` role.

**Acceptance:** A managing partner can author a simple policy, simulate it, enable it firm-wide, and see results within 10 minutes without developer help.

---

### F15 — Custom Evaluator SDK (Enterprise)

**REQ-F15.1** Python SDK for customer engineering teams to define evaluators that run alongside CiteGuard's built-in ones. Example:

```python
from citeguard import Evaluator, Severity, Flag

class ClientConflictCheck(Evaluator):
    name = "client_conflict"

    def evaluate(self, document, context):
        # Custom logic: call firm's CRM to check if
        # cited opposing parties conflict with existing clients
        ...
        return [Flag(severity=Severity.CRITICAL, ...)]
```

**REQ-F15.2** Evaluators run in a sandboxed Python runtime inside the customer's VPC deployment (Enterprise tier only, for security reasons).

**REQ-F15.3** Customer-defined evaluators have access to: document text, parsed citations, metadata, firm's own API endpoints (for CRM lookups, etc.).

**REQ-F15.4** Timeout per custom evaluator: 5 seconds max. Exceed → flag timeout, don't fail the document.

**REQ-F15.5** Available only on VPC-deployment and Enterprise tier (not on multi-tenant SaaS).

**Acceptance:** A customer's engineer can write, deploy, and see results of a custom evaluator in their dev environment in <1 day.

---

### F16 — SAML SSO + SCIM Provisioning

**REQ-F16.1** SAML 2.0 support via industry-standard library (e.g., `python3-saml` or managed via Clerk Enterprise tier).

**REQ-F16.2** Tested with Okta, Azure AD / Entra ID, Google Workspace, OneLogin, Ping Identity.

**REQ-F16.3** SCIM 2.0 endpoint for user provisioning/deprovisioning.

**REQ-F16.4** Just-in-time user creation on first SAML login.

**REQ-F16.5** Role mapping: SAML attributes (e.g., `groups`) map to CiteGuard roles (admin, reviewer, submitter, policy_author).

**REQ-F16.6** Session policies: configurable session duration, IP allowlisting (Enterprise tier).

**REQ-F16.7** Audit log records every authentication event, SSO or otherwise.

**Acceptance:** AmLaw IT can configure SAML SSO end-to-end in <2 hours with documentation only; SCIM auto-provisioning works for a 500-user firm.

---

### F17 — Single-Tenant VPC Deployment (Enterprise)

**REQ-F17.1** Single-tenant deployment into the customer's AWS account (via CloudFormation stack or Terraform module) OR CiteGuard-managed dedicated AWS account with PrivateLink to the customer.

**REQ-F17.2** All CiteGuard components (API, workers, Postgres, ClickHouse, PDF generator) run in the single tenant.

**REQ-F17.3** Customer controls encryption keys via AWS KMS (CMK option).

**REQ-F17.4** Data never leaves the customer's AWS region.

**REQ-F17.5** External data (CourtListener, FJC) retrieved via customer's egress or via a CiteGuard-operated shared cache (customer's choice).

**REQ-F17.6** Deployment automation: CiteGuard engineering deploys + maintains, with customer visibility via a status dashboard.

**REQ-F17.7** SLA: 99.9% uptime, written, with credits.

**REQ-F17.8** Pricing: $50K floor + per-document usage; custom based on size.

**Acceptance:** First Enterprise customer deployed end-to-end in <15 business days from contract signing. Ongoing deployments automate to <5 days.

---

### F18 — Court-Admissible Audit Package

**REQ-F18.1** Extends V1's Audit PDF Export. New capabilities:
- Cryptographic timestamp via RFC 3161 trusted timestamp authority (e.g., FreeTSA, DigiCert)
- Evaluator version hashes (code fingerprint at time of verification)
- Reviewer bar credentials (captured at firm setup, displayed in report)
- CourtListener / source data snapshot reference (so evaluator result is reproducible)
- Notarized PDF signing via eIDAS-equivalent (DocuSign CLM or equivalent integration)

**REQ-F18.2** Retention: court-admissible packages stored minimum 7 years (regardless of firm retention settings).

**REQ-F18.3** Re-verification: given a historical package and its inputs, any party can re-run the evaluators at the same version and verify identical output (determinism requirement).

**REQ-F18.4** Export formats: PDF (signed), JSON (machine-readable), CSV (summary).

**Acceptance:** One design partner's malpractice carrier reviews and accepts the audit package as evidence of "reasonable AI-use controls."

---

### F19 — Malpractice Carrier Reporting API

**REQ-F19.1** Outbound API: firm opts in to share anonymized, aggregated metrics (flag counts by severity, review rates, override rates) with their malpractice carrier on a monthly schedule.

**REQ-F19.2** Pre-built integration templates with the top 5 legal malpractice carriers (ALPS, Aon, CNA, Markel, Ironshore).

**REQ-F19.3** Firm controls: opt-in, can revoke, can preview report before sending.

**REQ-F19.4** No client-identifying data ever leaves — aggregates only.

**REQ-F19.5** Partnership play: co-sell with carriers offering premium discounts to CiteGuard customers. (Business development, not engineering.)

**Acceptance:** 1+ malpractice carrier publicly endorses CiteGuard for premium discounts by end of V2.

---

### F20 — Multi-Firm Support for Individual Lawyers

**REQ-F20.1** An individual lawyer can be a member of multiple firm workspaces.

**REQ-F20.2** On login, user selects which firm context they're working in.

**REQ-F20.3** Documents and audit trails are scoped to the firm context at time of submission.

**REQ-F20.4** Of-counsel / contract lawyer use case: lawyer works for multiple firms concurrently.

**REQ-F20.5** Sole practitioner use case: $79/month self-serve "Solo" plan, single-user workspace.

**REQ-F20.6** Conflict management: lawyer's session clearly indicates active firm; visual banner prevents cross-firm accidents.

**Acceptance:** Of-counsel lawyer can work across 3 firms in a single day with zero data crossover; sole practitioner can sign up and submit first document in <5 minutes without sales contact.

---

### F21 — Analytics & Firm-Level Reporting

**REQ-F21.1** Firm-wide dashboard (admin-only):
- Documents verified (over time, by practice group, by submitter)
- Flag rate (critical/high/medium/advisory) over time
- Evaluator-specific trends (which failure modes are most common?)
- Reviewer throughput
- Override rate (high = evaluator may be too aggressive)
- Time-to-resolution

**REQ-F21.2** Anonymized peer benchmarking: "Firms of your size have an average critical-flag rate of X; you're at Y." (Requires 20+ firm cohort per size bracket.)

**REQ-F21.3** Scheduled reports: monthly PDF/email summary to managing partner / risk committee.

**REQ-F21.4** Export: CSV of all flags + actions for the firm's own BI tools.

**REQ-F21.5** Personal (user) analytics: each lawyer sees their own flag rate over time (private; opt-out possible).

**Acceptance:** Managing partner can open dashboard at firm all-hands and present AI-risk posture without pre-work.

---

## 9. Non-Functional Requirements (V2 deltas from V1)

### 9.1 Performance
- **NFR-P1.V2** p95 end-to-end latency for native-surface verification: <4,000 ms (includes Google/MS round-trip)
- **NFR-P2.V2** Firm dashboard loads in <800 ms p95 even for firms with >1M historical documents

### 9.2 Availability
- **NFR-A1.V2** Multi-tenant SaaS uptime: 99.9% (was 99.5% in V1)
- **NFR-A2.V2** Enterprise VPC deployments: 99.9% uptime SLA with credits
- **NFR-A3.V2** Regional redundancy: active-passive across us-east-1 and us-west-2

### 9.3 Security
- **NFR-S1.V2** SOC 2 Type II report (issued by end of V2 release)
- **NFR-S2.V2** Annual penetration test from an independent third party
- **NFR-S3.V2** HIPAA readiness (not required for legal, but unlocks later healthcare vertical — do it now to avoid re-architecture)
- **NFR-S4.V2** Customer-managed encryption keys (CMK) option for Enterprise tier
- **NFR-S5.V2** IP allowlisting for Enterprise tier
- **NFR-S6.V2** Bug bounty program launched (via HackerOne or equivalent)

### 9.4 Scalability
- **NFR-Sc1** Support firms with 3,000+ lawyers (AmLaw top tier)
- **NFR-Sc2** Sustain 100 concurrent document submissions without latency degradation
- **NFR-Sc3** Local CourtListener mirror serves >95% of citation lookups without external API calls (V1 relied on live CourtListener with caching; V2 runs a local read replica)

### 9.5 Data residency
- **NFR-D1.V2** Multi-region support: firms can opt for us-east-1 or us-west-2 in V2; EU region deferred to V3

---

## 10. Architecture Changes (V2 vs V1)

### 10.1 New components

```
V1 baseline + the following:

┌──────────────────────────────────────┐
│  Add-in Surface Layer                │
│  - Google Docs add-on (Apps Script)  │
│  - Word Office add-in (TypeScript)   │
│  - Outlook add-in (TypeScript)       │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Public API v2 (versioned)           │
│  Native-surface-optimized endpoints  │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  Policy Engine (OPA-based)           │
│  - Rule registry                     │
│  - Simulator                         │
│  - Versioning                        │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  Custom Evaluator Sandbox            │
│  (runs only in VPC deployments)      │
│  - gVisor-isolated Python runtime    │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  Local CourtListener Mirror          │
│  - Daily sync from CL bulk data      │
│  - ~160 GB opinion full-texts        │
│  - Postgres full-text index          │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  Enterprise Deployment Automation    │
│  - Terraform modules                 │
│  - Deployment dashboard              │
│  - PrivateLink endpoints             │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  Analytics Data Warehouse            │
│  - ClickHouse cluster (scaled)       │
│  - Scheduled rollups for dashboards  │
└──────────────────────────────────────┘
```

### 10.2 Migration considerations

- **Clerk → Enterprise auth layer:** Clerk may not scale to enterprise SAML requirements at reasonable cost. Evaluate migration to WorkOS or self-hosted Keycloak.
- **Multi-tenant DB → per-tenant schema for Enterprise:** VPC deployments get their own DB instance. Multi-tenant SaaS stays shared DB.
- **CourtListener dependency → local mirror:** Primary lookups now against local replica. CourtListener only for real-time updates (nightly sync).

---

## 11. Pricing (V2)

### 11.1 Tier structure (restructured in V2)

| Tier | Target | Price | Features |
|------|--------|-------|----------|
| **Solo** | Sole practitioners, 1 user | $79/mo flat + $1/doc | Core evaluators, web dashboard, email alerts, basic audit export |
| **Team** | 2–20 lawyer firms | $499/mo + $2/doc | Solo features + team workspace, basic native surfaces (Google Docs), Slack alerts |
| **Firm** (V1's tier, renamed) | 20–200 lawyer firms | $1,500/mo + $2/doc | Team features + all native surfaces (Word, Outlook, Google Docs), custom policies, full audit export, analytics |
| **Enterprise** (NEW) | 200+ lawyer firms | $50K/yr floor + usage | Firm features + SSO/SAML, SCIM, VPC deployment, custom evaluator SDK, court-admissible audit, dedicated support, SLA |

### 11.2 Pricing strategy notes

- **Solo tier is strategically important** — it's the land-and-expand pipeline for when solo lawyers join firms.
- **Team tier didn't exist in V1** — adding it captures the 2-20 lawyer gap.
- **Enterprise pricing is deliberately opaque** (negotiated) — signals to AmLaw buyers that CiteGuard is serious; speeds procurement.
- **Per-seat pricing still absent.** Continue to avoid the compression trend Claude is causing on seat-based SaaS.

### 11.3 Target revenue mix at end of V2

- Solo: 200 firms × $79 = $16K MRR
- Team: 50 firms × $700 avg = $35K MRR
- Firm: 30 firms × $2,200 avg = $66K MRR
- Enterprise: 5 firms × $6,000 avg = $30K MRR (annual contracts, monthly equivalent)
- **Total MRR: ~$147K → $1.76M ARR trajectory** (exceeds $500K V2 target; provides headroom)

---

## 12. Dependencies & Risks

### 12.1 New dependencies

| Dependency | Purpose | Risk | Mitigation |
|------------|---------|------|-----------|
| Google Workspace Marketplace | Add-on distribution | Low-Med — review process can be slow/opaque | Start submission in week 1 of V2 work |
| Microsoft AppSource | Word/Outlook add-in distribution | Med — MS cert can take 4-8 weeks | Begin cert path early; have alternative direct-install plan |
| WorkOS / Auth0 | Enterprise auth (replacing Clerk) | Low | Standard vendor |
| OPA (Open Policy Agent) | Policy engine | Low — mature open source | Self-hosted; no vendor risk |
| gVisor | Custom evaluator sandboxing | Medium — operational complexity | Hire infra engineer before launching custom evaluators |
| RFC 3161 TSA (FreeTSA / DigiCert) | Court-admissible timestamping | Low | Multiple providers; easy to switch |

### 12.2 Risks

| # | Risk | Severity | Mitigation |
|---|------|---------|------------|
| R7 | Add-on approval delays from Google/Microsoft | Medium | Submit early; have web fallback always available |
| R8 | SOC 2 Type II audit reveals control gaps | Medium-High | Engage auditor at start of V2 (Vanta/Drata ongoing); don't leave to end |
| R9 | Enterprise deal cycles take 9-12 months; we miss AmLaw target | High | Start Enterprise sales motion in month 1 of V2 work, not at launch |
| R10 | Policy engine false positives drive firm frustration | Medium | Mandatory simulation-mode testing before any policy goes live |
| R11 | VPC deployment ops overhead | High | Charge $50K floor; only take on 1-2 VPC deals in V2; build automation before scaling |
| R12 | Native surface integrations cannibalize web dashboard usage before native parity achieved | Low-Med | Ensure feature parity between native + web before heavy native promotion |

---

## 13. V2 Release Criteria (Definition of Done)

### 13.1 Functional
- [ ] F11 Google Docs add-on published and approved
- [ ] F12 Word plugin published and approved
- [ ] F13 Outlook plugin published and approved
- [ ] F14 Policy engine live with 10+ pre-built templates
- [ ] F15 Custom evaluator SDK documented and tested with 1 design partner
- [ ] F16 SAML SSO working end-to-end with Okta and Azure AD
- [ ] F16 SCIM provisioning verified with 2 design partners
- [ ] F17 Single-tenant VPC deployment completed for ≥1 enterprise customer
- [ ] F18 Court-admissible audit package accepted by ≥1 malpractice carrier
- [ ] F19 Malpractice carrier reporting API live with ≥1 carrier integrated
- [ ] F20 Multi-firm user support shipped
- [ ] F21 Analytics dashboard live with benchmarking

### 13.2 Non-functional
- [ ] SOC 2 Type II report issued
- [ ] Penetration test completed; all high/critical findings remediated
- [ ] Bug bounty program launched
- [ ] Local CourtListener mirror serving ≥95% of lookups
- [ ] p95 native-surface latency <4s verified in load test
- [ ] Active-passive multi-region tested via failover drill

### 13.3 Business
- [ ] ≥5 AmLaw 200 firms signed
- [ ] ≥100 total paying firms
- [ ] MRR ≥ $40K
- [ ] ≥1 malpractice carrier public endorsement or premium-discount program
- [ ] Written SLAs live on Enterprise tier
- [ ] Enterprise sales playbook documented + 2 sales reps hired

### 13.4 Operational
- [ ] On-call rotation of ≥3 engineers (not just founder)
- [ ] Runbooks for top 15 operational incidents
- [ ] Customer success process live (dedicated CSM for Enterprise tier)
- [ ] Training materials + certification program for design partners

---

## 14. Milestones (V2 — 6 months)

| Month | Milestone | Exit criteria |
|-------|-----------|---------------|
| M1 | Foundation | SOC 2 Type II auditor engaged; Google/Microsoft marketplace submissions started; WorkOS migration complete; local CourtListener mirror live |
| M2 | Native surfaces alpha | Google Docs add-on in beta with 3 design partners; Word plugin in internal testing |
| M3 | Native surfaces GA + Policy engine | Google Docs + Word plugins public; Outlook in beta; policy engine live with 3 firms using custom rules |
| M4 | Enterprise foundation | SAML SSO GA; SCIM GA; first VPC deployment in progress; custom evaluator SDK documented |
| M5 | Court-admissible + carrier | Court-admissible audit package GA; first malpractice carrier integration live |
| M6 | Launch | All release criteria met; public announcement; enterprise customer case studies published |

---

## 15. Team & Hiring Implications

V2 cannot be executed by a solo founder or 2-3 person team. Minimum team for V2 completion:

| Role | Why needed |
|------|-----------|
| Founder/CEO | Sales to AmLaw, vision, fundraising |
| Head of Engineering | Architecture, platform expansion |
| 2x Backend engineers | API v2, policy engine, mirror sync |
| 1x Frontend engineer | Native surfaces (Google Docs, Word, Outlook) |
| 1x Platform/DevOps engineer | VPC deployments, SOC 2 infra, SSO |
| 1x Designer (contract or FT) | Native surface UX |
| 1x Enterprise Account Executive | AmLaw sales cycle management |
| 1x Customer Success Manager | Enterprise onboarding |
| 1x Legal Ops / Domain Expert (could be FT or advisor) | Policy templates, bar association outreach, court-admissible format |

**Total: 9 people.** Hire in this order, front-load engineering in M1-M3.

Funding implication: this team at a modest $150K/person burn = $1.35M/year burn. With $500K ARR at end of V2, pre-V2 you'd want to close a seed round ($2-4M) to cover 18-24 months.

---

## 16. Open Questions

- [ ] **Should we build the Word plugin first or Google Docs first?** Data says: AmLaw uses Word (Microsoft shop). Mid-market splits 60/40 Google/Microsoft. Decision: build Word first for Enterprise GTM.
- [ ] **Do we self-host the policy engine (OPA) or use a managed policy service?** Recommend self-hosted OPA; adds complexity but keeps customer data in our trust boundary.
- [ ] **Is multi-region active-active worth it in V2?** Currently proposed as active-passive. Decision by M3.
- [ ] **Pricing: do we grandfather V1 firms at V1 pricing or upgrade them?** Recommend grandfathering current customers; apply new tiers to new signups only.
- [ ] **Enterprise VPC: AWS only, or also Azure?** AmLaw split is ~60/40 AWS/Azure. Likely need Azure by V3.
- [ ] **What's our data governance story when firms bring their own custom evaluators that hit third-party APIs?** Legal review needed before F15 GA.
- [ ] **Do we open-source the policy engine templates?** Arguments both ways; defer decision.

---

## 17. Beyond V2 — What V3 Looks Like

V3 is where CiteGuard expands beyond legal. Previewed here for context, not for V2 execution:

- **Vertical 2: Healthcare** — clinical guideline adherence, ICD-10/CPT validation, drug interaction checking, HIPAA audit trails
- **Vertical 3: Accounting/Audit** — GAAP compliance checks, SOX evidence, audit trail for AI-assisted attestation
- **International expansion** — UK (Bar Standards Board rules), EU (DAC7/MiCA compliance for legal advice)
- **Proactive mode** — not just verify after the fact, but autocomplete with verified citations as lawyers draft
- **Acquisition target / platform** — by V3, CiteGuard might be acquired by Thomson Reuters, LexisNexis, or a malpractice carrier; or might itself acquire smaller verticals

---

## 18. Decision Log (living)

| Date | Decision | Rationale |
|------|----------|-----------|
| Day 0 | V2 does NOT add new verticals | Focus; execution capacity; legal TAM is large enough |
| Day 0 | V2 keeps per-document pricing | Resistant to Claude-driven per-seat compression |
| Day 0 | V2 introduces Enterprise tier with negotiated pricing | AmLaw procurement expects this |
| Day 0 | V2 requires migration off Clerk to WorkOS | Clerk ceiling on enterprise SAML |

---

*End of V2 PRD. V2 is the "prove the platform" release. If V1 is "we catch citation hallucinations," V2 is "we are the AI compliance infrastructure for law firms of any size." Keep scope disciplined; resist the urge to add healthcare/accounting in V2.*