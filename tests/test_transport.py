"""Signing and response decoding.

The signing tests are the important ones: nothing else in the suite would catch
a change that makes every Private call fail with a signature mismatch.
"""

import hashlib
import hmac
import json

import httpx
import pytest

from pylightningfx import APIError, CredentialsError, RateLimitError, RateLimitState
from pylightningfx._transport import (
    NEVER_RETRY_PATHS,
    ORDER_PATHS,
    build_error,
    decode_response,
    prepare_request,
    retry_after,
)

from .conftest import FAKE_KEY, FAKE_SECRET, empty, error, ok, sync_client

FROZEN_TIME = 1_700_000_000


@pytest.fixture
def frozen_clock(monkeypatch: pytest.MonkeyPatch) -> int:
    """Pin the signing timestamp so signatures are reproducible."""
    monkeypatch.setattr("pylightningfx._transport.time.time", lambda: FROZEN_TIME)
    return FROZEN_TIME


def expected_sign(message: bytes) -> str:
    return hmac.new(FAKE_SECRET.encode(), message, hashlib.sha256).hexdigest()


def sign_of(request: httpx.Request) -> str:
    return request.headers["ACCESS-SIGN"]


class TestSigning:
    def test_get_signature_covers_timestamp_method_and_path(self, frozen_clock: int) -> None:
        client = httpx.Client(base_url="https://api.bitflyer.com")
        request = prepare_request(
            client,
            "GET",
            "/v1/me/getbalance",
            private=True,
            api_key=FAKE_KEY,
            api_secret=FAKE_SECRET,
        )
        assert request.headers["ACCESS-KEY"] == FAKE_KEY
        assert request.headers["ACCESS-TIMESTAMP"] == str(FROZEN_TIME)
        assert sign_of(request) == expected_sign(f"{FROZEN_TIME}GET/v1/me/getbalance".encode())

    def test_query_string_is_part_of_the_signature(self, frozen_clock: int) -> None:
        """The signed path must include the query, exactly as sent."""
        client = httpx.Client(base_url="https://api.bitflyer.com")
        request = prepare_request(
            client,
            "GET",
            "/v1/me/getchildorders",
            params={"product_code": "BTC_JPY", "count": 5},
            private=True,
            api_key=FAKE_KEY,
            api_secret=FAKE_SECRET,
        )
        query = request.url.raw_path.decode()
        assert query == "/v1/me/getchildorders?product_code=BTC_JPY&count=5"
        assert sign_of(request) == expected_sign(f"{FROZEN_TIME}GET{query}".encode())

    def test_signature_matches_the_body_actually_sent(self, frozen_clock: int) -> None:
        """Signing a re-serialised body is the classic source of flaky 401s."""
        client = httpx.Client(base_url="https://api.bitflyer.com")
        body = {"product_code": "BTC_JPY", "size": 0.01}
        request = prepare_request(
            client,
            "POST",
            "/v1/me/sendchildorder",
            body=body,
            private=True,
            api_key=FAKE_KEY,
            api_secret=FAKE_SECRET,
        )
        sent = request.content
        assert sent == b'{"product_code":"BTC_JPY","size":0.01}'
        expected = f"{FROZEN_TIME}POST/v1/me/sendchildorder".encode() + sent
        assert sign_of(request) == expected_sign(expected)
        assert request.headers["Content-Type"] == "application/json"

    def test_public_requests_are_not_signed(self) -> None:
        client = httpx.Client(base_url="https://api.bitflyer.com")
        request = prepare_request(
            client, "GET", "/v1/getticker", params={"product_code": "BTC_JPY"}
        )
        assert "ACCESS-KEY" not in request.headers
        assert "ACCESS-SIGN" not in request.headers

    @pytest.mark.parametrize(("key", "secret"), [("", ""), (FAKE_KEY, ""), ("", FAKE_SECRET)])
    def test_missing_credentials_raise_before_sending(self, key: str, secret: str) -> None:
        client = httpx.Client(base_url="https://api.bitflyer.com")
        with pytest.raises(CredentialsError, match="Private API endpoint"):
            prepare_request(
                client, "GET", "/v1/me/getbalance", private=True, api_key=key, api_secret=secret
            )

    def test_signature_is_stable_across_equal_inputs(self, frozen_clock: int) -> None:
        client = httpx.Client(base_url="https://api.bitflyer.com")
        signs = {
            sign_of(
                prepare_request(
                    client,
                    "GET",
                    "/v1/me/getbalance",
                    private=True,
                    api_key=FAKE_KEY,
                    api_secret=FAKE_SECRET,
                )
            )
            for _ in range(3)
        }
        assert len(signs) == 1


class TestDecodeResponse:
    def test_empty_body_decodes_to_none(self) -> None:
        """The cancel endpoints answer 200 with zero bytes; .json() would raise."""
        assert decode_response(empty()) is None

    def test_json_body_decodes(self) -> None:
        assert decode_response(ok({"status": "NORMAL"})) == {"status": "NORMAL"}

    def test_error_status_raises_api_error(self) -> None:
        response = error(400, status=-100, message="Invalid product")
        response.request = httpx.Request("GET", "https://api.bitflyer.com/v1/getticker")
        with pytest.raises(APIError) as caught:
            decode_response(response)
        exc = caught.value
        assert exc.status_code == 400
        assert exc.status == -100
        assert exc.error_message == "Invalid product"
        assert "Invalid product" in str(exc)


