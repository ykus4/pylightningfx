"""Shared test helpers.

Nothing in the suite touches the network: every client is wired to an
:class:`httpx.MockTransport` that records what it was asked for and replays
canned responses.
"""

from typing import Any

import httpx
import pytest

from pylightningfx import AsyncClient, Client, RateLimits, RetryPolicy

FAKE_KEY = "test-key"
FAKE_SECRET = "test-secret"


class Recorder:
    """A fake bitFlyer: records requests, replays queued responses.

    Queue one response per expected request. The last one repeats if more
    requests arrive, which keeps the common single-request test to one argument.
    """

    def __init__(self, *responses: httpx.Response) -> None:
        self.responses = list(responses) or [httpx.Response(200, json={})]
        self.requests: list[httpx.Request] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        request.read()  # make request.content available to assertions
        self.requests.append(request)
        return self.responses[min(len(self.requests) - 1, len(self.responses) - 1)]

    @property
    def transport(self) -> httpx.MockTransport:
        """A transport usable by both the sync and the async client."""
        return httpx.MockTransport(self.handle)

    @property
    def request(self) -> httpx.Request:
        """The one request that was sent; fails if there was not exactly one."""
        assert len(self.requests) == 1, f"expected exactly 1 request, got {len(self.requests)}"
        return self.requests[0]

    @property
    def count(self) -> int:
        return len(self.requests)


def ok(payload: Any) -> httpx.Response:
    """A 200 carrying ``payload`` as JSON."""
    return httpx.Response(200, json=payload)


def empty() -> httpx.Response:
    """A 200 with a zero-length body, as the cancel endpoints return."""
    return httpx.Response(200, content=b"")


def error(status_code: int, status: int = -100, message: str = "Invalid product") -> httpx.Response:
    """A bitFlyer-shaped error response."""
    return httpx.Response(
        status_code, json={"status": status, "error_message": message, "data": None}
    )


def sync_client(
    *responses: httpx.Response, authed: bool = False, **kwargs: Any
) -> tuple[Client, Recorder]:
    """A :class:`Client` backed by canned responses, plus its recorder.

    Retries and rate limiting are off by default so tests neither sleep nor
    accidentally depend on them; the tests that care pass their own.
    """
    recorder = Recorder(*responses)
    kwargs.setdefault("retry", RetryPolicy(attempts=1))
    kwargs.setdefault("rate_limits", RateLimits.disabled())
    client = Client(
        FAKE_KEY if authed else "",
        FAKE_SECRET if authed else "",
        transport=recorder.transport,
        **kwargs,
    )
    return client, recorder


def async_client(
    *responses: httpx.Response, authed: bool = False, **kwargs: Any
) -> tuple[AsyncClient, Recorder]:
    """An :class:`AsyncClient` backed by canned responses, plus its recorder."""
    recorder = Recorder(*responses)
    kwargs.setdefault("retry", RetryPolicy(attempts=1))
    kwargs.setdefault("rate_limits", RateLimits.disabled())
    client = AsyncClient(
        FAKE_KEY if authed else "",
        FAKE_SECRET if authed else "",
        transport=recorder.transport,
        **kwargs,
    )
    return client, recorder


class Clock:
    """Stands in for the ``time`` module inside the engine.

    Sleeping advances the clock instead of blocking, so a test can drive the
    retry and throttle loops through minutes of simulated waiting instantly.
    """

    def __init__(self) -> None:
        self.now = 0.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    """Replace the engine's view of ``time`` with a controllable fake."""
    fake = Clock()
    monkeypatch.setattr("pylightningfx._engine.time", fake)
    return fake


@pytest.fixture
def no_sleep(clock: Clock) -> list[float]:
    """The delays the engine would have slept for, without any real waiting."""
    return clock.slept
