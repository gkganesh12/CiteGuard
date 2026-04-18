# CiteGuard: Product Spec & 12-Week Build Plan

**A vertical AI reliability + audit platform for law firms.**
Version 0.1 — product blueprint for a founder building in 2026

---

## TL;DR

**Product:** The verification and audit layer for every AI-generated document a law firm produces. Catches hallucinated citations, fabricated quotes, and mischaracterized holdings before they reach a judge. Produces a tamper-evident audit trail that doubles as bar-compliance evidence.

**Buyer:** Managing partners and General Counsel at 20-200 lawyer firms — especially litigation-heavy practices (personal injury, family law, commercial litigation, insurance defense).

**Pricing:** $1,500/mo flat + $2/document verified. No per-seat fees.

**Moat:** Regulatory complexity + proprietary evaluator rules + workflow embedding + liability framework that Claude/Anthropic will not touch.

**Target:** $600K ARR in year one (25 firms × ~$2k/mo avg).

---

## 1. Why Legal, Specifically

Of the five regulated professions available (legal, healthcare, accounting, insurance claims, HR), legal is the right wedge for a founder without existing domain expertise:

- **The pain is public, named, and famous.** *Mata v. Avianca* (2023) is folklore: a lawyer filed an AI-drafted brief with six fabricated case citations, got sanctioned, and made international news. Since then, state bars in California, New York, Florida, Texas, and 15+ others have issued formal AI-use guidance. Every litigation partner knows this fear personally.
- **The verification is mechanical, not judgmental.** You don't need a JD. The core evaluators answer factual questions: Does this case exist in CourtListener? Is the citation format valid under The Bluebook? Does the cited judge sit in this jurisdiction? Did the cited opinion actually contain this quote? These are API calls and string matching — not legal reasoning.
- **Buyers have personal, unlimited liability.** A partner faces bar sanctions, client malpractice suits, and reputation damage. They'll pay insurance-equivalent prices to prevent a single incident.
- **Free data is available.** CourtListener has ~8M+ U.S. court opinions freely accessible by API. You don't need Westlaw/Lexis to start.
- **The market has clear adjacencies.** Once you own legal, the same architecture extends to healthcare, accounting, insurance, and HR. Legal is Act 1.

---

## 2. The 10 Core Evaluators (MVP)

These are the actual checks your product runs on every AI-generated document. Each returns a severity (Critical / High / Medium / Advisory) and a human-readable explanation.

| # | Evaluator | What it does | Data source |
|---|-----------|--------------|-------------|
| 1 | **Citation Existence** | Every case citation must resolve to a real opinion | CourtListener API (free), optional CaseText |
| 2 | **Bluebook Formatting** | Validates 21st-edition Bluebook format: signals, pincites, parallel cites | Regex + rule engine |
| 3 | **Jurisdiction Match** | Cited precedent must be controlling/persuasive in the filing court | Court hierarchy database |
| 4 | **Judge Verification** | Named judges must have actually sat on the named court during the relevant year | Federal Judicial Center data (public) |
| 5 | **Quote Verification** | Any quoted language from a case must actually appear in that opinion | Full-text search against opinion corpus |
| 6 | **Holding Accuracy** | AI's characterization of a case's holding must match the actual opinion | LLM-as-judge using Claude Opus + opinion summary |
| 7 | **Temporal Validity** | Flags overturned, superseded, or vacated precedent | CourtListener citation graph |
| 8 | **PII / Privilege Scan** | Detects client PII, privileged material, or sealed content leaked into AI outputs | Custom NER + rule patterns |
| 9 | **Opposing Authority** | Flags likely missing adverse controlling precedent (ABA Model Rule 3.3(a)(2) compliance) | Semantic search over opposing counsel's likely cites |
| 10 | **Statutory Currency** | Flags cited statutes/regulations that are repealed, amended, or superseded | LegInfo + public statute databases |

**Build order:** 1 → 2 → 4 → 5 → 3 → 7 → 10 → 6 → 8 → 9 (easiest/highest-signal first)