class TestBuildError:
    def _with_request(self, response: httpx.Response) -> httpx.Response:
        response.request = httpx.Request("GET", "https://api.bitflyer.com/v1/getticker")
        return response

    def test_preserves_bitflyer_fields(self) -> None:
        exc = build_error(self._with_request(error(401, status=-500, message="Key not found")))
        assert (exc.status, exc.error_message) == (-500, "Key not found")
        assert exc.body

    def test_429_becomes_rate_limit_error(self) -> None:
        response = httpx.Response(429, json={"status": -1, "error_message": "slow down"})
        exc = build_error(self._with_request(response))
        assert isinstance(exc, RateLimitError)

    def test_aspnet_404_shape_is_understood(self) -> None:
        """Omitting a required query param misses the route and returns capital-M Message."""
        response = httpx.Response(404, json={"Message": "No HTTP resource was found"})
        exc = build_error(self._with_request(response))
        assert exc.error_message == "No HTTP resource was found"
        assert exc.status is None

    def test_non_json_body_does_not_break(self) -> None:
        """An unknown path returns an HTML error page, not JSON."""
        response = httpx.Response(404, text="<html>Not Found</html>")
        exc = build_error(self._with_request(response))
        assert exc.status is None
        assert exc.error_message is None
        assert "<html>" in exc.body


class TestRateLimitHeaders:
    def test_parses_headers(self) -> None:
        response = httpx.Response(
            200,
            json={},
            headers={
                "X-RateLimit-Remaining": "496",
                "X-RateLimit-Period": "297",
                "X-RateLimit-Reset": "1785507598",
            },
        )
        state = RateLimitState.from_response(response)
        assert state == RateLimitState(remaining=496, period=297, reset=1785507598)

    def test_absent_headers_give_none(self) -> None:
        assert RateLimitState.from_response(ok({})) is None

    def test_unparseable_header_is_ignored(self) -> None:
        response = httpx.Response(200, json={}, headers={"X-RateLimit-Remaining": "many"})
        assert RateLimitState.from_response(response) is None

    def test_client_exposes_the_latest_state(self) -> None:
        response = httpx.Response(
            200, json={"status": "NORMAL"}, headers={"X-RateLimit-Remaining": "12"}
        )
        client, _ = sync_client(response)
        with client:
            assert client.rate_limit is None
            client.get_health()
            assert client.rate_limit is not None
            assert client.rate_limit.remaining == 12

    def test_retry_after_prefers_header_then_window(self) -> None:
        assert retry_after(httpx.Response(429, headers={"Retry-After": "7"})) == 7.0
        assert retry_after(httpx.Response(429, headers={"X-RateLimit-Period": "42"})) == 42.0
        assert retry_after(httpx.Response(429)) is None

    def test_http_date_retry_after_falls_through(self) -> None:
        response = httpx.Response(429, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})
        assert retry_after(response) is None


class TestPathSets:
    def test_order_bucket_holds_only_the_three_metered_endpoints(self) -> None:
        """bitFlyer meters these three together; single-order cancels are not included."""
        assert {
            "/v1/me/sendchildorder",
            "/v1/me/sendparentorder",
            "/v1/me/cancelallchildorders",
        } == ORDER_PATHS
        assert "/v1/me/cancelchildorder" not in ORDER_PATHS
        assert "/v1/me/cancelparentorder" not in ORDER_PATHS

    def test_withdraw_is_never_retried(self) -> None:
        assert {"/v1/me/withdraw"} == NEVER_RETRY_PATHS


class TestUserAgent:
    def test_identifies_the_library(self) -> None:
        client, api = sync_client(ok({"status": "NORMAL"}))
        with client:
            client.get_health()
        assert api.request.headers["User-Agent"].startswith("pylightningfx/")

    def test_caller_headers_win(self) -> None:
        client, api = sync_client(ok({"status": "NORMAL"}), headers={"User-Agent": "mine/1.0"})
        with client:
            client.get_health()
        assert api.request.headers["User-Agent"] == "mine/1.0"


class TestBorrowedHttpClient:
    def test_is_not_closed_by_the_wrapper(self) -> None:
        """A pool the caller owns must outlive the client that borrowed it."""
        from pylightningfx import Client

        from .conftest import Recorder

        recorder = Recorder(ok({"status": "NORMAL"}))
        pool = httpx.Client(base_url="https://api.bitflyer.com", transport=recorder.transport)
        with Client(http_client=pool) as client:
            client.get_health()
        assert not pool.is_closed
        pool.close()

    def test_body_round_trips_through_a_borrowed_pool(self) -> None:
        from pylightningfx import Client

        from .conftest import Recorder

        recorder = Recorder(ok({"child_order_acceptance_id": "JRF1"}))
        pool = httpx.Client(base_url="https://api.bitflyer.com", transport=recorder.transport)
        with Client(FAKE_KEY, FAKE_SECRET, http_client=pool) as client:
            client.send_child_order("BTC_JPY", "MARKET", "BUY", 0.01)
        assert json.loads(recorder.request.content)["child_order_type"] == "MARKET"
        pool.close()
