# Project Manager - Code & Project Review Rules

## Role Overview
As a Senior Project Manager, you are responsible for project planning, sprint management, quality assurance, risk mitigation, stakeholder communication, and ensuring the development team delivers high-quality features on time for the CiteGuard platform — an AI verification and audit layer for U.S. law firms.

> **⚠️ Domain criticality notice:** CiteGuard processes privileged legal material and produces compliance artifacts. Project management here is not just about shipping features — it is about ensuring the team never releases something that could cause malpractice exposure for a customer. Quality, audit integrity, and tenant isolation outrank velocity every time.

**Reference documents:**
- V1 PRD (`citeguard_v1_prd.md`)
- Architect Rules (`citeguard_architect_rules.md`)
- Backend Guidelines (`citeguard_backend_guidelines.md`)
- Frontend Guidelines (`citeguard_frontend_guidelines.md`)
- QA Rules (`citeguard_qa_rules.md`)

---

## 1. PROJECT PLANNING & ESTIMATION

### 1.1 Feature Breakdown
- **RULE**: Break down features into manageable, estimable tasks
- **CHECK**: Each feature has clear acceptance criteria (aligned with V1 PRD)
- **CHECK**: Dependencies identified and documented (external APIs like CourtListener, FJC; shared evaluator infrastructure; audit log)
- **CHECK**: Tasks sized appropriately (1-5 days max)
- **CHECK**: Complex features broken into subtasks (e.g., each evaluator is its own task)
- **CHECK**: Technical spikes identified for unknowns (e.g., CourtListener rate-limit behavior, PDF hash chain format)
- **REJECT**: Vague feature descriptions without acceptance criteria
- **REJECT**: Tasks estimated at >5 days (too large, break down)
- **REJECT**: Missing dependencies causing mid-sprint blockers

### 1.2 Estimation Accuracy
- **RULE**: Realistic, data-driven estimates
- **CHECK**: Estimates include development, testing (including evaluator corpus regression), and review time
- **CHECK**: Buffer added for unknowns (20% contingency; more for evaluator work where CourtListener behavior may surprise)
- **CHECK**: Historical data used for similar tasks once available
- **CHECK**: Team members involved in estimation
- **CHECK**: Re-estimate if scope changes
- **TARGET**: Estimation accuracy within ±20%
- **REJECT**: Estimates without testing time
- **REJECT**: Overly optimistic estimates
- **REJECT**: Not adjusting for team velocity

### 1.3 Sprint Planning
- **RULE**: Well-structured, achievable sprints aligned with the V1 12-week roadmap
- **CHECK**: Sprint goals clearly defined (map to V1 PRD milestones)
- **CHECK**: Sprint capacity matches team velocity
- **CHECK**: Sprint backlog prioritized
- **CHECK**: No overcommitment (plan for 80% capacity)
- **CHECK**: Emergency buffer for critical bugs
- **CHECK**: All team members have clear assignments
- **REJECT**: Sprints without clear goals
- **REJECT**: Overloading sprint (>100% capacity)
- **REJECT**: Unclear priorities

### 1.4 Roadmap Management
- **RULE**: Clear, communicated product roadmap
- **CHECK**: V1 roadmap documented (12-week plan in PRD); V1.1/V1.2 previews maintained
- **CHECK**: Monthly roadmap updates
- **CHECK**: Design partners (law firms) informed of timeline
- **CHECK**: Feature prioritization documented
- **CHECK**: V1 scope vs post-V1 clearly marked (explicit non-goals in PRD)
- **REJECT**: No long-term vision
- **REJECT**: Scope creep into V1 (Jurisdiction Match, Statutory Currency, etc. are V1.1)
- **REJECT**: Unclear priorities

---

## 2. TASK & FEATURE MANAGEMENT

### 2.1 Task Definition
- **RULE**: Clear, actionable tasks
- **CHECK**: Task title is descriptive
- **CHECK**: Acceptance criteria defined (map to V1 PRD requirement IDs, e.g., REQ-F2.1)
- **CHECK**: Technical requirements documented
- **CHECK**: UI/UX designs attached for frontend tasks
- **CHECK**: API contracts defined for backend tasks
- **CHECK**: Test cases outlined (including evaluator corpus tests where relevant)
- **FORMAT**: Use `CG-XXX` for feature/bug tracking
- **REJECT**: Vague tasks ("Fix bugs", "Improve performance")
- **REJECT**: Tasks without acceptance criteria
- **REJECT**: Missing designs for UI tasks

### 2.2 Task Prioritization
- **RULE**: Clear prioritization system
- **CHECK**: Use P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
- **CHECK**: Priorities reviewed weekly
- **CHECK**: Critical bugs prioritized over features
- **CHECK**: Business value considered
- **CHECK**: Technical debt balanced with features
- **PRIORITY GUIDE (CiteGuard-specific):**
  - **P0**: Privileged data leak; audit hash chain break; tenant isolation bug; production down; evaluator false-negative on seeded hallucination; security vulnerability
  - **P1**: Major feature broken; high-impact bug; evaluator accuracy regression; blocker for design partner
  - **P2**: Enhancement; medium bug; nice-to-have
  - **P3**: Minor improvement; low-priority bug; cosmetic
- **REJECT**: Everything marked P0
- **REJECT**: No prioritization system
- **REJECT**: Ignoring technical debt

### 2.3 Task Tracking
- **RULE**: Accurate, up-to-date task status
- **CHECK**: Tasks have clear status (To Do, In Progress, In Review, Done)
- **CHECK**: Status updated daily
- **CHECK**: Blockers clearly marked and escalated
- **CHECK**: Assignees clearly defined
- **CHECK**: Progress tracked daily
- **REJECT**: Stale task status
- **REJECT**: Tasks "in progress" for weeks
- **REJECT**: Blockers not escalated

