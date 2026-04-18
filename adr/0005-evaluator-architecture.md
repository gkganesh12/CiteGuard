# Architecture Decision Record (ADR)

**Status: Accepted**

## ADR-0005: Evaluator System Architecture

### Decision

We have decided to implement evaluators as **versioned strategy objects** conforming to an **`IEvaluator` protocol**, orchestrated via **`asyncio.gather`** for parallel fan-out. External failures (CourtListener, FJC) produce **ADVISORY flags** instead of hard errors, ensuring that external service outages degrade quality but never block the reviewer workflow.

### Context

- CiteGuard V1 runs 5 deterministic evaluators on every submitted document: citation existence, quote verification, Bluebook format, judge verification, and temporal validity.
- Each evaluator must be independently developable, testable, and versionable. A change to one evaluator must not require changes to others.
- Evaluators depend on external services (CourtListener API for citation verification, FJC database for judge verification) that may be unavailable. External failures must not block document processing.
- Every change to evaluator logic must bump the evaluator's version number. This ensures that flags in the audit trail can be traced back to the exact evaluator logic that produced them.
- Every PR that modifies evaluator code must include a corpus regression report (50 seeded hallucinations + 50 clean documents) to ensure accuracy is not degraded.
- Evaluators must run in parallel to minimize total evaluation time for a document.

### Rationale

#### Strategy Pattern for Evaluator Independence
- Each evaluator is a self-contained class that implements the `IEvaluator` protocol. This provides a clean separation of concerns: the orchestrator manages fan-out and error handling, while each evaluator focuses on its domain logic.
- New evaluators can be added by implementing the protocol and registering with the orchestrator — no changes to existing evaluators or orchestration logic required.
- Each evaluator can be unit-tested in isolation with mock inputs, independent of the orchestrator and other evaluators.

#### asyncio.gather for Parallel Fan-Out
- `asyncio.gather` runs all evaluators concurrently within a single worker process, maximizing parallelism for I/O-bound evaluators (external API calls) without the overhead of multi-processing.
- Per-evaluator timeouts (10 seconds default) prevent a single slow evaluator from blocking the entire evaluation pipeline.
- `return_exceptions=True` ensures that one evaluator's failure does not cancel the others.

#### External Failures as ADVISORY Flags
- CourtListener and FJC are external services beyond CiteGuard's control. Their unavailability should not prevent document processing.
- When an external call fails (timeout, HTTP error, rate limit), the evaluator produces an ADVISORY-severity flag explaining that verification could not be completed, rather than raising an exception.
- This ensures the reviewer sees the document with a note that certain checks were inconclusive, rather than the document being stuck in a "pending" state indefinitely.

#### Semantic Versioning for Evaluator Logic
- Each evaluator has a version following semver (major.minor.patch).
- Major version bumps indicate breaking changes to the evaluator's flag output schema.
- Minor version bumps indicate new detection capabilities or accuracy improvements.
- Patch version bumps indicate bug fixes that do not change detection behavior.
- The version is recorded on every flag, allowing historical analysis of evaluator accuracy by version.

### Implementation Details

#### IEvaluator Protocol
```python
class IEvaluator(Protocol):
    @property
    def name(self) -> str:
        """Unique evaluator identifier (e.g., 'citation_existence')."""
        ...

    @property
    def version(self) -> str:
        """Semantic version of the evaluator logic (e.g., '1.2.0')."""
        ...

    async def evaluate(
        self,
        document: Document,
        context: EvaluationContext,
    ) -> list[FlagResult]:
        """
        Evaluate a document and return zero or more flags.

        Must not raise exceptions for expected failures (external API
        errors, malformed input). Instead, return an ADVISORY flag.

        May raise exceptions only for unexpected internal errors
        (these are caught by the orchestrator and converted to
        ADVISORY flags).
        """
        ...
```

#### FlagResult Dataclass
- **evaluator_name**: `str` — which evaluator produced this flag
- **evaluator_version**: `str` — semver of the evaluator at the time of evaluation
- **severity**: `Severity` — one of CRITICAL, HIGH, MEDIUM, ADVISORY
- **explanation**: `str` — human-readable explanation of the flag for the reviewer
- **confidence**: `float` — confidence score between 0.0 and 1.0
- **start_offset**: `int | None` — character offset in the document where the flagged content starts
- **end_offset**: `int | None` — character offset where the flagged content ends
- **suggested_correction**: `str | None` — optional suggested fix for the flagged issue
- **raw_output**: `dict` — full evaluator output for debugging and audit (stored as JSONB)

