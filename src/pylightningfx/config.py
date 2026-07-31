"""Tunable client behaviour: retries and client-side rate limiting."""

import random
from dataclasses import dataclass, field

__all__ = ["RateLimits", "RetryPolicy"]

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """When and how far apart to retry a failed request.

    Retries are deliberately conservative about *writes*. A 5xx or a dropped
    connection on ``POST /v1/me/sendchildorder`` is ambiguous — the order may
    already be live on the exchange — so retrying it risks a double fill. By
    default only safe methods are retried on those failures.

    HTTP 429 is always retried regardless of method: a rate-limited request was
    rejected before it reached the matching engine, so replaying it cannot
    duplicate an order.

    Attributes:
        attempts: Total attempts per request, including the first one. ``1``
            disables retrying.
        backoff: Base delay in seconds. Doubles each attempt.
        max_backoff: Ceiling for a single delay, in seconds.
        retry_statuses: HTTP status codes worth retrying, on top of 429.
        retry_unsafe_methods: Retry ``POST`` too. Only enable this if every
            call you make is idempotent, or you reconcile orders afterwards.
    """

    attempts: int = 3
    backoff: float = 0.5
    max_backoff: float = 30.0
    retry_statuses: frozenset[int] = field(default_factory=lambda: frozenset({500, 502, 503, 504}))
    retry_unsafe_methods: bool = False

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("attempts must be >= 1")
        if self.backoff < 0 or self.max_backoff < 0:
            raise ValueError("backoff and max_backoff must be >= 0")

    def should_retry(self, method: str, status_code: int | None) -> bool:
        """Whether a failure is worth another attempt.

        Args:
            method: HTTP method of the failed request.
            status_code: Status code received, or ``None`` for a transport-level
                failure (timeout, reset connection) where the outcome is unknown.
        """
        if status_code == 429:
            return True
        if status_code is not None and status_code not in self.retry_statuses:
            return False
        return method.upper() in _SAFE_METHODS or self.retry_unsafe_methods

    def delay(self, attempt: int, retry_after: float | None = None) -> float:
        """Seconds to sleep before ``attempt``, which is 1-based.

        Honours a server-supplied ``retry_after`` when present, otherwise uses
        exponential backoff with full jitter on the lower half of the interval
        so that concurrent clients do not retry in lockstep.
        """
        if retry_after is not None:
            return min(max(retry_after, 0.0), self.max_backoff)
        base = min(self.backoff * 2.0 ** (attempt - 1), self.max_backoff)
        return base * (0.5 + random.random() / 2.0)


@dataclass(frozen=True, slots=True)
class RateLimits:
    """Client-side request budget, mirroring bitFlyer's published limits.

    The client tracks its own request timestamps and sleeps before sending when a
    window is full, so bursts get spread out instead of coming back as 429s. This
    is a courtesy backstop, not a guarantee: bitFlyer counts per IP and per
    account, so other processes sharing either will not be visible here.

    One limit is *not* modelled here: bitFlyer separately caps orders of size
    0.1 or less at 100 per minute, aggregated across every market, and drops you
    to 10 per minute for an hour if you exceed it. Sizing that budget needs to
    know each order's size, so pace small orders yourself.

    Attributes:
        general: Requests allowed per ``period`` across all endpoints, or
            ``None`` for no client-side limit. bitFlyer's own figure is 500 per
            5 minutes, applied per IP and again per account.
        order: Requests allowed per ``period`` across ``sendchildorder``,
            ``sendparentorder`` and ``cancelallchildorders``, which share one
            tighter budget of 300 per 5 minutes. ``None`` disables just this
            limit. Single-order cancels are not metered here.
        period: Length of the window in seconds.
    """

    general: int | None = 500
    order: int | None = 300
    period: float = 300.0

    @classmethod
    def disabled(cls) -> "RateLimits":
        """A budget that never delays a request."""
        return cls(general=None, order=None)
