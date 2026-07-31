"""Exceptions raised by pylightningfx."""

from typing import Any

import httpx

__all__ = [
    "APIError",
    "BitflyerError",
    "CredentialsError",
    "RateLimitError",
    "RealtimeError",
]


class BitflyerError(Exception):
    """Base class for every error raised by this library."""


class CredentialsError(BitflyerError):
    """A Private API call was attempted without an API key and secret."""


class APIError(BitflyerError):
    """The bitFlyer API returned an error response.

    Attributes:
        status_code: HTTP status code of the response.
        status: bitFlyer's numeric error code, or ``None`` if the body was not
            a bitFlyer error object.
        error_message: bitFlyer's human-readable message, or ``None``.
        data: The ``data`` field of the error body, or ``None``.
        body: The raw response body, decoded as text.
        request: The request that produced the error.
        response: The error response.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        status: int | None = None,
        error_message: str | None = None,
        data: Any = None,
        body: str = "",
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.status = status
        self.error_message = error_message
        self.data = data
        self.body = body
        self.request = request
        self.response = response


class RateLimitError(APIError):
    """The request was rejected because a rate limit was exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying, parsed from the
            ``Retry-After`` header, or ``None`` if the header was absent.
    """

    def __init__(self, *args: Any, retry_after: float | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after


class RealtimeError(BitflyerError):
    """The Realtime (WebSocket) API returned an error or the connection failed."""
