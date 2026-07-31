"""The Realtime (WebSocket JSON-RPC 2.0) API client.

bitFlyer streams market data and your own order events over a single WebSocket
connection. Subscribe to any number of channels on one connection; see
[`pylightningfx.channels`][pylightningfx.channels] for the names.
"""

import asyncio
import contextlib
import hashlib
import hmac
import itertools
import json
import random
import secrets
import time
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from typing import Any, Self

from websockets.asyncio.client import ClientConnection as AsyncConnection
from websockets.asyncio.client import connect as async_connect
from websockets.exceptions import ConnectionClosed, WebSocketException
from websockets.sync.client import ClientConnection as SyncConnection
from websockets.sync.client import connect as sync_connect

from . import channels as _channels
from ._transport import REALTIME_URL
from .errors import CredentialsError, RealtimeError
from .models.public import Board, Execution, Ticker
from .models.realtime import ChildOrderEvent, ParentOrderEvent

__all__ = ["AsyncRealtimeClient", "RealtimeClient", "RealtimeMessage"]

_BOARD_SNAPSHOT_PREFIX = "lightning_board_snapshot_"
_BOARD_PREFIX = "lightning_board_"
_TICKER_PREFIX = "lightning_ticker_"
_EXECUTIONS_PREFIX = "lightning_executions_"

_CHANNEL_MESSAGE = "channelMessage"


@dataclass(frozen=True, slots=True)
class RealtimeMessage:
    """One ``channelMessage`` pushed by the server.

    Attributes:
        channel: The channel it arrived on.
        data: The payload, parsed into the model for that channel — a
            [`Board`][pylightningfx.models.public.Board] for ``lightning_board*``, a
            [`Ticker`][pylightningfx.models.public.Ticker] for ``lightning_ticker_*``, a list of
            [`Execution`][pylightningfx.models.public.Execution] for ``lightning_executions_*``, and
            a list of [`ChildOrderEvent`][pylightningfx.models.realtime.ChildOrderEvent] or
            [`ParentOrderEvent`][pylightningfx.models.realtime.ParentOrderEvent] for the private
            channels. A
            channel this release does not know passes through as decoded JSON.
        raw: The decoded but unvalidated payload, for anything the models drop.
    """

    channel: str
    data: Any
    raw: Any


def _parse(channel: str, payload: Any) -> Any:
    """Validate a raw payload into the model registered for its channel."""
    if channel.startswith(_BOARD_SNAPSHOT_PREFIX) or channel.startswith(_BOARD_PREFIX):
        return Board.model_validate(payload)
    if channel.startswith(_TICKER_PREFIX):
        return Ticker.model_validate(payload)
    if channel.startswith(_EXECUTIONS_PREFIX):
        return [Execution.model_validate(e) for e in payload]
    if channel == _channels.CHILD_ORDER_EVENTS:
        return [ChildOrderEvent.model_validate(e) for e in payload]
    if channel == _channels.PARENT_ORDER_EVENTS:
        return [ParentOrderEvent.model_validate(e) for e in payload]
    return payload


def _to_message(frame: Any) -> RealtimeMessage | None:
    """Convert a decoded frame to a [`RealtimeMessage`][pylightningfx.RealtimeMessage], or ``None``
    if it is not one."""
    if not isinstance(frame, dict) or frame.get("method") != _CHANNEL_MESSAGE:
        return None
    params = frame.get("params")
    if not isinstance(params, dict):
        return None
    channel = params.get("channel")
    if not isinstance(channel, str):
        return None
    payload = params.get("message")
    return RealtimeMessage(channel=channel, data=_parse(channel, payload), raw=payload)


