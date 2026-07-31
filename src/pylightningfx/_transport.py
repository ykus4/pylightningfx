"""Request signing and response decoding.

Deliberately free of I/O: the sync and async clients share every byte-level
decision made here, above all the exact string that gets signed.
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

import httpx

from ._version import __version__
from .errors import APIError, CredentialsError, RateLimitError

BASE_URL = "https://api.bitflyer.com"
REALTIME_URL = "wss://ws.lightstream.bitflyer.com/json-rpc"
DEFAULT_TIMEOUT = 10.0
DEFAULT_USER_AGENT = f"pylightningfx/{__version__}"

ORDER_PATHS = frozenset(
    {
        "/v1/me/sendchildorder",
        "/v1/me/sendparentorder",
        "/v1/me/cancelallchildorders",
    }
)
"""Endpoints sharing bitFlyer's separate, tighter order budget.

Exactly these three share one 300-per-5-minutes allowance. Note that
``cancelchildorder`` and ``cancelparentorder`` are *not* among them — cancelling
one order at a time counts only against the general limit.
"""

NEVER_RETRY_PATHS = frozenset({"/v1/me/withdraw"})
"""Endpoints never retried, regardless of [`RetryPolicy`][pylightningfx.RetryPolicy].

Moving cash off the exchange is irreversible and a timed-out withdrawal may
still have been accepted, so replaying one risks sending the money twice. There
is no upside to guess: re-check with ``get_withdrawals`` instead.
"""


@dataclass(frozen=True, slots=True)
class RateLimitState:
    """bitFlyer's own view of your rate limit, read from the response headers.

    Attributes:
        remaining: Requests left in the current window.
        period: Seconds left in the current window.
        reset: Unix timestamp at which the window resets.
    """

    remaining: int | None = None
    period: int | None = None
    reset: int | None = None

    @classmethod
    def from_response(cls, response: httpx.Response) -> "RateLimitState | None":
        """Parse the ``X-RateLimit-*`` headers, or ``None`` if absent."""
        state = cls(
            remaining=_header_int(response, "X-RateLimit-Remaining"),
            period=_header_int(response, "X-RateLimit-Period"),
            reset=_header_int(response, "X-RateLimit-Reset"),
        )
        if state.remaining is None and state.period is None and state.reset is None:
            return None
        return state


def _header_int(response: httpx.Response, name: str) -> int | None:
    raw = response.headers.get(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def prepare_request(
    client: httpx.Client | httpx.AsyncClient,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    private: bool = False,
    api_key: str = "",
    api_secret: str = "",
) -> httpx.Request:
    """Build a request, signing it when ``private`` is set.

    The signature covers the exact bytes that go on the wire. The body is
    serialised once here and handed to httpx as raw ``content``, and the path and
    query are read back off the built request rather than re-rendered. Signing a
    separately built copy of either is the classic source of intermittent
    ``Signature does not match`` errors, because ``json.dumps`` and httpx need
    not agree on spacing or percent-encoding.

    Raises:
        CredentialsError: If ``private`` is set but the key or secret is missing.
    """
    content = json.dumps(body, separators=(",", ":")).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if content is not None else {}
    request = client.build_request(method, path, params=params, content=content, headers=headers)

    if not private:
        return request

    if not api_key or not api_secret:
        raise CredentialsError(
            f"{method} {path} is a Private API endpoint; construct the client with "
            "api_key and api_secret."
        )

    timestamp = str(int(time.time()))
    message = timestamp.encode() + method.upper().encode() + request.url.raw_path + (content or b"")
    request.headers["ACCESS-KEY"] = api_key
    request.headers["ACCESS-TIMESTAMP"] = timestamp
    request.headers["ACCESS-SIGN"] = hmac.new(
        api_secret.encode(), message, hashlib.sha256
    ).hexdigest()
    return request


def decode_response(response: httpx.Response) -> Any:
    """Return the decoded body of a successful response, or raise.

    Yields ``None`` for a success with an empty body. The cancel endpoints answer
    ``200`` with zero bytes, and ``response.json()`` raises on that.

    Raises:
        RateLimitError: On HTTP 429.
        APIError: On any other non-2xx status.
    """
    if response.is_success:
        return response.json() if response.content else None
    raise build_error(response)


def build_error(response: httpx.Response) -> APIError:
    """Turn an error response into the matching exception.

    bitFlyer sends ``{"status": -100, "error_message": "...", "data": null}``
    alongside the HTTP status. Both are preserved on the exception; the numeric
    ``status`` is the one that actually identifies the failure.
    """
    payload: Any
    try:
        payload = response.json()
    except ValueError:
        payload = None  # an unknown path answers 404 with an HTML page

    status: int | None = None
    error_message: str | None = None
    data: Any = None
    if isinstance(payload, dict):
        if isinstance(payload.get("status"), int):
            status = payload["status"]
        if isinstance(payload.get("error_message"), str):
            error_message = payload["error_message"]
        elif isinstance(payload.get("Message"), str):
            # Omitting a required query parameter misses the route entirely and
            # comes back as a bare ASP.NET 404 with a capitalised "Message".
            error_message = payload["Message"]
        data = payload.get("data")

    detail = error_message or response.reason_phrase or "unknown error"
    label = f"HTTP {response.status_code}"
    if status is not None:
        label += f" status={status}"
    message = f"{label}: {detail} ({response.request.method} {response.request.url.path})"

    kwargs: dict[str, Any] = {
        "status_code": response.status_code,
        "status": status,
        "error_message": error_message,
        "data": data,
        "body": response.text,
        "request": response.request,
        "response": response,
    }
    if response.status_code == 429:
        return RateLimitError(message, retry_after=retry_after(response), **kwargs)
    return APIError(message, **kwargs)


def retry_after(response: httpx.Response) -> float | None:
    """Seconds the server wants us to wait, or ``None`` if it did not say.

    Prefers ``Retry-After``, falling back to how much of the rate limit window
    is left. Only the delta-seconds form of ``Retry-After`` is understood; the
    HTTP-date form falls through to the window.
    """
    raw = response.headers.get("Retry-After")
    if raw is not None:
        try:
            return float(raw)
        except ValueError:
            pass
    state = RateLimitState.from_response(response)
    if state is not None and state.period is not None:
        return float(state.period)
    return None