#### EvaluatorOrchestrator
- **Registration**: Evaluators are registered at application startup. The orchestrator maintains an ordered list of `IEvaluator` instances.
- **Execution**: `orchestrator.run(document, context)` calls `asyncio.gather(*[e.evaluate(document, context) for e in evaluators], return_exceptions=True)`.
- **Per-evaluator timeout**: Each `evaluate()` call is wrapped in `asyncio.wait_for(timeout=10.0)`. Timeout produces an ADVISORY flag: "Evaluator {name} timed out after 10 seconds."
- **Exception handling**: If an evaluator raises an unexpected exception, the orchestrator catches it and produces an ADVISORY flag: "Evaluator {name} encountered an internal error." The exception is logged (without document content) for debugging.
- **Result aggregation**: All FlagResult lists from all evaluators are flattened into a single list, sorted by severity (CRITICAL first), and returned.

#### V1 Evaluators

##### Citation Existence Evaluator (`citation_existence`, v1.0.0)
- Uses `eyecite` to extract legal citations from document text.
- Verifies each citation exists via CourtListener API (with retry, backoff, circuit breaker).
- External failure: produces ADVISORY flag per unverified citation.
- Cached responses: CourtListener results cached in Redis (TTL: 24 hours).

##### Quote Verification Evaluator (`quote_verification`, v1.0.0)
- Extracts quoted passages attributed to court opinions.
- Retrieves source text from CourtListener.
- Uses `rapidfuzz` for fuzzy matching with configurable similarity threshold (default: 85%).
- Flags mismatches as CRITICAL (below 50% similarity) or HIGH (50-85% similarity).

##### Bluebook Format Evaluator (`bluebook_format`, v1.0.0)
- Parses citations and checks conformance to Bluebook citation format rules.
- Entirely local (no external dependencies).
- Flags format violations as MEDIUM severity.

##### Judge Verification Evaluator (`judge_verification`, v1.0.0)
- Extracts judge names mentioned in document.
- Verifies against FJC (Federal Judicial Center) database that the judge served on the referenced court during the referenced time period.
- External failure: produces ADVISORY flag per unverified judge reference.

##### Temporal Validity Evaluator (`temporal_validity`, v1.0.0)
- Checks whether cited cases have been overruled, reversed, or otherwise invalidated.
- Uses CourtListener's citation network data.
- Flags citations to overruled cases as CRITICAL.
- External failure: produces ADVISORY flag.

#### Corpus Regression Testing
- **Fixture corpus**: 100 documents stored in the test fixtures directory.
  - 50 documents with seeded hallucinations (fabricated citations, misquoted passages, incorrect judge attributions, Bluebook violations, citations to overruled cases).
  - 50 clean documents with verified-correct legal content.
- **Regression report**: For each evaluator, reports precision, recall, and F1 score against the labeled corpus.
- **Merge gate**: Any accuracy regression (lower F1 score compared to the previous version) blocks the PR merge until explicit product owner sign-off.
- **Execution**: Run as part of CI on every PR that modifies files in the evaluator source directory.

#### External API Resilience
- **Retries**: 3 attempts with exponential backoff (1s, 2s, 4s).
- **Circuit breaker**: Opens after 5 consecutive failures, half-opens after 30 seconds.
- **Cached fallback**: If the circuit breaker is open, use cached results from Redis if available.
- **Timeout**: 5 seconds per external API call (separate from the 10-second per-evaluator timeout).

### Consequences

**Positive:**
- Parallel execution: all 5 evaluators run concurrently via asyncio.gather, minimizing total evaluation time.
- Independent development and testing: each evaluator is a self-contained strategy object with its own version, tests, and regression corpus.
- Graceful degradation: external service failures produce informational ADVISORY flags rather than blocking the workflow. Reviewers always see their documents.
- Version tracking: every flag records the exact evaluator version, enabling historical accuracy analysis and audit trail traceability.
- Extensibility: adding a new evaluator requires implementing the IEvaluator protocol and registering it — no changes to existing code.

**Challenges:**
- asyncio.gather error handling complexity: `return_exceptions=True` means the orchestrator must check each result for exceptions. Thorough testing of failure scenarios is required.
- Corpus maintenance overhead: the 100-document fixture corpus must be maintained as evaluator capabilities evolve. New detection rules may require new corpus documents.
- Partial results in UI: when some evaluators fail and produce ADVISORY flags, the frontend must clearly communicate which checks were inconclusive vs. which checks passed or found issues.
- Per-evaluator timeouts may be too aggressive: 10 seconds may not be enough for CourtListener queries on documents with many citations. Configurable per-evaluator timeout overrides are supported.
- Confidence calibration: the 0-1 confidence score must be meaningful and consistent across evaluators. This requires ongoing calibration against the regression corpus.

---

**Related Documents:**
- `docs/PRD_v1.md` — V1 product requirements (5 evaluators defined)
- `adr/0002-database-schema.md` — flags table schema
- `adr/0003-audit-log-hash-chain.md` — evaluation_complete and flag_created events
- `adr/0004-tenant-isolation.md` — firm_id scoping on flags
- `RnR/citeguard_backend_guidelines.md` — backend coding standards
- `RnR/citeguard_qa_rules.md` — corpus regression testing requirements