---

## 3. 12-Week Roadmap

### Weeks 1–3: Foundation & Customer Discovery
- **Week 1:** 10–15 discovery calls with litigators at mid-size firms. Source via LinkedIn + Clay + warm intros. Questions: "Walk me through the last time AI messed up on a document." "Who reviewed? What did you wish you had?" Goal: sign 2–3 design partners (free 6-month pilot, product feedback, case study rights).
- **Week 2:** Company setup (LLC, Stripe, basic contracts including a liability-limiting ToS). Technical scaffolding: Python/FastAPI backend, Postgres (with append-only audit table + hash chaining), ClickHouse for traces, Next.js/Tailwind frontend. Deploy on Fly.io or Railway.
- **Week 3:** Build ingestion. Ship both a ~3-line Python/Node SDK and a REST proxy endpoint (Claude/OpenAI-compatible shape). Capture: prompt, completion, metadata, timestamps, user ID. Store in append-only, hash-chained audit log.

### Weeks 4–7: Core Evaluators
- **Week 4:** Evaluator #1 (Citation Existence) + #2 (Bluebook Formatting). CourtListener integration. Citation parser.
- **Week 5:** #4 (Judge Verification) + #5 (Quote Verification). Build court-judge database from Federal Judicial Center public data. Full-text indexing of opinion corpus (start with federal).
- **Week 6:** #3 (Jurisdiction Match) + #7 (Temporal Validity). Court hierarchy mapping. Citation-graph queries for overruled status.
- **Week 7:** #10 (Statutory Currency) + #6 (Holding Accuracy via LLM-as-judge). Ship all priority evaluators.

### Weeks 8–9: Review Workflow
- **Week 8:** Review-queue UI. Flagged issues sorted by severity. Reviewer actions: Approve, Override-with-reason, Reject. Keyboard shortcuts, fast through-put. Slack alerts for Critical flags.
- **Week 9:** Audit-export packet. One-click PDF: original prompt, AI output, all evaluator results, reviewer name, timestamp, override reasons, cryptographic hash. Format mirrors common bar documentation standards.

### Weeks 10–11: Polish & First Paid Customers
- **Week 10:** Onboarding (SSO with Google/Microsoft, API key provisioning, firm-level settings). Basic analytics dashboard: flagged rate, top failure modes, reviewer throughput.
- **Week 11:** Convert 2 of 3 design partners to paid ($1,500/mo + per-doc fees). Ask each for 3 peer-firm intros. Close 2 more paying customers.

### Week 12: Public Launch
- LinkedIn posts from design partners.
- Submit to Legaltech News, ABA Journal, Law360, Above the Law.
- Apply to speak at ILTACon 2026 / Clio Con / Legalweek.
- Begin outbound to a target list of 100 mid-market litigation firms.
- Target outcome: 5 paying customers, $10K MRR committed.

---

## 4. Technical Architecture

### Components

```
Law Firm App (Harvey, Claude.ai, internal RAG, etc.)
           │
           ▼
┌──────────────────────────────────┐
│  CiteGuard SDK or REST Proxy     │
│  Captures all LLM inputs/outputs │
└──────────────────┬───────────────┘
                   ▼
┌──────────────────────────────────┐
│  Ingestion API (FastAPI)         │
│  - Auth + rate limit             │
│  - Enqueue to evaluator pipeline │
│  - Write to append-only log      │
└──────────────────┬───────────────┘
                   │
     ┌─────────────┼──────────────┐
     ▼             ▼              ▼
┌─────────┐  ┌──────────┐   ┌─────────────┐
│ Trace   │  │ Audit    │   │ Evaluator   │
│ Store   │  │ Log      │   │ Workers     │
│ (CH)    │  │(PG chain)│   │ (parallel)  │
└─────────┘  └──────────┘   └──────┬──────┘
                                   │
                                   ▼
                           ┌──────────────┐
                           │ External APIs│
                           │ CourtListener│
                           │ FJC, LegInfo │
                           │ (CaseText)   │
                           └──────┬───────┘
                                  │
                                  ▼
                           ┌──────────────┐
                           │ Review Queue │
                           │ (Next.js UI) │
                           └──────┬───────┘
                                  │
                                  ▼
                           ┌──────────────┐
                           │ Audit Export │
                           │ (signed PDF) │
                           └──────────────┘
```