class _RealtimeBase:
    """Protocol state shared by the sync and async Realtime clients."""

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        *,
        url: str = REALTIME_URL,
        reconnect: bool = True,
        max_reconnect_attempts: int | None = None,
        reconnect_backoff: float = 1.0,
        max_reconnect_backoff: float = 60.0,
        open_timeout: float | None = 10.0,
        ping_interval: float | None = 20.0,
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._url = url
        self._reconnect = reconnect
        self._max_reconnect_attempts = max_reconnect_attempts
        self._reconnect_backoff = reconnect_backoff
        self._max_reconnect_backoff = max_reconnect_backoff
        self._open_timeout = open_timeout
        self._ping_interval = ping_interval
        self._ids = itertools.count(1)
        self._buffer: list[Any] = []
        self._subscribed: dict[str, None] = {}
        self._authenticated = False

    @property
    def authenticated(self) -> bool:
        """Whether the ``auth`` handshake has completed on the live connection."""
        return self._authenticated

    @property
    def subscriptions(self) -> tuple[str, ...]:
        """Channels currently subscribed, in the order they were requested.

        These are replayed automatically after a reconnect.
        """
        return tuple(self._subscribed)

    def _auth_request(self, request_id: int) -> dict[str, Any]:
        """Build the ``auth`` request.

        The signature is HMAC-SHA256 over ``str(timestamp) + nonce``, hex encoded.
        Note this is a different message from the HTTP API's ``ACCESS-SIGN``,
        which also covers the method, path and body.
        """
        if not self._api_key or not self._api_secret:
            raise CredentialsError(
                "the Realtime API needs api_key and api_secret to authenticate; "
                "public channels work without them"
            )
        timestamp = int(time.time())
        nonce = secrets.token_hex(16)
        signature = hmac.new(
            self._api_secret.encode(), f"{timestamp}{nonce}".encode(), hashlib.sha256
        ).hexdigest()
        return {
            "jsonrpc": "2.0",
            "method": "auth",
            "id": request_id,
            "params": {
                "api_key": self._api_key,
                "timestamp": timestamp,
                "nonce": nonce,
                "signature": signature,
            },
        }

    @staticmethod
    def _subscribe_request(method: str, channel: str, request_id: int) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id,
            "params": {"channel": channel},
        }

    def _match(self, frame: Any, request_id: int) -> tuple[bool, Any]:
        """Test a frame against a pending request id.

        Returns ``(matched, result)``. Raises if the frame is that request's
        error response.
        """
        if not isinstance(frame, dict) or frame.get("id") != request_id:
            return False, None
        error = frame.get("error")
        if error is not None:
            if isinstance(error, dict):
                raise RealtimeError(f"JSON-RPC error {error.get('code')}: {error.get('message')}")
            raise RealtimeError(f"JSON-RPC error: {error}")
        return True, frame.get("result")

    def _check_private(self, channel: str) -> None:
        if channel in _channels.PRIVATE_CHANNELS and not self._authenticated:
            raise RealtimeError(
                f"{channel} requires authentication; construct the client with "
                "api_key and api_secret"
            )

    def _record(self, method: str, channel: str, result: Any) -> None:
        if result is not True:
            raise RealtimeError(f"{method} {channel} returned {result!r} instead of true")
        if method == "subscribe":
            self._subscribed[channel] = None
        else:
            self._subscribed.pop(channel, None)

    def _backoff(self, attempt: int) -> float:
        """Reconnect delay for a 1-based attempt, exponential with jitter."""
        capped = min(self._reconnect_backoff * 2.0 ** (attempt - 1), self._max_reconnect_backoff)
        return capped * (0.5 + random.random() / 2.0)

    def _giving_up(self, attempt: int) -> bool:
        return self._max_reconnect_attempts is not None and attempt > self._max_reconnect_attempts


