"""Retry behaviour.

The safety property under test: a write whose outcome is unknown is not replayed
by default, because a resent order can fill twice.
"""

import httpx
import pytest

from pylightningfx import APIError, Client, RateLimitError, RateLimits, RetryPolicy

from .conftest import FAKE_KEY, FAKE_SECRET, Recorder, error, ok


def client_with(
    *responses: httpx.Response, retry: RetryPolicy, authed: bool = True
) -> tuple[Client, Recorder]:
    recorder = Recorder(*responses)
    client = Client(
        FAKE_KEY if authed else "",
        FAKE_SECRET if authed else "",
        transport=recorder.transport,
        retry=retry,
        rate_limits=RateLimits.disabled(),
    )
    return client, recorder


def raising_client(exc: Exception, retry: RetryPolicy) -> tuple[Client, list[int]]:
    """A client whose transport always fails, counting the attempts."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise exc

    client = Client(
        FAKE_KEY,
        FAKE_SECRET,
        transport=httpx.MockTransport(handler),
        retry=retry,
        rate_limits=RateLimits.disabled(),
    )
    return client, calls


class TestSafeMethods:
    def test_get_retries_5xx_then_succeeds(self, no_sleep: list[float]) -> None:
        client, api = client_with(
            error(503, message="unavailable"), ok({"status": "NORMAL"}), retry=RetryPolicy()
        )
        with client:
            assert client.get_health().status == "NORMAL"
        assert api.count == 2
        assert len(no_sleep) == 1

    def test_get_gives_up_after_attempts(self, no_sleep: list[float]) -> None:
        client, api = client_with(error(500, message="boom"), retry=RetryPolicy(attempts=3))
        with client, pytest.raises(APIError):
            client.get_health()
        assert api.count == 3
        assert len(no_sleep) == 2

    def test_attempts_one_disables_retrying(self, no_sleep: list[float]) -> None:
        client, api = client_with(error(500), retry=RetryPolicy(attempts=1))
        with client, pytest.raises(APIError):
            client.get_health()
        assert api.count == 1
        assert no_sleep == []

    def test_4xx_is_not_retried(self, no_sleep: list[float]) -> None:
        client, api = client_with(error(400, status=-100), retry=RetryPolicy(attempts=4))
        with client, pytest.raises(APIError):
            client.get_health()
        assert api.count == 1

    def test_transport_error_is_retried_for_get(self, no_sleep: list[float]) -> None:
        client, calls = raising_client(httpx.ConnectError("no route"), RetryPolicy(attempts=3))
        with client, pytest.raises(httpx.ConnectError):
            client.get_health()
        assert len(calls) == 3


class TestUnsafeMethods:
    def test_post_5xx_is_not_retried_by_default(self, no_sleep: list[float]) -> None:
        """A 5xx on sendchildorder may mean the order is live; do not resend it."""
        client, api = client_with(error(502, message="bad gateway"), retry=RetryPolicy(attempts=5))
        with client, pytest.raises(APIError):
            client.send_child_order("BTC_JPY", "MARKET", "BUY", 0.01)
        assert api.count == 1
        assert no_sleep == []

    def test_post_transport_error_is_not_retried_by_default(self) -> None:
        """A timeout is the most ambiguous case of all: the order may have landed."""
        client, calls = raising_client(httpx.ReadTimeout("timed out"), RetryPolicy(attempts=5))
        with client, pytest.raises(httpx.ReadTimeout):
            client.send_child_order("BTC_JPY", "MARKET", "BUY", 0.01)
        assert len(calls) == 1

    def test_post_retries_when_explicitly_opted_in(self, no_sleep: list[float]) -> None:
        client, api = client_with(
            error(502),
            ok({"child_order_acceptance_id": "JRF1"}),
            retry=RetryPolicy(retry_unsafe_methods=True),
        )
        with client:
            ack = client.send_child_order("BTC_JPY", "MARKET", "BUY", 0.01)
        assert ack.child_order_acceptance_id == "JRF1"
        assert api.count == 2

    def test_429_is_retried_on_post_without_opt_in(self, no_sleep: list[float]) -> None:
        """A rate-limited request never reached the matching engine, so it is safe."""
        rejected = httpx.Response(429, json={"status": -1, "error_message": "slow down"})
        client, api = client_with(
            rejected, ok({"child_order_acceptance_id": "JRF1"}), retry=RetryPolicy()
        )
        with client:
            client.send_child_order("BTC_JPY", "MARKET", "BUY", 0.01)
        assert api.count == 2

    def test_429_surfaces_as_rate_limit_error_when_persistent(self, no_sleep: list[float]) -> None:
        client, _ = client_with(httpx.Response(429, json={}), retry=RetryPolicy(attempts=2))
        with client, pytest.raises(RateLimitError):
            client.get_health()


class TestWithdrawIsNeverRetried:
    def test_not_retried_even_with_unsafe_opt_in(self, no_sleep: list[float]) -> None:
        client, api = client_with(
            error(503), retry=RetryPolicy(attempts=5, retry_unsafe_methods=True)
        )
        with client, pytest.raises(APIError):
            client.withdraw("JPY", 1234, 10_000)
        assert api.count == 1

    def test_not_retried_on_429_either(self, no_sleep: list[float]) -> None:
        client, api = client_with(
            httpx.Response(429, json={}), retry=RetryPolicy(attempts=5, retry_unsafe_methods=True)
        )
        with client, pytest.raises(RateLimitError):
            client.withdraw("JPY", 1234, 10_000)
        assert api.count == 1


class TestRetryPolicy:
    def test_rejects_nonsense_configuration(self) -> None:
        with pytest.raises(ValueError, match="attempts"):
            RetryPolicy(attempts=0)
        with pytest.raises(ValueError, match="backoff"):
            RetryPolicy(backoff=-1)

    def test_delay_grows_and_is_capped(self) -> None:
        policy = RetryPolicy(backoff=1.0, max_backoff=4.0)
        # Full jitter on the upper half: attempt N sits in [base/2, base].
        assert 0.5 <= policy.delay(1) <= 1.0
        assert 1.0 <= policy.delay(2) <= 2.0
        assert 2.0 <= policy.delay(3) <= 4.0
        assert all(policy.delay(9) <= 4.0 for _ in range(20))

    def test_delay_honours_retry_after(self) -> None:
        policy = RetryPolicy(max_backoff=30.0)
        assert policy.delay(1, retry_after=5.0) == 5.0

    def test_retry_after_is_still_capped(self) -> None:
        """bitFlyer can report a 297-second window; do not block that long."""
        policy = RetryPolicy(max_backoff=30.0)
        assert policy.delay(1, retry_after=297.0) == 30.0

    def test_negative_retry_after_is_clamped(self) -> None:
        assert RetryPolicy().delay(1, retry_after=-5.0) == 0.0

    @pytest.mark.parametrize(
        ("method", "status", "expected"),
        [
            ("GET", 500, True),
            ("GET", 400, False),
            ("GET", None, True),
            ("POST", 500, False),
            ("POST", None, False),
            ("POST", 429, True),
            ("GET", 429, True),
        ],
    )
    def test_should_retry(self, method: str, status: int | None, expected: bool) -> None:
        assert RetryPolicy().should_retry(method, status) is expected