### Stack

- **Backend:** Python 3.12, FastAPI, async workers (Arq or Celery)
- **DB:** Postgres 16 (primary + append-only audit table with SHA-256 hash chaining)
- **Traces:** ClickHouse (cost-efficient for high-cardinality trace data)
- **Frontend:** Next.js 14, TypeScript, Tailwind, shadcn/ui
- **Auth:** Clerk or Auth.js + SSO (SAML for enterprise tier later)
- **Hosting:** Fly.io or Railway for app; ClickHouse Cloud; Cloudflare in front
- **Observability:** Use one of the horizontal tools (e.g., Langfuse self-hosted, or Helicone) for your own LLM calls — don't reinvent that wheel
- **Standards:** OpenTelemetry `gen_ai.*` semantic conventions so you're portable

### Key architectural decisions

1. **Proxy + SDK, both.** Some firms want drop-in proxy (zero code change). Others need SDK for deeper capture. Support both.
2. **Append-only audit log with hash chaining.** Each audit row stores a hash of the prior row's hash + content. Any tampering is detectable. This is the core compliance artifact.
3. **LLM-as-judge is fine for some evaluators, not others.** #6 (Holding Accuracy) uses Claude as judge. #1, #4, #5, #10 must be deterministic (no LLM in the loop — the whole point is to catch LLM errors).
4. **Evaluators run in parallel, not sequentially.** Use async fan-out. Total latency target: <3s for a typical brief.
5. **Start federal-only.** Expand to state law in month 4–6. Don't bite off the whole corpus day one.

---

## 5. Pricing

### Launch pricing
- **Base:** $1,500/month per firm (flat)
- **Usage:** $2 per document verified
- **Included:** Unlimited seats, all 10 evaluators, audit exports, SDK + proxy access
- **Annual pre-pay:** 20% discount
- **14-day free trial** on the base fee; usage metered from day one

### Why this pricing works

1. **Much cheaper than the alternative.** A single bar sanction / malpractice suit easily exceeds $100K in legal fees, insurance premium increases, and reputation damage.
2. **No per-seat friction.** Per-seat pricing is the exact thing getting compressed by AI. Per-document aligns to actual risk reduction.
3. **Flat base covers COGS.** API and infra costs have a floor; the flat base ensures positive margin even on slow months.
4. **Per-doc scales with value delivered.** High-volume firms pay more because they're reducing more risk. Low-volume firms aren't forced into a tier that doesn't fit.

### Target year-one economics
- 25 paying firms × $2,000 avg monthly = **$600K ARR**
- Gross margin: ~75% (API costs to CourtListener are free; LLM-as-judge costs real; infra is manageable)
- CAC target: <$3K via founder-led sales to warm intros
- Payback: <3 months

---

## 6. Moat Analysis

You will have **at least 3 of the 4 defensible moats**:

### Regulatory moat (primary)
- State bar rules are jurisdictional, granular, and constantly evolving.
- ABA Model Rules + 50 state variations + local court rules.
- Claude can *explain* the rules. It cannot *certify* a firm's compliance, nor carry liability. Your audit trail IS the compliance artifact.

### Data moat (compounding)
- Every flagged hallucination across every customer improves your evaluator bank.
- After 12 months in production, you'll have proprietary data on the top 50 failure patterns of legal AI — richer than any external source.
- New customers benefit immediately. Network effect on evaluator quality.

### Workflow moat (sticky)
- Review queues, sign-off flows, and audit exports embed in the firm's document-production process.
- Ripping you out = re-engineering how the firm ships briefs.
- Combined with annual contracts, this produces >95% logo retention once established.

