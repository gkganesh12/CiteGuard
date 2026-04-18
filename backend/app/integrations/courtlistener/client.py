"""CourtListener API client with retry, backoff, circuit breaker, and Redis cache.

Key behaviors (per ADR-0008):
- Retry: 3 attempts with exponential backoff (1s, 2s, 4s)
- Circuit breaker: 5 failures in 60s opens circuit for 30s
- Redis cache: 24h TTL for hits, 1h TTL for misses
- External failures produce ADVISORY flags, not hard errors
"""

from __future__ import annotations

import asyncio
import time

import httpx
import structlog

from app.config import settings
from app.integrations.courtlistener.schemas import (
    CitationLookupResult,
    NegativeTreatment,
    OpinionResult,
)

logger = structlog.get_logger()

# Circuit breaker state
_failure_count = 0
_last_failure_time = 0.0
_circuit_open_until = 0.0
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_FAILURE_WINDOW = 60  # seconds
CIRCUIT_OPEN_DURATION = 30  # seconds

# Retry settings
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 10.0

# Cache TTLs
CACHE_HIT_TTL = 86400  # 24 hours
CACHE_MISS_TTL = 3600  # 1 hour


def _is_circuit_open() -> bool:
    global _circuit_open_until
    if time.monotonic() < _circuit_open_until:
        return True
    return False


def _record_failure() -> None:
    global _failure_count, _last_failure_time, _circuit_open_until
    now = time.monotonic()
    if now - _last_failure_time > CIRCUIT_FAILURE_WINDOW:
        _failure_count = 0
    _failure_count += 1
    _last_failure_time = now
    if _failure_count >= CIRCUIT_FAILURE_THRESHOLD:
        _circuit_open_until = now + CIRCUIT_OPEN_DURATION


def _record_success() -> None:
    global _failure_count
    _failure_count = 0


class CourtListenerClient:
    """Async client for CourtListener REST API."""

    def __init__(self) -> None:
        self._base_url = settings.courtlistener_base_url
        self._token = settings.courtlistener_api_token
        self._redis: object | None = None  # Set via set_redis()

    def set_redis(self, redis_client: object) -> None:
        """Inject Redis client for caching."""
        self._redis = redis_client

    async def resolve_citation(
        self,
        volume: str,
        reporter: str,
        page: str,
    ) -> CitationLookupResult:
        """Resolve a citation by volume/reporter/page against CourtListener.

        Returns cached result if available. On failure, returns not-found
        rather than raising (failure-as-ADVISORY pattern).
        """
        cache_key = f"cl:{volume}:{reporter}:{page}"

        # Check cache first
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        # Check circuit breaker
        if _is_circuit_open():
            await logger.awarning("courtlistener_circuit_open")
            return CitationLookupResult(
                found=False,
                error="CourtListener temporarily unavailable (circuit breaker open)",
            )

        # Make API call with retry
        result = await self._call_with_retry(
            f"/search/",
            params={
                "type": "o",
                "q": f"{volume} {reporter} {page}",
            },
        )

        if result is None:
            lookup = CitationLookupResult(
                found=False, error="CourtListener API unavailable"
            )
            await self._cache_set(cache_key, lookup, CACHE_MISS_TTL)
            return lookup

        # Parse results
        results = result.get("results", [])
        if not results:
            lookup = CitationLookupResult(found=False)
            await self._cache_set(cache_key, lookup, CACHE_MISS_TTL)
            return lookup

        first = results[0]
        opinion = OpinionResult(
            id=first.get("id", 0),
            case_name=first.get("caseName", ""),
            court=first.get("court", ""),
            date_filed=first.get("dateFiled"),
            absolute_url=first.get("absolute_url"),
        )

        lookup = CitationLookupResult(found=True, opinion=opinion)
        await self._cache_set(cache_key, lookup, CACHE_HIT_TTL)
        return lookup

    async def fetch_opinion_text(self, opinion_id: int) -> str | None:
        """Fetch the full text of an opinion by ID."""
        cache_key = f"cl:opinion:{opinion_id}"

        cached_text = await self._cache_get_raw(cache_key)
        if cached_text is not None:
            return cached_text

        if _is_circuit_open():
            return None

        result = await self._call_with_retry(f"/opinions/{opinion_id}/")
        if result is None:
            return None

        text = result.get("plain_text") or result.get("html_with_citations") or ""
        if text:
            await self._cache_set_raw(cache_key, text, CACHE_HIT_TTL)
        return text or None

    async def _call_with_retry(
        self, path: str, params: dict | None = None
    ) -> dict | None:
        """Make an API call with retry and exponential backoff."""
        backoff = INITIAL_BACKOFF
        headers = {}
        if self._token:
            headers["Authorization"] = f"Token {self._token}"

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(
                        f"{self._base_url}{path}",
                        params=params,
                        headers=headers,
                    )
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", backoff))
                        await logger.awarning(
                            "courtlistener_rate_limited",
                            retry_after=retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    resp.raise_for_status()
                    _record_success()
                    return resp.json()

            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                _record_failure()
                await logger.awarning(
                    "courtlistener_request_failed",
                    attempt=attempt + 1,
                    error=str(exc),
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(min(backoff, MAX_BACKOFF))
                    backoff *= 2

        return None

    async def _cache_get(self, key: str) -> CitationLookupResult | None:
        if self._redis is None:
            return None
        try:
            import orjson
            data = await self._redis.get(key)  # type: ignore[union-attr]
            if data:
                return CitationLookupResult.model_validate_json(data)
        except Exception:
            pass
        return None

    async def _cache_set(
        self, key: str, value: CitationLookupResult, ttl: int
    ) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.set(key, value.model_dump_json(), ex=ttl)  # type: ignore[union-attr]
        except Exception:
            pass

    async def _cache_get_raw(self, key: str) -> str | None:
        if self._redis is None:
            return None
        try:
            data = await self._redis.get(key)  # type: ignore[union-attr]
            if data:
                return data.decode() if isinstance(data, bytes) else data
        except Exception:
            pass
        return None

    async def _cache_set_raw(self, key: str, value: str, ttl: int) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.set(key, value, ex=ttl)  # type: ignore[union-attr]
        except Exception:
            pass


# Singleton
courtlistener_client = CourtListenerClient()