### 2.4 Feature Documentation
- **RULE**: Comprehensive feature documentation
- **CHECK**: Feature template used
- **CHECK**: Business requirements documented
- **CHECK**: Technical approach outlined (link to relevant ADR)
- **CHECK**: API contracts defined (in generated OpenAPI)
- **CHECK**: UI mockups attached (Figma links)
- **CHECK**: Test scenarios listed (including evaluator corpus impact where relevant)
- **CHECK**: Release notes prepared
- **REJECT**: Features without documentation
- **REJECT**: Missing API documentation
- **REJECT**: No test plan

---

## 3. QUALITY ASSURANCE OVERSIGHT

### 3.1 Code Review Standards
- **RULE**: Enforce code review process
- **CHECK**: All PRs reviewed before merge
- **CHECK**: At least one approval required
- **CHECK**: Architect review for architectural changes (see `citeguard_architect_rules.md`)
- **CHECK**: No self-merges
- **CHECK**: Review turnaround < 24 hours
- **CHECK**: Reviews follow role-specific guidelines (`citeguard_architect_rules.md`, `citeguard_backend_guidelines.md`, `citeguard_frontend_guidelines.md`)
- **REJECT**: Merging without review
- **REJECT**: PRs open for > 3 days
- **REJECT**: Rubber-stamp approvals

### 3.2 Testing Requirements
- **RULE**: Comprehensive testing before release
- **CHECK**: Unit tests for all new code (80%+ coverage backend; 70%+ frontend)
- **CHECK**: Integration tests for APIs
- **CHECK**: Evaluator accuracy tests against the fixed 100-document corpus (50 seeded hallucinations + 50 clean)
- **CHECK**: Tenant isolation tests (critical: Firm A must never see Firm B data)
- **CHECK**: Audit log hash chain verification tests
- **CHECK**: Manual QA for UI changes
- **CHECK**: Edge cases tested
- **CHECK**: Mobile responsiveness tested (V1 = read-only below 1024px)
- **CHECK**: Cross-browser testing (Chrome, Safari, Firefox, Edge)
- **CHECK**: Performance testing (p95 evaluation latency <3s)
- **REJECT**: No tests written
- **REJECT**: Skipping QA for "small changes"
- **REJECT**: Evaluator changes without corpus regression results

### 3.3 Bug Management
- **RULE**: Systematic bug tracking and resolution
- **CHECK**: All bugs logged with reproduction steps (and firm_id / document_id context where applicable)
- **CHECK**: Bugs prioritized appropriately
- **CHECK**: Critical bugs (privileged data leak, audit chain break, tenant isolation) fixed within 4 hours
- **CHECK**: P0 bugs fixed within 24 hours
- **CHECK**: High-priority bugs fixed within sprint
- **CHECK**: Root cause analysis for all P0 bugs
- **CHECK**: Regression tests added for every fixed bug
- **TARGET**: P0 bugs resolved < 24h; P1 bugs < 3 days
- **REJECT**: Bugs not logged
- **REJECT**: No reproduction steps
- **REJECT**: Critical bugs delayed

### 3.4 Definition of Done
- **RULE**: Clear completion criteria (CiteGuard-adapted)
- **CHECK**: Code written and reviewed
- **CHECK**: Tests written and passing (including any applicable corpus tests)
- **CHECK**: Documentation updated (OpenAPI, changelog, ADR if applicable)
- **CHECK**: QA tested and approved
- **CHECK**: Tenant isolation verified for any multi-tenant code
- **CHECK**: Audit log entries verified where applicable
- **CHECK**: No document content in logs/errors/analytics (privilege check)
- **CHECK**: Deployed to staging
- **CHECK**: Product owner approved
- **CHECK**: Release notes prepared
- **REJECT**: Marking done without all criteria met
- **REJECT**: Skipping documentation
- **REJECT**: No QA sign-off

---

## 4. RISK MANAGEMENT