### Network moat (future)
- Once 100+ firms use you, you become referenced in RFPs, cyber-insurance questionnaires, and malpractice carrier underwriting.
- At that point, not using CiteGuard becomes an insurance question. That's deeply defensible.

### Why Claude/Anthropic will not replace you
To replace you, Anthropic would need to: license + maintain court data feeds, build evaluators for every regulated profession, take on legal liability for errors, build firm-specific workflow UI, and get adopted by bar associations. None of that is Anthropic's strategy. They want to be a foundation-model + orchestration provider. You'd need to be wildly successful before they'd bother — and by then you'd be acquired or entrenched.

---

## 7. Go-to-Market: First 90 Days

### Days 1–14: Discovery + Brand-Building
- 20 discovery calls with litigation-focused lawyers and law firm IT/operations leaders.
- Write 3 LinkedIn posts about AI hallucinations in legal contexts. Make the posts substantive, not promotional — share data, cite specific cases (including *Mata*, *Park v. Kim*, etc.).
- Grow LinkedIn network to 500+ in your target ICP (use Clay + Apollo for sourcing).
- Identify 3 design-partner candidates.

### Days 15–45: MVP + Design Partners
- Build MVP (evaluators 1–5 minimum).
- Onboard 2–3 design partners on free pilots.
- Weekly feedback calls. Fix the top complaint every week.
- Document everything: their before/after stories become case studies.

### Days 46–75: Remaining Evaluators + First Revenue
- Ship evaluators 6–10.
- Convert design partners to $1,500/mo pilots (they should *want* to pay — it means you built something valuable).
- Get 3-5 warm intros from each design partner.
- Close the first non-design-partner paying customers.

### Days 76–90: Public Launch
- Close to 5 paying customers.
- Launch publicly: LinkedIn, Legaltech News, Above the Law, HN if appropriate.
- Apply to 2–3 legal tech conferences (even as a sponsor/attendee, not speaker).
- Hire: part-time legal advisor (~10 hours/month retainer), perhaps a junior engineer.

### Distribution channels that actually work for legal
1. **Warm intros from design partners.** By far the highest conversion.
2. **LinkedIn content** aimed at managing partners / GCs / legal ops.
3. **Legaltech publications.** Above the Law, Law360, Legaltech News, ABA Journal.
4. **Conferences.** ILTACon (late summer), Clio Con (fall), Legalweek (winter). Start by attending; speak year 2.
5. **Malpractice carriers.** Approach risk-management departments at ALPS, Aon, Attorney's Liability Protection — they have every lawyer's ear on risk.
6. **Bar associations.** Get mentioned in state bar CLE materials once you have traction.

