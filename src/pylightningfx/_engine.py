"""The request loop shared by every API method: throttle, sign, send, retry."""

import asyncio
import threading
import time
from typing import Any, Self

import httpx

from ._ratelimit import Limiter
from ._transport import (
    BASE_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    NEVER_RETRY_PATHS,
    ORDER_PATHS,
    RateLimitState,
    build_error,
    decode_response,
    prepare_request,
)
from .config import RateLimits, RetryPolicy
from .errors import RateLimitError

_UNREACHABLE = "retry loop exited without a result"


class _EngineBase:
    """Configuration and state common to the sync and async engines."""

    _http: httpx.Client | httpx.AsyncClient

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        *,
        retry: RetryPolicy | None = None,
        rate_limits: RateLimits | None = None,
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._retry = retry if retry is not None else RetryPolicy()
        self._limiter = Limiter(rate_limits if rate_limits is not None else RateLimits())
        self._rate_limit: RateLimitState | None = None
        self._owns_http = True

    @property
    def rate_limit(self) -> RateLimitState | None:
        """bitFlyer's rate limit counters as of the most recent response.

        ``None`` until the first request completes, or if the server stopped
        sending the ``X-RateLimit-*`` headers.
        """
        return self._rate_limit

    def _observe(self, response: httpx.Response) -> None:
        state = RateLimitState.from_response(response)
        if state is not None:
            self._rate_limit = state

    def _delay_for(self, attempt: int, error: Exception | None) -> float:
        after = error.retry_after if isinstance(error, RateLimitError) else None
        return self._retry.delay(attempt, after)

    @staticmethod
    def _client_kwargs(
        base_url: str,
        timeout: float | httpx.Timeout | None,
        headers: dict[str, str] | None,
    ) -> dict[str, Any]:
        merged = {"User-Agent": DEFAULT_USER_AGENT}
        if headers:
            merged.update(headers)
        return {"base_url": base_url, "timeout": timeout, "headers": merged}


class SyncEngine(_EngineBase):
    """Synchronous HTTP engine.

    Args:
        api_key: API key. Only needed for Private API calls.
        api_secret: API secret. Only needed for Private API calls.
        timeout: Request timeout in seconds, or an `httpx.Timeout`.
            ``None`` waits forever, which is rarely what you want against an
            exchange.
        base_url: API root. Override to point at a mock server.
        retry: Retry behaviour. See [`RetryPolicy`][pylightningfx.RetryPolicy].
        rate_limits: Client-side request budget. See
            [`RateLimits`][pylightningfx.RateLimits]. Pass ``RateLimits.disabled()``
            to opt out.
        headers: Extra headers sent with every request.
        transport: Custom `httpx.BaseTransport`, e.g. an
            `httpx.MockTransport` in tests.
        http_client: An existing `httpx.Client` to send through, for
            connection pooling or proxy configuration you already own. When
            given, ``timeout``, ``base_url``, ``headers`` and ``transport`` are
            ignored, and closing the client stays your responsibility.
    """

    _http: httpx.Client

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        *,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        base_url: str = BASE_URL,
        retry: RetryPolicy | None = None,
        rate_limits: RateLimits | None = None,
        headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(api_key, api_secret, retry=retry, rate_limits=rate_limits)
        self._lock = threading.Lock()
        if http_client is not None:
            self._http = http_client
            self._owns_http = False
        else:
            self._http = httpx.Client(
                transport=transport, **self._client_kwargs(base_url, timeout, headers)
            )

    def close(self) -> None:
        """Close the underlying connection pool, unless it was passed in."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _throttle(self, *, order: bool) -> None:
        while True:
            with self._lock:
                wait = self._limiter.reserve(time.monotonic(), order=order)
            if wait <= 0.0:
                return
            time.sleep(wait)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        *,
        private: bool = False,
    ) -> Any:
        order = path in ORDER_PATHS
        attempts = 1 if path in NEVER_RETRY_PATHS else self._retry.attempts
        for attempt in range(1, attempts + 1):
            self._throttle(order=order)
            request = prepare_request(
                self._http,
                method,
                path,
                params=params,
                body=body,
                private=private,
                api_key=self._api_key,
                api_secret=self._api_secret,
            )
            try:
                response = self._http.send(request)
            except httpx.TransportError:
                if attempt == attempts or not self._retry.should_retry(method, None):
                    raise
                time.sleep(self._delay_for(attempt, None))
                continue

            self._observe(response)
            if response.is_success:
                return decode_response(response)

            error = build_error(response)
            if attempt == attempts or not self._retry.should_retry(method, response.status_code):
                raise error
            time.sleep(self._delay_for(attempt, error))

        raise AssertionError(_UNREACHABLE)  # pragma: no cover

    def _get(
        self, path: str, params: dict[str, Any] | None = None, *, private: bool = False
    ) -> Any:
        return self._request("GET", path, params=params, private=private)

    def _post(self, path: str, body: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, body=body or {}, private=True)


class AsyncEngine(_EngineBase):
    """Asynchronous HTTP engine.

    Takes the same arguments as `SyncEngine`, with
    `httpx.AsyncBaseTransport` and `httpx.AsyncClient` in place of
    their blocking counterparts.
    """

    _http: httpx.AsyncClient

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        *,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        base_url: str = BASE_URL,
        retry: RetryPolicy | None = None,
        rate_limits: RateLimits | None = None,
        headers: dict[str, str] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(api_key, api_secret, retry=retry, rate_limits=rate_limits)
        self._alock = asyncio.Lock()
        if http_client is not None:
            self._http = http_client
            self._owns_http = False
        else:
            self._http = httpx.AsyncClient(
                transport=transport, **self._client_kwargs(base_url, timeout, headers)
            )

    async def aclose(self) -> None:
        """Close the underlying connection pool, unless it was passed in."""
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def _throttle(self, *, order: bool) -> None:
        while True:
            async with self._alock:
                wait = self._limiter.reserve(time.monotonic(), order=order)
            if wait <= 0.0:
                return
            await asyncio.sleep(wait)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        *,
        private: bool = False,
    ) -> Any:
        order = path in ORDER_PATHS
        attempts = 1 if path in NEVER_RETRY_PATHS else self._retry.attempts
        for attempt in range(1, attempts + 1):
            await self._throttle(order=order)
            request = prepare_request(
                self._http,
                method,
                path,
                params=params,
                body=body,
                private=private,
                api_key=self._api_key,
                api_secret=self._api_secret,
            )
            try:
                response = await self._http.send(request)
            except httpx.TransportError:
                if attempt == attempts or not self._retry.should_retry(method, None):
                    raise
                await asyncio.sleep(self._delay_for(attempt, None))
                continue

            self._observe(response)
            if response.is_success:
                return decode_response(response)

            error = build_error(response)
            if attempt == attempts or not self._retry.should_retry(method, response.status_code):
                raise error
            await asyncio.sleep(self._delay_for(attempt, error))

        raise AssertionError(_UNREACHABLE)  # pragma: no cover

    async def _get(
        self, path: str, params: dict[str, Any] | None = None, *, private: bool = False
    ) -> Any:
        return await self._request("GET", path, params=params, private=private)

    async def _post(self, path: str, body: dict[str, Any] | None = None) -> Any:
        return await self._request("POST", path, body=body or {}, private=True)
