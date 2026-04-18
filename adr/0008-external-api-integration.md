# Architecture Decision Record (ADR)

**Status: Accepted**

## ADR-0008: External API Integration Strategy

### Decision

We have decided to integrate with the CourtListener REST API and the Federal Judicial Center (FJC) biographical directory using retry with exponential backoff, circuit breaker pattern, and Redis caching (24h TTL for hits, 1h for misses). External failures produce ADVISORY flags, not hard errors.

### Context

CiteGuard's evaluators depend on external APIs (CourtListener for case data, FJC for judge data). These are nonprofit/government services with rate limits and potential outages. The product must remain useful even when external APIs are down.

- CourtListener is a nonprofit service (Free Law Project) providing court opinion data. It has rate limits and occasional downtime.
- The Federal Judicial Center maintains a biographical directory of ~4,000 federal judges. The data changes infrequently (new appointments, retirements).
- Legal citations are highly repetitive — the same cases are cited across many documents and firms. Caching provides significant benefit.
- A hard failure when an external API is down would block document processing entirely, which is unacceptable for a production legal tool.
- External API calls must never send privileged document content (see ADR-0007). Only citation strings and judge names are transmitted.

### Rationale

#### Resilience via Retry and Circuit Breaker
- Retry with exponential backoff handles transient failures (network blips, temporary 503s) without manual intervention.
- Circuit breaker prevents cascading failures: if CourtListener is down for an extended period, the circuit opens and requests fail fast instead of timing out repeatedly.
- This combination is a well-established pattern for external service integration in distributed systems.

#### Redis Caching for Performance and Cost
- Legal citations are frequently repeated across documents and firms. Caching reduces API calls by an estimated 80-90%.
- Cache hit TTL of 24h balances freshness with performance. Court opinions rarely change after publication.
- Cache miss TTL of 1h prevents repeated lookups for citations that do not exist in CourtListener, while allowing relatively quick recovery if a new opinion is published.
- Redis provides sub-millisecond lookups, making cached evaluator checks effectively instant.

#### ADVISORY on Failure
- When an external API is unavailable, the evaluator returns an ADVISORY-level flag with an explanation ("External verification unavailable — citation not verified") rather than blocking the entire document.
- This ensures documents are always processed — just with reduced evaluator coverage during outages.
- Users see a clear indication that some checks were not performed, allowing them to take manual action if needed.

### Implementation Details

#### CourtListener Client (`app/integrations/courtlistener/client.py`)
- **HTTP Client**: `httpx` async client with connection pooling.
- **Retry Policy**: 3 attempts, exponential backoff starting at 1s, max 10s between retries. Retry on 429, 500, 502, 503, 504.
- **Circuit Breaker**: 5 failures within 60s opens the circuit for 30s. Half-open state allows a single probe request before fully closing.
- **Redis Cache**:
  - Key format: `cl:{volume}:{reporter}:{page}` (e.g., `cl:410:us:113`)
  - Hit TTL: 24 hours
  - Miss TTL: 1 hour
  - Cache is shared across all firms (citation data is public)
- **Rate Limit Monitoring**: Read `X-RateLimit-Remaining` header from responses. Log a warning when remaining < 20% of limit. Back off proactively when remaining < 10%.

#### FJC Integration (`app/integrations/fjc/`)
- **Data Storage**: Local Postgres table with ~4,000 federal judge records (name, court, appointment date, status).
- **Refresh Schedule**: Quarterly refresh via Arq scheduled task that downloads the FJC biographical directory CSV and upserts records.
- **No Real-Time API Dependency**: All judge lookups are local Postgres queries. No external API call at document processing time.
- **Fuzzy Matching**: Judge name lookup uses trigram similarity (`pg_trgm`) to handle name variations (e.g., "Sotomayor" vs. "Sonia Sotomayor").

#### Failure Handling by Evaluator
- **Citation Existence Evaluator**: If CourtListener is unavailable, returns ADVISORY with explanation "External verification unavailable — citation not verified."
- **Quote Verification Evaluator**: If CourtListener is unavailable, returns ADVISORY with explanation "Quote verification unavailable — external source unreachable."
- **Bluebook Formatting Evaluator**: Unaffected — uses local formatting rules only.
- **Judge Verification Evaluator**: Unaffected — uses local FJC data only.
- **Temporal Validity Evaluator**: If citation graph data is unavailable from CourtListener, returns ADVISORY with explanation "Temporal validity check unavailable — citation graph unreachable."

#### Data Minimization (per ADR-0007)
- CourtListener receives only citation strings (e.g., "410 U.S. 113"), never full document text.
- FJC refresh downloads public data; no CiteGuard data is sent to FJC.

### Consequences

**Positive:**
- Resilient to outages: Document processing continues with ADVISORY flags when external APIs are down, ensuring no blocked workflows.
- Reduced API costs: Redis caching reduces CourtListener API calls by 80-90%, staying well within free-tier rate limits.
- Fast lookups: Cached citation checks complete in sub-millisecond time. Local FJC lookups avoid network latency entirely.
- No real-time FJC dependency: Judge verification works even if the FJC website is completely offline.
- Public cache sharing: Citation data is public, so cache entries benefit all firms without tenant isolation concerns.

**Challenges:**
- Cache staleness: New court opinions will not appear in cache until existing entries expire (up to 24h). Mitigation: users can manually trigger a cache-busted re-check for specific citations in V2.
- FJC data lag: Quarterly refresh means recently appointed judges may not appear for up to 3 months. Mitigation: admin UI to trigger manual FJC refresh; ADVISORY flag for unrecognized judge names.
- CourtListener rate limits: At scale, the free tier may be insufficient. Mitigation: monitor usage, engage with Free Law Project for a paid/partnership tier, and increase cache TTLs if needed.
- Circuit breaker tuning: Threshold parameters (5 failures / 60s / 30s recovery) may need adjustment based on real-world CourtListener behavior. Mitigation: make parameters configurable via environment variables.

---

**Date:** 2026-04-18
**Supersedes:** None
**Related ADRs:** ADR-0007 (Privileged Data Handling)
