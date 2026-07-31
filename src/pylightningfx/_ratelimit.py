"""Client-side sliding-window request limiting."""

from collections import deque

from .config import RateLimits


class _Window:
    """Send timestamps for the requests inside one rolling window."""

    __slots__ = ("_hits", "_limit", "_period")

    def __init__(self, limit: int, period: float) -> None:
        self._limit = limit
        self._period = period
        self._hits: deque[float] = deque()

    def wait_for(self, now: float) -> float:
        """Seconds until a slot frees up, or ``0.0`` if one is free already."""
        cutoff = now - self._period
        while self._hits and self._hits[0] <= cutoff:
            self._hits.popleft()
        if len(self._hits) < self._limit:
            return 0.0
        return self._hits[0] + self._period - now

    def record(self, now: float) -> None:
        self._hits.append(now)


class Limiter:
    """Enforces the general and order-endpoint budgets together.

    Slots in both windows are reserved atomically: a call that needs the order
    budget takes a general slot only if it can take an order slot too, so a
    blocked order never silently burns general capacity.

    Sleeping and locking are left to the caller, which keeps one implementation
    usable from both the sync and the async client.
    """

    __slots__ = ("_general", "_order")

    def __init__(self, limits: RateLimits) -> None:
        self._general = _Window(limits.general, limits.period) if limits.general else None
        self._order = _Window(limits.order, limits.period) if limits.order else None

    def reserve(self, now: float, *, order: bool) -> float:
        """Take a slot, or report how long to wait before asking again.

        Returns ``0.0`` once the slot is reserved. A positive result means
        nothing was reserved and the caller should sleep that long and retry.
        """
        windows = [w for w in (self._general, self._order if order else None) if w is not None]
        wait = max((w.wait_for(now) for w in windows), default=0.0)
        if wait > 0.0:
            return wait
        for window in windows:
            window.record(now)
        return 0.0