class RealtimeClient(_RealtimeBase):
    """Synchronous Realtime API client.

    Iterate `listen()` to consume messages. Subscribing connects on demand,
    so the shortest useful program is::

        with RealtimeClient() as rt:
            rt.subscribe(channels.ticker(ProductCode.FX_BTC_JPY))
            for message in rt.listen():
                print(message.data.ltp)

    Private channels need credentials, and the client waits for the ``auth``
    response before it will subscribe to them::

        with RealtimeClient(api_key, api_secret) as rt:
            rt.subscribe(channels.CHILD_ORDER_EVENTS)
            for message in rt.listen():
                for event in message.data:
                    print(event.event_type, event.child_order_acceptance_id)

    Args:
        api_key: API key. Needed only for the private channels, and the key must
            carry the "receive order events" permission.
        api_secret: API secret.
        url: WebSocket endpoint. Override to point at a fake server.
        reconnect: Reconnect and replay `subscriptions` when the
            connection drops mid-`listen()`. With this off, a drop raises
            `websockets.exceptions.ConnectionClosed`.
        max_reconnect_attempts: Give up after this many consecutive failed
            reconnects, raising [`RealtimeError`][pylightningfx.RealtimeError]. ``None``
            retries forever, which is usually what a long-running bot wants.
        reconnect_backoff: Base reconnect delay in seconds; doubles each attempt.
        max_reconnect_backoff: Ceiling for a single reconnect delay.
        open_timeout: Seconds to wait for the handshake.
        ping_interval: Keepalive ping interval, passed to ``websockets``.
            ``None`` disables keepalive.

    A dropped connection loses order events that fired while it was down; the
    stream has no replay. After a reconnect, reconcile with
    ``get_child_orders`` rather than assuming continuity.
    """

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        *,
        url: str = REALTIME_URL,
        reconnect: bool = True,
        max_reconnect_attempts: int | None = None,
        reconnect_backoff: float = 1.0,
        max_reconnect_backoff: float = 60.0,
        open_timeout: float | None = 10.0,
        ping_interval: float | None = 20.0,
    ) -> None:
        super().__init__(
            api_key,
            api_secret,
            url=url,
            reconnect=reconnect,
            max_reconnect_attempts=max_reconnect_attempts,
            reconnect_backoff=reconnect_backoff,
            max_reconnect_backoff=max_reconnect_backoff,
            open_timeout=open_timeout,
            ping_interval=ping_interval,
        )
        self._ws: SyncConnection | None = None

    def connect(self) -> None:
        """Open the connection, authenticating when credentials were supplied.

        Called for you by `subscribe()` and `listen()`.
        """
        self.close()
        self._ws = sync_connect(
            self._url, open_timeout=self._open_timeout, ping_interval=self._ping_interval
        )
        self._authenticated = False
        if self._api_key and self._api_secret:
            self._authenticate()

    def close(self) -> None:
        """Close the connection if one is open. Safe to call repeatedly."""
        ws, self._ws = self._ws, None
        self._authenticated = False
        if ws is not None:
            with contextlib.suppress(OSError, WebSocketException):
                ws.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def subscribe(self, *channels: str) -> None:
        """Subscribe to one or more channels, connecting first if needed.

        Raises:
            RealtimeError: If the server rejects a channel, or a private channel
                is requested without authentication.
        """
        self._each("subscribe", channels)

    def unsubscribe(self, *channels: str) -> None:
        """Stop receiving messages from one or more channels."""
        self._each("unsubscribe", channels)

    def listen(self) -> Iterator[RealtimeMessage]:
        """Yield messages as they arrive, forever.

        Frames that are not channel messages, such as late responses to a
        subscribe, are skipped. When ``reconnect`` is on, a dropped connection is
        re-established and every channel in `subscriptions` resubscribed
        before iteration continues.
        """
        # Connect before the first drain: the handshake buffers any pushes that
        # arrive during it, and those must be yielded ahead of new frames.
        self._connection()
        while True:
            while self._buffer:
                message = _to_message(self._buffer.pop(0))
                if message is not None:
                    yield message
            try:
                frame = json.loads(self._connection().recv())
            except ConnectionClosed:
                if not self._reconnect:
                    raise
                self._reconnect_now()
                continue
            message = _to_message(frame)
            if message is not None:
                yield message

    def _connection(self) -> SyncConnection:
        if self._ws is None:
            self.connect()
        if self._ws is None:  # pragma: no cover - connect either sets it or raises
            raise RealtimeError("no connection")
        return self._ws

    def _authenticate(self) -> None:
        request_id = next(self._ids)
        result = self._call(self._auth_request(request_id), request_id)
        if result is not True:
            raise RealtimeError(f"auth returned {result!r} instead of true")
        self._authenticated = True

    def _each(self, method: str, names: tuple[str, ...]) -> None:
        # Connect (and so authenticate) first: the private-channel check below
        # reads a flag that only the auth handshake can set.
        self._connection()
        for channel in names:
            if method == "subscribe":
                self._check_private(channel)
            request_id = next(self._ids)
            result = self._call(self._subscribe_request(method, channel, request_id), request_id)
            self._record(method, channel, result)

    def _call(self, payload: dict[str, Any], request_id: int) -> Any:
        """Send a request and read until its response arrives.

        Channel messages that land while we wait are buffered, not dropped, so
        subscribing to a second channel cannot lose data from the first.
        """
        ws = self._connection()
        ws.send(json.dumps(payload))
        while True:
            frame = json.loads(ws.recv())
            matched, result = self._match(frame, request_id)
            if matched:
                return result
            self._buffer.append(frame)

    def _reconnect_now(self) -> None:
        wanted = tuple(self._subscribed)
        self._subscribed.clear()
        for attempt in itertools.count(1):
            if self._giving_up(attempt):
                raise RealtimeError(
                    f"giving up after {self._max_reconnect_attempts} reconnect attempts"
                )
            time.sleep(self._backoff(attempt))
            try:
                self.connect()
                if wanted:
                    self.subscribe(*wanted)
            except (OSError, WebSocketException, RealtimeError):
                continue
            return