### Distribution channels that do NOT work for legal
- Paid ads on Google/Meta (CAC catastrophic)
- Outbound cold email at scale (bar ethics rules on "solicitation" are tricky; it also feels slimy)
- Product Hunt / Hacker News as primary channels (wrong audience — engineers aren't your buyer)

---

## 8. Top 5 Risks & Mitigations

### Risk 1: Harvey or Casetext bundles this as a feature
**Likelihood:** High
**Mitigation:** Stay tool-agnostic. Firms use multiple AI tools (Harvey + Claude + GPT + internal RAG), and you sit across all of them. Harvey's incentive is NOT to highlight errors in its own tool — that's a trust conflict you can exploit. Position as the "independent third party" in your marketing.

### Risk 2: Westlaw/Lexis charge punitive API fees when you need them
**Likelihood:** Medium
**Mitigation:** Start with CourtListener (free, ~8M opinions). Add paid sources only when customer volume justifies it. Negotiate B2B pricing at scale — paint yourself as a source of downstream Westlaw usage (your customers already subscribe).

### Risk 3: A missed hallucination causes a client sanction → they sue you
**Likelihood:** Low but catastrophic
**Mitigation:**
- Clear ToS: you're a "verification assistant," not a substitute for lawyer judgment.
- Every flag explicitly says "Human review required."
- E&O insurance from day 1 ($5K–$15K/yr).
- Keep humans always in the loop on the final output.
- Never auto-approve; always require a human sign-off before audit-trail closure.

### Risk 4: Market too small for venture scale
**Likelihood:** Medium
**Mitigation:** Legal is Act 1. Your architecture (domain-specific evaluators + tamper-evident audit + review workflow) extends identically to healthcare, accounting, insurance, and HR. You can reach $3–10M ARR on legal alone (great bootstrap outcome), then expand vertically.

### Risk 5: Regulatory pressure changes or slips
**Likelihood:** Medium
**Mitigation:** Value exists without regulatory pressure — firms want to avoid sanctions regardless of what the EU AI Act does. Don't anchor marketing entirely on one regulation.

---

## 9. Questions to Answer Before Writing Code

1. **Who are your first 3 design-partner candidates?** (Names, firms, how you know them.) If the answer is "I don't know any lawyers" — start with 50 LinkedIn outreach messages before writing a single line of code.
2. **Have you validated that firms will pay $1,500/mo?** Ask 10 managing partners directly: "If a tool prevented AI citation errors and produced an audit-ready record, would you pay $1,500/month?" Get 6+ yeses before building.
3. **What's your personal runway?** This path is 12+ months to meaningful revenue. Plan for it.
4. **Who is the technical co-founder or first engineer?** This is buildable solo if you're technical, but a design partner managing a firm while you code nights-and-weekends is painful. Consider finding a co-founder.

---

## 10. What to Do This Week

- [ ] Post on LinkedIn: "I'm researching AI hallucinations in legal practice. If you're a litigator or legal ops leader, I'd love 20 minutes of your time." See who replies.
- [ ] Read the full opinions in *Mata v. Avianca* (2023), *Park v. Kim* (2024), and the 2024 ABA Formal Opinion 512. Internalize the vocabulary.
- [ ] Register for a free CourtListener API key at courtlistener.com/api.
- [ ] Set up GitHub repo, basic Python project, deploy a "hello world" FastAPI to Fly.io. Confirm your stack works end-to-end.
- [ ] Write the first LinkedIn post on AI legal hallucinations (share a concrete story, not a pitch).

---

## Appendix A: Competitive Landscape (Legal-Specific)

| Tool | Focus | Overlap with CiteGuard |
|------|-------|------------------------|
| Harvey | Full AI workstation for lawyers | Competes partially; Harvey's incentive is NOT to highlight its own errors — you're the neutral verifier |
| CaseText / CoCounsel (Thomson Reuters) | AI legal research on Westlaw | Overlaps in research; doesn't do verification of arbitrary AI outputs across tools |
| Paxton AI | Legal drafting AI | Same issue as Harvey — they produce outputs, they don't verify them |
| Spellbook | Contract drafting AI | Different modality (contracts, not litigation) |
| Disco, Relativity (eDiscovery) | Discovery review | Adjacent market; not direct competitor |
| Fiddler, Arize, Braintrust | Horizontal LLM observability | Compete only until firms realize they need legal-specific evaluators |

**Your positioning:** Tool-agnostic, profession-specific, compliance-first. "We work with whatever AI tool your lawyers already use. We make sure nothing embarrassing reaches a judge."

---

## Appendix B: Rough Financial Model (Year 1)

| Month | Paying Firms | MRR | ARR (annualized) |
|-------|-------------|-----|------------------|
| 3 | 2 | $3K | $36K |
| 6 | 5 | $10K | $120K |
| 9 | 12 | $25K | $300K |
| 12 | 25 | $50K | $600K |

**Costs (monthly, year 1 exit):**
- Infra: ~$2K
- LLM API (Claude for LLM-as-judge): ~$3K
- Tools (Stripe, Clerk, monitoring): ~$500
- E&O insurance: ~$1K
- Founder salary (minimal): $5K
- **Total: ~$11.5K/mo → $138K/year**

Net at month 12 (assuming $50K MRR): ~$38.5K/mo positive operating income. Default-alive territory.

---

*This document is a starting blueprint, not a contract with reality. Revise weekly as you learn.*