### 4.1 Risk Identification
- **RULE**: Proactive risk identification
- **CHECK**: Technical risks identified in planning (external API dependencies, evaluator accuracy drift, hash chain design pitfalls)
- **CHECK**: Resource risks tracked (small team, single founder)
- **CHECK**: Dependency risks monitored (CourtListener is the #1 dependency)
- **CHECK**: Timeline risks assessed
- **CHECK**: Quality risks evaluated (evaluator false-negatives are existential)
- **CHECK**: Risk register maintained and reviewed weekly
- **REJECT**: No risk assessment
- **REJECT**: Ignoring warning signs
- **REJECT**: Reactive instead of proactive

### 4.2 Risk Mitigation (CiteGuard-specific risks)
- **RULE**: Clear mitigation strategies
- **CHECK**: Each risk has mitigation plan
- **CHECK**: High-impact risks addressed first
- **CHECK**: Contingency plans for critical paths
- **CHECK**: Regular risk review (weekly)
- **CHECK**: Escalate risks early
- **TOP RISKS TO ACTIVELY MANAGE:**
  1. **CourtListener API outage / rate limit change** → local opinion mirror, paid fallback research (Westlaw/Lexis)
  2. **Evaluator false-negative on a hallucinated cite in production** → corpus regression before every release; public accuracy reporting
  3. **Hash chain break / audit integrity failure** → daily verification job with alerting; disaster recovery procedure
  4. **Tenant isolation violation** → CI lint + dedicated tenant-isolation test suite on every PR
  5. **Privileged data leak** (document content in logs, errors, analytics, Sentry) → Sentry scrubbing + pre-commit hooks + mandatory code review checks
  6. **Harvey/Casetext bundles verification as a feature** → lean into tool-agnostic, multi-provider coverage; focus on audit angle
  7. **Design partner churn** → weekly check-ins during pilot; fast issue response
  8. **Evaluator drift as CourtListener data shifts** → monthly accuracy re-baseline
- **REJECT**: No mitigation plans
- **REJECT**: Waiting until issues occur
- **REJECT**: Not escalating risks

### 4.3 Dependency Management
- **RULE**: Track and manage dependencies
- **CHECK**: External dependencies documented (CourtListener, FJC, Clerk, Stripe, Anthropic, OpenAI, Sentry, Vercel, Fly.io, AWS RDS, ClickHouse Cloud)
- **CHECK**: SLAs for paid dependencies (Clerk, Stripe) known
- **CHECK**: Dependency updates planned (monthly)
- **CHECK**: Security vulnerabilities tracked (Dependabot, pip-audit, pnpm audit)
- **CHECK**: Fallback plans for critical dependencies
- **REJECT**: Unknown dependencies
- **REJECT**: Outdated dependencies with known vulnerabilities
- **REJECT**: No fallback for critical services

### 4.4 Scope Creep Prevention
- **RULE**: Protect sprint and V1 scope
- **CHECK**: Change requests evaluated formally
- **CHECK**: Impact assessment for scope changes
- **CHECK**: Stakeholder approval for scope changes
- **CHECK**: Timeline adjusted if scope increases
- **CHECK**: Say "no" to non-critical additions mid-sprint
- **CHECK**: V1 non-goals (in PRD) are hard boundaries — defer new evaluators, state law, SSO, etc. to V1.1+
- **REJECT**: Accepting all change requests
- **REJECT**: Adding features without timeline adjustment
- **REJECT**: Letting V1 scope drift into V1.1 territory

---

## 5. COMMUNICATION & STAKEHOLDER MANAGEMENT

### 5.1 Daily Standups
- **RULE**: Effective daily synchronization
- **CHECK**: Daily standup at consistent time
- **CHECK**: Max 15 minutes
- **CHECK**: Each member shares: done, doing, blockers
- **CHECK**: Blockers addressed immediately after
- **CHECK**: Parking lot for detailed discussions
- **REJECT**: Standups > 20 minutes
- **REJECT**: Problem-solving during standup
- **REJECT**: Not addressing blockers

### 5.2 Sprint Reviews
- **RULE**: Showcase completed work
- **CHECK**: Demo all completed features (prefer live demos on staging over slides)
- **CHECK**: Stakeholders invited (including design-partner point of contact for V1)
- **CHECK**: Feedback collected and documented
- **CHECK**: Metrics presented (velocity, completion rate, evaluator accuracy, audit chain verifications passing)
- **CHECK**: What went well / what didn't discussion
- **REJECT**: No demos
- **REJECT**: Only showing slides, not working software
- **REJECT**: Ignoring feedback

### 5.3 Stakeholder Updates
- **RULE**: Regular, transparent communication
- **CHECK**: Weekly progress updates sent
- **CHECK**: Milestone achievements communicated
- **CHECK**: Blockers and risks escalated
- **CHECK**: Timeline changes communicated promptly
- **CHECK**: Use clear, non-technical language for law-firm stakeholders
- **FORMAT**: Executive summary + detailed status (see template in §17)
- **REJECT**: Surprises at the last minute
- **REJECT**: No communication during critical issues
- **REJECT**: Technical jargon in stakeholder updates

### 5.4 Design Partner Communication (CiteGuard-specific)
- **RULE**: Treat design partners as product co-authors
- **CHECK**: Weekly check-in calls with each design partner during pilot
- **CHECK**: Direct Slack Connect channel for fast issue reporting
- **CHECK**: Share release notes before each deploy that affects them
- **CHECK**: Capture every piece of feedback in a feedback backlog
- **CHECK**: Be transparent about timelines and failures
- **REJECT**: Going silent on design partners
- **REJECT**: Treating them as customers rather than partners
- **REJECT**: Surfacing only good news

### 5.5 Documentation Standards
- **RULE**: Maintain comprehensive documentation
- **CHECK**: ADRs for architectural decisions (in `docs/adr/`)
- **CHECK**: Feature specifications versioned with the PRD
- **CHECK**: Release notes for each release (internal + customer-facing)
- **CHECK**: API documentation up-to-date (auto-generated from FastAPI OpenAPI)
- **CHECK**: Meeting notes documented
- **CHECK**: Decision log maintained
- **REJECT**: Undocumented decisions
- **REJECT**: Outdated documentation
- **REJECT**: No meeting notes

---

## 6. SPRINT EXECUTION & MONITORING

### 6.1 Progress Tracking
- **RULE**: Continuous monitoring of sprint progress
- **CHECK**: Daily progress review
- **CHECK**: Burndown chart updated daily
- **CHECK**: Velocity tracked per sprint
- **CHECK**: Early warning for at-risk tasks
- **CHECK**: Blockers resolved within 24 hours
- **TARGET**: Sprint completion rate > 85%
- **REJECT**: Waiting until sprint end to check progress
- **REJECT**: Ignoring burndown trends
- **REJECT**: Not addressing blockers quickly

### 6.2 Sprint Metrics
- **RULE**: Data-driven sprint management
- **CHECK**: Track planned vs completed story points
- **CHECK**: Track velocity trends
- **CHECK**: Track bug discovery rate
- **CHECK**: Track code review turnaround time
- **CHECK**: Track deployment frequency
- **CHECK**: Track evaluator accuracy on the corpus (per evaluator, per version)
- **CHECK**: Track p95 evaluation latency
- **CHECK**: Track audit chain verification pass rate (should always be 100%)
- **CHECK**: Track team happiness
- **REJECT**: No metrics collected
- **REJECT**: Ignoring metric trends
- **REJECT**: Metrics without action

### 6.3 Mid-Sprint Adjustments
- **RULE**: Adapt when needed
- **CHECK**: Re-prioritize if P0 bug discovered (privileged data leak, audit break, tenant isolation)
- **CHECK**: Remove low-priority tasks if overcommitted
- **CHECK**: Add resources only if feasible and needed
- **CHECK**: Communicate adjustments to stakeholders
- **REJECT**: Refusing to adjust scope
- **REJECT**: Adding more work to a struggling sprint
- **REJECT**: Not communicating changes

### 6.4 Sprint Retrospectives
- **RULE**: Continuous improvement culture
- **CHECK**: Retrospective at end of every sprint
- **CHECK**: Safe environment for feedback
- **CHECK**: What went well / what didn't / action items
- **CHECK**: Action items assigned and tracked
- **CHECK**: Previous action items reviewed
- **CHECK**: Team participation encouraged
- **REJECT**: Skipping retrospectives
- **REJECT**: Blame-focused discussions
- **REJECT**: Action items not tracked

---

## 7. RELEASE MANAGEMENT

### 7.1 Release Planning
- **RULE**: Well-planned, low-risk releases
- **CHECK**: Release schedule communicated
- **CHECK**: Release notes prepared (customer-facing, privilege-safe)
- **CHECK**: Staging environment tested with real-shape data
- **CHECK**: Rollback plan documented
- **CHECK**: Database migrations tested
- **CHECK**: Design partners notified in advance for changes affecting them
- **CHECK**: Off-hours releases for major changes
- **REJECT**: Surprise releases
- **REJECT**: No rollback plan
- **REJECT**: Releasing on Friday afternoons

### 7.2 Release Checklist (CiteGuard-adapted)
- **RULE**: Comprehensive release process
- **CHECK**: All features tested on staging
- **CHECK**: Evaluator corpus regression passed (for any evaluator changes — no accuracy regressions)
- **CHECK**: Tenant isolation test suite passed
- **CHECK**: Audit log hash chain verification passed
- **CHECK**: Performance tested (p95 latency within budget)
- **CHECK**: Security scan passed
- **CHECK**: Database backup taken
- **CHECK**: Alembic migration tested with rollback
- **CHECK**: Monitoring and alerts configured
- **CHECK**: Sentry scrubbing verified (no document content)
- **CHECK**: Support channel (design-partner Slack) briefed
- **REJECT**: Skipping checklist items
- **REJECT**: No backup before release
- **REJECT**: Deploying untested code
- **REJECT**: Deploying evaluator changes without a fresh corpus run

### 7.3 Release Communication
- **RULE**: Clear release communication
- **CHECK**: Release notes published
- **CHECK**: Design partners notified of relevant changes
- **CHECK**: Training materials updated if UX changes
- **CHECK**: Support FAQ updated
- **CHECK**: Stakeholders informed of deployment time
- **REJECT**: Releasing without user notification
- **REJECT**: Incomplete release notes
- **REJECT**: Support channel unaware of changes

### 7.4 Post-Release Monitoring
- **RULE**: Monitor releases actively
- **CHECK**: Monitor error rates for 2 hours post-release
- **CHECK**: Monitor p95 evaluation latency
- **CHECK**: Monitor audit chain verification job output
- **CHECK**: Monitor design-partner Slack for real-time issue reports
- **CHECK**: Quick response team available
- **CHECK**: Rollback if critical issues found
- **REJECT**: Deploy and leave
- **REJECT**: No error monitoring
- **REJECT**: Slow response to production issues

---

## 8. TEAM MANAGEMENT & PRODUCTIVITY

### 8.1 Team Capacity Planning
- **RULE**: Realistic capacity management
- **CHECK**: Account for holidays and PTO
- **CHECK**: Account for meetings and overhead (20%)
- **CHECK**: Account for on-call rotation
- **CHECK**: Don't plan for 100% capacity (aim for 80%)
- **CHECK**: Balance work distribution across team
- **REJECT**: Overloading team members
- **REJECT**: Planning for 100% capacity
- **REJECT**: Ignoring PTO in planning

### 8.2 Blocker Resolution
- **RULE**: Rapid blocker removal
- **CHECK**: Blockers identified in standups
- **CHECK**: Blockers addressed within 4 hours
- **CHECK**: Escalate if can't resolve quickly
- **CHECK**: Document blocker and resolution
- **TARGET**: Blocker resolution < 4 hours
- **REJECT**: Blockers lasting multiple days
- **REJECT**: Not escalating blockers
- **REJECT**: Team members stuck without help

### 8.3 Meeting Efficiency
- **RULE**: Respect team time
- **CHECK**: All meetings have agenda
- **CHECK**: Start and end on time
- **CHECK**: Required attendees only
- **CHECK**: Action items documented
- **CHECK**: Follow up on action items
- **CHECK**: Cancel unnecessary meetings
- **TARGET**: Meeting time < 25% of work week
- **REJECT**: Meetings without agenda
- **REJECT**: Meetings running over consistently
- **REJECT**: Too many meetings

### 8.4 Team Morale & Health
- **RULE**: Maintain healthy team dynamics
- **CHECK**: Regular 1-on-1s
- **CHECK**: Monitor workload and burnout signs
- **CHECK**: Celebrate wins and milestones
- **CHECK**: Encourage work-life balance
- **CHECK**: Address conflicts early
- **CHECK**: Provide growth opportunities
- **REJECT**: Ignoring burnout signs
- **REJECT**: Constant crunch time
- **REJECT**: No recognition of achievements

---

## 9. SPECIFIC CITEGUARD PROJECT RULES

### 9.1 Evaluator System
- **RULE**: Evaluators are the product — treat changes with extreme care
- **CHECK**: Every evaluator change produces a corpus accuracy report in the PR
- **CHECK**: No accuracy regressions merged without explicit product sign-off
- **CHECK**: Version bumped on every material behavior change
- **CHECK**: Evaluator tests cover the 100-doc corpus (50 seeded hallucinations + 50 clean)
- **CHECK**: False-positive rate and false-negative rate both tracked
- **CHECK**: Evaluator performance (latency) tracked per version
- **REJECT**: Evaluator changes without corpus regression
- **REJECT**: Accuracy regressions merged silently
- **REJECT**: Version not bumped on logic change

### 9.2 Audit Log Integrity (CRITICAL)
- **RULE**: The audit log is our product moat — it cannot break
- **CHECK**: Daily hash-chain verification job monitored; alerts on divergence trigger P0 response
- **CHECK**: Every change to `AuditLogService` or the audit schema gets an architect + PM review
- **CHECK**: Migration touching `audit_log` requires explicit approval and a verified non-destructive path
- **CHECK**: Every new significant action must be mapped to an audit event before shipping
- **CHECK**: Disaster recovery procedure documented and tested quarterly
- **REJECT**: Any change that allows UPDATE or DELETE on `audit_log`
- **REJECT**: Writes to `audit_log` outside `AuditLogService`
- **REJECT**: Shipping a new state-changing action without a matching audit event

### 9.3 Tenant Isolation
- **RULE**: Multi-tenant bugs are existential
- **CHECK**: Every repository method takes `firm_id` as a required parameter
- **CHECK**: CI lint enforces `firm_id` filters on tenant-scoped queries
- **CHECK**: Dedicated tenant-isolation test suite runs on every PR
- **CHECK**: Any cross-firm query requires explicit architect approval and an audit trail
- **CHECK**: Admin/analytics queries that do aggregate across firms live in a separate service with documented approval
- **REJECT**: Queries missing `firm_id` filter
- **REJECT**: Accepting `firm_id` from request body (must come from authenticated session)
- **REJECT**: Any "temporary" cross-firm code paths

### 9.4 Privileged Data Handling
- **RULE**: Customer document content must never leak
- **CHECK**: Pre-commit hook blocks logging of `document.text`, `prompt`, `completion`
- **CHECK**: Sentry `beforeSend` scrubs privileged fields (verified in staging)
- **CHECK**: No analytics events contain document content
- **CHECK**: URL paths and page titles do not include document previews
- **CHECK**: Client-side storage (`localStorage`, IndexedDB, Zustand persist) never contains document text
- **CHECK**: External services (CourtListener, FJC) receive only the minimum (citation strings, quoted passages)
- **CHECK**: US-only data residency verified quarterly
- **REJECT**: Any code path that puts document content in logs, errors, analytics, or external calls beyond declared LLM provider
- **REJECT**: Page titles like "Review: [first 50 chars of document]"
- **REJECT**: Caching document content on the client

### 9.5 Review Queue & Reviewer Workflow
- **RULE**: The queue is the primary surface — keep it fast, keyboard-driven, and correct
- **CHECK**: Reviewer actions write audit entries transactionally
- **CHECK**: Finalize is blocked while flags are unresolved (enforced server-side)
- **CHECK**: OVERRIDE requires reason ≥10 chars (enforced both client and server)
- **CHECK**: Keyboard shortcuts implemented for every reviewer action
- **CHECK**: Optimistic UI with rollback tested
- **REJECT**: Finalize allowed with pending flags
- **REJECT**: OVERRIDE without reason
- **REJECT**: Reviewer flows that break keyboard-only operation

### 9.6 Firm & User Administration
- **RULE**: Admin operations are audited and safeguarded
- **CHECK**: Only ADMINs can invite/remove users, generate API keys, change roles
- **CHECK**: Last-admin safeguard enforced (cannot remove the only admin)
- **CHECK**: Users cannot modify their own role
- **CHECK**: API keys shown only at creation; never displayed again
- **CHECK**: Every admin action written to `audit_log`
- **REJECT**: Destructive admin actions without confirmation
- **REJECT**: Self-service role changes
- **REJECT**: API key re-display

### 9.7 External API Dependencies
- **RULE**: Treat CourtListener and FJC as mission-critical dependencies
- **CHECK**: Rate-limit headers monitored; alerts on approaching quota
- **CHECK**: Circuit breaker + retry with backoff in every external client
- **CHECK**: Local cache for court/judge data (refresh job runs nightly)
- **CHECK**: Evaluator failures due to external outage produce ADVISORY flags, not hard errors
- **CHECK**: Paid fallback (Westlaw/Lexis) plan documented; budget approved for V1.1
- **REJECT**: Uncached external calls in the hot path
- **REJECT**: No retry/backoff logic
- **REJECT**: Treating an external outage as a fatal evaluator failure

---

## 10. TECHNICAL DEBT MANAGEMENT

### 10.1 Debt Identification
- **RULE**: Track and document technical debt
- **CHECK**: Technical debt items logged in backlog with `debt` label
- **CHECK**: Debt prioritized by impact
- **CHECK**: Debt estimated like features
- **CHECK**: Architect consulted on priorities
- **CHECK**: Debt backlog maintained and reviewed monthly
- **REJECT**: Ignoring technical debt
- **REJECT**: No plan to address debt
- **REJECT**: Debt not prioritized

### 10.2 Debt Paydown Strategy
- **RULE**: Regular debt reduction
- **CHECK**: Allocate 20% of sprint capacity to debt (once V1 stabilizes post-launch)
- **CHECK**: Critical debt addressed immediately (tenant isolation, audit chain risks are never deferred)
- **CHECK**: Debt reduction tracked in metrics
- **CHECK**: Balance features with debt paydown
- **REJECT**: Always postponing debt work
- **REJECT**: 100% feature-focused sprints long-term
- **REJECT**: Accumulating debt without a plan

### 10.3 Preventing New Debt
- **RULE**: Quality over speed
- **CHECK**: Code review catches shortcuts
- **CHECK**: Refactoring encouraged when touching adjacent code
- **CHECK**: No shortcuts under pressure — especially on audit, tenancy, or privilege
- **CHECK**: Architecture guidelines followed (see `citeguard_architect_rules.md`)
- **REJECT**: "We'll fix it later" on audit/tenancy/privilege issues
- **REJECT**: Accepting low-quality code
- **REJECT**: Rushing to meet arbitrary deadlines at the cost of correctness

---

## 11. METRICS & REPORTING

### 11.1 Key Performance Indicators
- **RULE**: Track meaningful metrics
- **DELIVERY METRICS:**
  - Sprint velocity (story points per sprint)
  - Sprint completion rate (target: >85%)
  - Bug discovery rate
  - Bug fix time (P0 < 24h, P1 < 3 days)
  - Code review turnaround (<24h)
  - Deployment frequency
  - Test coverage (target: >80% backend, >70% frontend)
  - Production incidents per release
- **CITEGUARD-SPECIFIC METRICS:**
  - Evaluator accuracy on corpus (per evaluator, per version) — target: ≥95% true-positive, ≤5% false-positive
  - p50/p95/p99 evaluation latency
  - Audit chain verification pass rate (target: 100%)
  - Tenant isolation test pass rate (target: 100%)
  - Privileged data leak incidents (target: 0)
  - CourtListener API error rate
  - Design-partner satisfaction (measured quarterly)
  - Time to first verified document (new customer onboarding)
- **REJECT**: Vanity metrics without insight
- **REJECT**: Not tracking critical metrics
- **REJECT**: Metrics without action plans

### 11.2 Progress Reporting
- **RULE**: Transparent, regular reporting
- **CHECK**: Weekly status reports
- **CHECK**: Sprint burndown charts
- **CHECK**: Feature completion tracking
- **CHECK**: Timeline vs actual tracking
- **CHECK**: Risk register updates
- **CHECK**: Evaluator accuracy trend chart (per evaluator)
- **FORMAT**:
  - Executive Summary (1 paragraph)
  - Completed this week
  - In progress
  - Planned next week
  - Blockers & risks
  - Metrics (delivery + CiteGuard-specific)
- **REJECT**: Infrequent reporting
- **REJECT**: Hiding problems
- **REJECT**: No data to support status

### 11.3 Quality Metrics
- **RULE**: Measure and improve quality
- **CHECK**: Code coverage trends
- **CHECK**: Production bug rate
- **CHECK**: Customer-reported issues (from design partners)
- **CHECK**: Performance metrics (page load, evaluation latency)
- **CHECK**: Accessibility compliance
- **CHECK**: Evaluator accuracy trends
- **CHECK**: Audit chain integrity
- **TARGET**: <3 production bugs per release; 0 P0 bugs in production
- **REJECT**: No quality tracking
- **REJECT**: Declining quality trends ignored
- **REJECT**: Reactive quality management

---

## 12. DECISION-MAKING FRAMEWORK

### 12.1 Decision Authority
- **RULE**: Clear decision ownership
- **CHECK**: Technical decisions → Architect + Lead Devs (see `citeguard_architect_rules.md`)
- **CHECK**: UX decisions → Product Owner + Designer
- **CHECK**: Timeline decisions → PM + Stakeholders
- **CHECK**: Priority decisions → Product Owner + PM
- **CHECK**: Resource decisions → PM + Management
- **CHECK**: Evaluator changes with accuracy impact → Architect + PM + Product Owner
- **CHECK**: Document all major decisions (ADRs in `docs/adr/`)
- **REJECT**: Unclear decision ownership
- **REJECT**: Decisions by committee (too slow)
- **REJECT**: Undocumented major decisions

### 12.2 Escalation Path
- **RULE**: Clear escalation process
- **CHECK**: Technical issues → Lead Dev → Architect
- **CHECK**: Timeline issues → PM → Management
- **CHECK**: Resource issues → PM → Management
- **CHECK**: Quality issues → QA → PM → Architect
- **CHECK**: Scope issues → PM → Product Owner → Stakeholders
- **CHECK**: Privileged data leak / audit break / tenant isolation breach → PM + Architect IMMEDIATELY; full incident response
- **REJECT**: No escalation process
- **REJECT**: Bypassing proper channels
- **REJECT**: Escalating too late

### 12.3 Trade-off Decisions
- **RULE**: Data-driven trade-off analysis
- **CHECK**: Consider: scope, time, quality, resources
- **CHECK**: Document pros/cons of options
- **CHECK**: Involve relevant stakeholders
- **CHECK**: Assess long-term impact
- **CHECK**: Document decision rationale (ADR)
- **PRINCIPLE**: Quality and correctness on audit/tenancy/privilege are non-negotiable. Adjust scope or time, never quality.
- **REJECT**: Sacrificing audit integrity / tenant isolation / privilege safety for speed
- **REJECT**: Making trade-offs without analysis
- **REJECT**: Unilateral decisions on major trade-offs

---

## 13. PROJECT HEALTH INDICATORS

### 13.1 Green Flags (Healthy Project)
- ✅ Sprint completion rate consistently >85%
- ✅ Velocity stable sprint-over-sprint
- ✅ Code reviews completed <24 hours
- ✅ Minimal blockers, resolved quickly
- ✅ Test coverage improving or stable >80%
- ✅ Production bugs <3 per release
- ✅ 0 P0 bugs in production
- ✅ Evaluator accuracy ≥95% on corpus
- ✅ Audit chain verification: 100% pass
- ✅ Tenant isolation tests: 100% pass
- ✅ Team morale high
- ✅ Design partners satisfied
- ✅ Documentation up-to-date

### 13.2 Yellow Flags (Needs Attention)
- ⚠️ Sprint completion rate 70-85%
- ⚠️ Velocity declining for 2+ sprints
- ⚠️ Code reviews taking >48 hours
- ⚠️ Increasing number of blockers
- ⚠️ Test coverage declining
- ⚠️ Production bugs 3-10 per release
- ⚠️ Evaluator accuracy drift (0.5-1% degradation)
- ⚠️ CourtListener error rate rising
- ⚠️ Team members mentioning burnout
- ⚠️ Design partner concerns emerging
- ⚠️ Documentation falling behind

### 13.3 Red Flags (Critical Issues)
- 🚨 Sprint completion rate <70% for 2+ sprints
- 🚨 Velocity dropped >30%
- 🚨 Code reviews taking >3 days
- 🚨 Blockers lasting >2 days
- 🚨 Test coverage <60%
- 🚨 Production bugs >10 per release
- 🚨 ANY P0 bug in production (privileged data leak, audit break, tenant isolation)
- 🚨 Evaluator accuracy regression >1%
- 🚨 Audit chain verification failure
- 🚨 Design partner threatening to churn
- 🚨 Team member attrition
- 🚨 Stakeholder escalations

### 13.4 Response Actions
- **RULE**: Proactive problem resolution
- **GREEN**: Maintain course, continue improvements
- **YELLOW**: Identify root causes, implement corrective actions, monitor closely
- **RED**: Emergency intervention, re-plan sprint, escalate to management, initiate incident response for any P0 (CiteGuard-specific) event
- **REJECT**: Ignoring warning signs
- **REJECT**: Reactive instead of proactive
- **REJECT**: Not learning from issues

---

## 14. CODE REVIEW OVERSIGHT

### 14.1 Review Process Monitoring
- **RULE**: Ensure quality review process
- **CHECK**: All PRs reviewed within 24 hours
- **CHECK**: Reviews follow guidelines (`citeguard_architect_rules.md`, `citeguard_backend_guidelines.md`, `citeguard_frontend_guidelines.md`)
- **CHECK**: Constructive, educational feedback provided
- **CHECK**: No rubber-stamp approvals
- **CHECK**: Architect review for architectural changes
- **CHECK**: Extra scrutiny for changes to `AuditLogService`, tenant-scoped queries, evaluator logic, or anything touching privileged content paths
- **TARGET**: 100% code review compliance
- **REJECT**: Self-merged PRs
- **REJECT**: PRs with no comments (too-quick approvals)
- **REJECT**: Skipping reviews for "small changes"

### 14.2 Review Quality Standards
- **RULE**: Effective code reviews
- **CHECK**: Reviewers run the code locally when relevant
- **CHECK**: SOLID, duplication, performance, and security checked
- **CHECK**: Tests verified (including corpus tests for evaluator changes)
- **CHECK**: Documentation verified
- **CHECK**: Tenant isolation verified
- **CHECK**: Privileged data leak check performed
- **REJECT**: Approving without understanding the code
- **REJECT**: Only checking for syntax errors
- **REJECT**: Not verifying tests exist

### 14.3 Review Turnaround
- **RULE**: Fast, thorough reviews
- **TARGET**: First review within 4 hours
- **TARGET**: Final approval within 24 hours
- **CHECK**: Urgent PRs flagged and prioritized
- **CHECK**: Large PRs reviewed in chunks if needed
- **CHECK**: Blockers addressed immediately
- **REJECT**: PRs waiting days for review
- **REJECT**: Multiple rounds of back-and-forth due to unclear requirements
- **REJECT**: Last-minute rush approvals

---

## 15. LESSONS LEARNED & CONTINUOUS IMPROVEMENT

### 15.1 Retrospective Actions
- **RULE**: Act on retrospective insights
- **CHECK**: Action items from retros tracked
- **CHECK**: Action items assigned to owners
- **CHECK**: Progress reviewed in next retro
- **CHECK**: Successful actions celebrated
- **CHECK**: Failed actions analyzed
- **REJECT**: Retrospectives without actions
- **REJECT**: Action items forgotten
- **REJECT**: Same issues every retrospective

### 15.2 Process Improvements
- **RULE**: Evolve processes based on data
- **CHECK**: Review processes quarterly
- **CHECK**: Identify bottlenecks and inefficiencies
- **CHECK**: Propose improvements with team input
- **CHECK**: Pilot changes before full rollout
- **CHECK**: Measure impact of changes
- **REJECT**: Rigid, unchanging processes
- **REJECT**: Process changes without team buy-in
- **REJECT**: Not measuring improvement impact

### 15.3 Knowledge Sharing
- **RULE**: Promote team learning
- **CHECK**: Regular tech talks or lunch-and-learns
- **CHECK**: Pair programming encouraged
- **CHECK**: Documentation accessible and searchable
- **CHECK**: Onboarding materials up-to-date
- **CHECK**: Cross-training so no single point of failure on audit chain, evaluators, or critical paths
- **REJECT**: Knowledge silos
- **REJECT**: Only one person understands the hash chain / a given evaluator / the FastAPI setup
- **REJECT**: No knowledge transfer

---

## 16. CHECKLIST FOR PROJECT HEALTH

### Weekly PM Checklist:
- [ ] Sprint progress on track (>85% completion projected)
- [ ] All blockers identified and being resolved
- [ ] Code reviews happening within 24 hours
- [ ] All P0/P1 bugs have owners
- [ ] Risks reviewed and mitigation plans active
- [ ] Team capacity appropriate for planned work
- [ ] Stakeholder update sent
- [ ] Design-partner check-ins completed
- [ ] Evaluator accuracy metrics reviewed
- [ ] Audit chain verification passing
- [ ] Documentation up-to-date
- [ ] Next sprint backlog groomed
- [ ] Team morale good (1-on-1s scheduled)

### Sprint Start Checklist:
- [ ] Sprint goal clearly defined (mapped to V1 PRD milestones)
- [ ] All tasks estimated and assigned
- [ ] Dependencies identified
- [ ] Designs/requirements available for all tasks
- [ ] Team capacity confirmed
- [ ] Previous sprint retrospective actions addressed
- [ ] Stakeholders aware of sprint goal

### Sprint End Checklist:
- [ ] All committed work completed or carried over with reason
- [ ] Demo prepared for sprint review
- [ ] Retrospective scheduled
- [ ] Metrics collected (velocity, completion, bugs, evaluator accuracy, audit integrity)
- [ ] Documentation updated
- [ ] Release notes drafted if releasing
- [ ] Next sprint backlog ready
- [ ] Team availability confirmed for next sprint

### Release Checklist (CiteGuard):
- [ ] All features tested on staging
- [ ] Evaluator corpus regression passed
- [ ] Tenant isolation test suite passed
- [ ] Audit log hash chain verification passed
- [ ] Performance within p95 budget
- [ ] Security scan passed
- [ ] Release notes completed (customer-facing, privilege-safe)
- [ ] Alembic migration tested (up + down)
- [ ] Rollback plan documented
- [ ] Design partners notified
- [ ] Support team briefed
- [ ] Monitoring configured
- [ ] Backup taken
- [ ] Post-release monitoring plan ready

---

## 17. COMMUNICATION TEMPLATES

### Weekly Status Update Template:
```
# CiteGuard - Week of [Date]

## Executive Summary
[1-2 sentence overview of progress and health]

## Completed This Week
- [Feature/Task 1] - [Status/Impact]
- [Feature/Task 2] - [Status/Impact]

## In Progress
- [Feature/Task 1] - [Progress %] - [Expected completion]
- [Feature/Task 2] - [Progress %] - [Expected completion]

## Planned Next Week
- [Feature/Task 1]
- [Feature/Task 2]

## Blockers & Risks
- [Blocker 1] - [Mitigation plan]
- [Risk 1] - [Probability/Impact/Mitigation]

## Metrics
- Sprint Velocity: [X story points]
- Sprint Completion Rate: [X%]
- Code Coverage: [backend X% / frontend X%]
- Production Bugs: [X]
- Evaluator Accuracy (corpus): [per evaluator]
- p95 Evaluation Latency: [X ms]
- Audit Chain Verification: [pass/fail]
- Team Health: [Green/Yellow/Red]

## Design Partner Updates
- [Firm A]: [status, feedback, blockers]
- [Firm B]: [status, feedback, blockers]

## Next Milestones
- [Milestone 1] - [Target date]
- [Milestone 2] - [Target date]
```

### Sprint Review Template:
```
# Sprint [Number] Review - [Dates]

## Sprint Goal
[Original sprint goal]

## Completed Features
1. [Feature 1] - [Demo notes/screenshots]
2. [Feature 2] - [Demo notes/screenshots]

## Sprint Metrics
- Planned: [X] story points
- Completed: [X] story points
- Completion Rate: [X%]
- Velocity: [X] story points
- Bugs Fixed: [X]
- Test Coverage: [X%]
- Evaluator Accuracy Changes: [any deltas per evaluator]

## Not Completed
- [Item 1] - [Reason]
- [Item 2] - [Reason]

## Feedback Received
- [Design partner / stakeholder feedback]

## Next Sprint Focus
[Preview of next sprint goals]
```

---

## 18. ESCALATION GUIDELINES

### When to Escalate:

#### Escalate to Management Immediately:
- 🚨 Project at risk of missing major milestone (V1 launch date)
- 🚨 Budget overrun or resource shortage
- 🚨 Team member leaving/out sick affecting critical path
- 🚨 Design partner conflict cannot be resolved
- 🚨 Security breach or privileged data leak incident
- 🚨 Audit hash chain integrity failure
- 🚨 Tenant isolation breach discovered
- 🚨 Scope change requiring >30% timeline adjustment

#### Escalate to Architect:
- ⚠️ Technical debt blocking progress
- ⚠️ Architecture decision needed
- ⚠️ Performance issues affecting production (p95 latency trending over budget)
- ⚠️ Technology choice required for new feature
- ⚠️ Major refactoring needed
- ⚠️ Evaluator design question with accuracy implications
- ⚠️ Changes touching `AuditLogService`, tenant-scope enforcement, or privilege boundaries

#### Escalate to Product Owner:
- ⚠️ Unclear requirements blocking development
- ⚠️ Conflicting priorities
- ⚠️ Scope change requested by stakeholders or design partners
- ⚠️ Feature impact unclear
- ⚠️ User feedback requiring decision

### How to Escalate:
1. **Document the issue** clearly with impact assessment
2. **Propose 2-3 options** with pros/cons
3. **State your recommendation** with rationale
4. **Provide timeline** for decision needed
5. **Follow up** to ensure resolution

---

## 🎓 REMEMBER

**Focus on delivering value, not just managing tasks.**

Your role is to enable the team to do their best work, remove obstacles, protect audit integrity and privilege safety, and ensure we're building the right thing the right way.

**When facing challenges:**
- 🎯 Focus on solutions, not blame
- 📊 Use data to drive decisions
- 🤝 Communicate early and often
- 🛡️ Protect the team from interruptions
- 🚀 Celebrate wins, learn from losses

**Leadership Principles:**
- 🌟 Lead by example
- 💬 Communicate transparently
- 🎯 Be decisive but flexible
- 📚 Always be learning
- 🤝 Build trust with your team and design partners
- 🎖️ Take responsibility for outcomes

**Project Success Factors:**
- ✅ Clear goals and priorities (V1 PRD as source of truth)
- ✅ Realistic timelines and scope
- ✅ Happy, productive team
- ✅ Quality over speed — especially on audit, tenancy, privilege
- ✅ Regular communication
- ✅ Proactive risk management
- ✅ Continuous improvement

---

## 🎓 REMEMBER

**Only change what is explicitly requested.**

Resist the temptation to "improve" code or process that wasn't part of the request. Every unnecessary change increases risk and makes reviews harder.

**When in doubt:**
- ❓ Ask for clarification
- 📖 Read existing documentation (PRD, role-specific guidelines)
- 🔍 Search for similar past decisions (ADRs)
- 🚫 Don't assume or guess

---

## FINAL NOTE

Successful project management at CiteGuard is about balance: speed vs. quality, features vs. technical debt, stakeholder demands vs. team capacity — and above all, ensuring that on every release day, the team has protected customer privilege, audit integrity, and tenant isolation. Your job is to make the tough decisions, protect your team, deliver value, and keep everyone aligned and informed.

**Remember**: CiteGuard succeeds when law firms can trust every artifact we produce. That trust is built one sprint, one release, one audit entry at a time. Be the leader who makes that trust possible.