class AsyncRealtimeClient(_RealtimeBase):
    """Asyncio Realtime API client.

    The same surface as [`RealtimeClient`][pylightningfx.RealtimeClient] with coroutines and an
    async
    iterator::

        async with AsyncRealtimeClient() as rt:
            await rt.subscribe(channels.executions(ProductCode.BTC_JPY))
            async for message in rt.listen():
                for trade in message.data:
                    print(trade.price, trade.size)

    Takes the same arguments as [`RealtimeClient`][pylightningfx.RealtimeClient]. One instance
    drives one
    connection, so drive it from a single task; run several instances if you want
    concurrent streams.
    """

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        *,
        url: str = REALTIME_URL,
        reconnect: bool = True,
        max_reconnect_attempts: int | None = None,
        reconnect_backoff: float = 1.0,
        max_reconnect_backoff: float = 60.0,
        open_timeout: float | None = 10.0,
        ping_interval: float | None = 20.0,
    ) -> None:
        super().__init__(
            api_key,
            api_secret,
            url=url,
            reconnect=reconnect,
            max_reconnect_attempts=max_reconnect_attempts,
            reconnect_backoff=reconnect_backoff,
            max_reconnect_backoff=max_reconnect_backoff,
            open_timeout=open_timeout,
            ping_interval=ping_interval,
        )
        self._ws: AsyncConnection | None = None

    async def connect(self) -> None:
        """Open the connection, authenticating when credentials were supplied."""
        await self.aclose()
        self._ws = await async_connect(
            self._url, open_timeout=self._open_timeout, ping_interval=self._ping_interval
        )
        self._authenticated = False
        if self._api_key and self._api_secret:
            await self._authenticate()

    async def aclose(self) -> None:
        """Close the connection if one is open. Safe to call repeatedly."""
        ws, self._ws = self._ws, None
        self._authenticated = False
        if ws is not None:
            with contextlib.suppress(OSError, WebSocketException):
                await ws.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def subscribe(self, *channels: str) -> None:
        """Subscribe to one or more channels, connecting first if needed."""
        await self._each("subscribe", channels)

    async def unsubscribe(self, *channels: str) -> None:
        """Stop receiving messages from one or more channels."""
        await self._each("unsubscribe", channels)

    async def listen(self) -> AsyncIterator[RealtimeMessage]:
        """Yield messages as they arrive, forever."""
        # Connect before the first drain: the handshake buffers any pushes that
        # arrive during it, and those must be yielded ahead of new frames.
        await self._connection()
        while True:
            while self._buffer:
                message = _to_message(self._buffer.pop(0))
                if message is not None:
                    yield message
            try:
                connection = await self._connection()
                frame = json.loads(await connection.recv())
            except ConnectionClosed:
                if not self._reconnect:
                    raise
                await self._reconnect_now()
                continue
            message = _to_message(frame)
            if message is not None:
                yield message

    async def _connection(self) -> AsyncConnection:
        if self._ws is None:
            await self.connect()
        if self._ws is None:  # pragma: no cover - connect either sets it or raises
            raise RealtimeError("no connection")
        return self._ws

    async def _authenticate(self) -> None:
        request_id = next(self._ids)
        result = await self._call(self._auth_request(request_id), request_id)
        if result is not True:
            raise RealtimeError(f"auth returned {result!r} instead of true")
        self._authenticated = True

    async def _each(self, method: str, names: tuple[str, ...]) -> None:
        # Connect (and so authenticate) first: the private-channel check below
        # reads a flag that only the auth handshake can set.
        await self._connection()
        for channel in names:
            if method == "subscribe":
                self._check_private(channel)
            request_id = next(self._ids)
            payload = self._subscribe_request(method, channel, request_id)
            self._record(method, channel, await self._call(payload, request_id))

    async def _call(self, payload: dict[str, Any], request_id: int) -> Any:
        """Send a request and read until its response arrives, buffering messages."""
        connection = await self._connection()
        await connection.send(json.dumps(payload))
        while True:
            frame = json.loads(await connection.recv())
            matched, result = self._match(frame, request_id)
            if matched:
                return result
            self._buffer.append(frame)

    async def _reconnect_now(self) -> None:
        wanted = tuple(self._subscribed)
        self._subscribed.clear()
        for attempt in itertools.count(1):
            if self._giving_up(attempt):
                raise RealtimeError(
                    f"giving up after {self._max_reconnect_attempts} reconnect attempts"
                )
            await asyncio.sleep(self._backoff(attempt))
            try:
                await self.connect()
                if wanted:
                    await self.subscribe(*wanted)
            except (OSError, WebSocketException, RealtimeError):
                continue
            return
