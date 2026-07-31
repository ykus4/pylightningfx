"""Client-side rate limiting."""

import httpx
import pytest

from pylightningfx import Client, RateLimits, RetryPolicy
from pylightningfx._ratelimit import Limiter, _Window

from .conftest import Clock, Recorder, ok


class TestWindow:
    def test_allows_up_to_the_limit(self) -> None:
        window = _Window(limit=2, period=10.0)
        assert window.wait_for(0.0) == 0.0
        window.record(0.0)
        assert window.wait_for(1.0) == 0.0
        window.record(1.0)
        assert window.wait_for(2.0) == pytest.approx(8.0)

    def test_slot_frees_once_the_oldest_hit_ages_out(self) -> None:
        window = _Window(limit=1, period=10.0)
        window.record(0.0)
        assert window.wait_for(5.0) == pytest.approx(5.0)
        assert window.wait_for(10.0) == 0.0

    def test_old_hits_are_discarded(self) -> None:
        window = _Window(limit=1, period=10.0)
        for t in range(0, 100, 20):
            assert window.wait_for(float(t)) == 0.0
            window.record(float(t))


class TestLimiter:
    def test_general_budget_is_enforced(self) -> None:
        limiter = Limiter(RateLimits(general=2, order=None, period=10.0))
        assert limiter.reserve(0.0, order=False) == 0.0
        assert limiter.reserve(1.0, order=False) == 0.0
        assert limiter.reserve(2.0, order=False) == pytest.approx(8.0)

    def test_order_budget_is_tighter_than_general(self) -> None:
        limiter = Limiter(RateLimits(general=10, order=1, period=10.0))
        assert limiter.reserve(0.0, order=True) == 0.0
        assert limiter.reserve(1.0, order=True) > 0.0

    def test_blocked_order_does_not_burn_general_capacity(self) -> None:
        """Both windows are reserved atomically, or neither is."""
        limiter = Limiter(RateLimits(general=10, order=1, period=10.0))
        limiter.reserve(0.0, order=True)  # takes 1 order slot and 1 general slot
        assert limiter.reserve(1.0, order=True) > 0.0  # order full, reserves nothing

        # 9 general slots must remain, so nine non-order calls pass straight through.
        for i in range(9):
            assert limiter.reserve(1.0 + i * 0.01, order=False) == 0.0
        assert limiter.reserve(2.0, order=False) > 0.0

    def test_non_order_calls_ignore_the_order_budget(self) -> None:
        limiter = Limiter(RateLimits(general=10, order=1, period=10.0))
        limiter.reserve(0.0, order=True)
        assert limiter.reserve(1.0, order=False) == 0.0

    def test_disabled_never_waits(self) -> None:
        limiter = Limiter(RateLimits.disabled())
        for i in range(1000):
            assert limiter.reserve(float(i) * 1e-6, order=True) == 0.0

    def test_defaults_match_bitflyer(self) -> None:
        limits = RateLimits()
        assert (limits.general, limits.order, limits.period) == (500, 300, 300.0)


class TestClientThrottling:
    def _client(self, limits: RateLimits, requests: int) -> tuple[Client, Recorder]:
        recorder = Recorder(*[ok({"status": "NORMAL"}) for _ in range(requests)])
        client = Client(
            transport=recorder.transport,
            retry=RetryPolicy(attempts=1),
            rate_limits=limits,
        )
        return client, recorder

    def test_sleeps_once_the_window_is_full(self, clock: Clock) -> None:
        client, api = self._client(RateLimits(general=2, order=None, period=10.0), 3)
        with client:
            client.get_health()
            client.get_health()
            assert clock.slept == []
            client.get_health()
        assert api.count == 3
        assert clock.slept == [pytest.approx(10.0)]

    def test_does_not_sleep_within_budget(self, clock: Clock) -> None:
        client, _ = self._client(RateLimits(general=50, order=None, period=10.0), 10)
        with client:
            for _ in range(10):
                client.get_health()
        assert clock.slept == []

    def test_order_endpoints_draw_on_the_tighter_budget(self, clock: Clock) -> None:
        recorder = Recorder(*[ok({"child_order_acceptance_id": "JRF1"}) for _ in range(2)])
        client = Client(
            "k",
            "s",
            transport=recorder.transport,
            retry=RetryPolicy(attempts=1),
            rate_limits=RateLimits(general=100, order=1, period=30.0),
        )
        with client:
            client.send_child_order("BTC_JPY", "MARKET", "BUY", 0.01)
            client.send_child_order("BTC_JPY", "MARKET", "BUY", 0.01)
        assert clock.slept == [pytest.approx(30.0)]

    def test_single_order_cancel_is_not_order_metered(self, clock: Clock) -> None:
        """cancelchildorder is outside bitFlyer's 300-per-5-minutes order bucket."""
        recorder = Recorder(*[httpx.Response(200, content=b"") for _ in range(5)])
        client = Client(
            "k",
            "s",
            transport=recorder.transport,
            retry=RetryPolicy(attempts=1),
            rate_limits=RateLimits(general=100, order=1, period=30.0),
        )
        with client:
            for _ in range(5):
                client.cancel_child_order("BTC_JPY", child_order_id="x")
        assert clock.slept == []
