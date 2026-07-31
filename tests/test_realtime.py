"""Realtime API protocol handling, against a scripted fake socket."""

import hashlib
import hmac
import itertools
import json
from collections import deque
from typing import Any

import pytest
from websockets.exceptions import ConnectionClosedOK

from pylightningfx import (
    AsyncRealtimeClient,
    Board,
    ChildOrderEvent,
    CredentialsError,
    Execution,
    RealtimeClient,
    RealtimeError,
    RealtimeMessage,
    Ticker,
    channels,
)

from .conftest import FAKE_KEY, FAKE_SECRET

TICKER_PAYLOAD = {
    "product_code": "FX_BTC_JPY",
    "state": "RUNNING",
    "timestamp": "2026-07-31T14:00:00.1",
    "tick_id": 1,
    "best_bid": 5_000_000,
    "best_ask": 5_000_100,
    "best_bid_size": 0.1,
    "best_ask_size": 0.2,
    "total_bid_depth": 100.0,
    "total_ask_depth": 120.0,
    "market_bid_size": 0.0,
    "market_ask_size": 0.0,
    "ltp": 5_000_050,
    "volume": 12345.6,
    "volume_by_product": 234.5,
    "preopen_end": None,
    "circuit_break_end": None,
}

BOARD_PAYLOAD = {
    "mid_price": 5_000_050,
    "bids": [{"price": 5_000_000, "size": 0.1}],
    "asks": [{"price": 5_000_100, "size": 0.2}],
}

EXECUTIONS_PAYLOAD = [
    {
        "id": 1,
        "side": "BUY",
        "price": 5_000_000,
        "size": 0.01,
        "exec_date": "2026-07-31T14:00:00.1",
        "buy_child_order_acceptance_id": "JRF-B",
        "sell_child_order_acceptance_id": "JRF-S",
    }
]

CHILD_EVENT_PAYLOAD = [
    {
        "product_code": "FX_BTC_JPY",
        "child_order_id": "JOR-1",
        "child_order_acceptance_id": "JRF-1",
        "event_date": "2026-07-31T14:00:00.1",
        "event_type": "EXECUTION",
        "exec_id": 99,
        "side": "BUY",
        "price": 5_000_000,
        "size": 0.01,
        "commission": 0.0,
        "sfd": 0.0,
        "outstanding_size": 0.0,
    }
]


def channel_message(channel: str, message: Any) -> str:
    """A server push, in the exact envelope bitFlyer sends."""
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "channelMessage",
            "params": {"channel": channel, "message": message},
        }
    )


class FakeSocket:
    """A scripted stand-in for a ``websockets`` connection.

    Replies ``result: true`` to every request unless ``errors`` names the method.
    ``inject`` frames are delivered *before* the next reply, which is how a real
    server interleaves pushes with responses. Once everything queued is drained,
    ``recv`` raises as a closed connection would.
    """

    def __init__(
        self,
        *,
        stream: list[str] | None = None,
        errors: dict[str, dict[str, Any]] | None = None,
        results: dict[str, Any] | None = None,
        inject: list[str] | None = None,
    ) -> None:
        self.requests: list[dict[str, Any]] = []
        self.outbox: deque[str] = deque(stream or [])
        self.errors = errors or {}
        self.results = results or {}
        self.inject = deque(inject or [])
        self.closed = False

    def send(self, raw: str) -> None:
        request = json.loads(raw)
        self.requests.append(request)
        method = request["method"]
        while self.inject:
            self.outbox.appendleft(self.inject.popleft())
        if method in self.errors:
            reply: dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "error": self.errors[method],
            }
        else:
            reply = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": self.results.get(method, True),
            }
        # The reply lands behind anything already queued ahead of it.
        self.outbox.append(json.dumps(reply))

    def recv(self, *_: Any, **__: Any) -> str:
        if not self.outbox:
            raise ConnectionClosedOK(None, None)
        return self.outbox.popleft()

    def close(self) -> None:
        self.closed = True

    def sent_methods(self) -> list[str]:
        return [r["method"] for r in self.requests]

    def channels_subscribed(self) -> list[str]:
        return [r["params"]["channel"] for r in self.requests if r["method"] == "subscribe"]


class AsyncFakeSocket(FakeSocket):
    """The same script, with the coroutine surface the async client expects."""

    async def send(self, raw: str) -> None:  # type: ignore[override]
        super().send(raw)

    async def recv(self, *_: Any, **__: Any) -> str:  # type: ignore[override]
        return super().recv()

    async def close(self) -> None:  # type: ignore[override]
        self.closed = True


class SocketFactory:
    """Stands in for ``connect``, handing out scripted sockets in order.

    Call :meth:`enqueue` to script specific sockets; anything beyond what was
    queued gets a default one. Index it to inspect what was handed out.
    """

    def __init__(self, cls: type[FakeSocket] = FakeSocket) -> None:
        self._cls = cls
        self.created: list[FakeSocket] = []
        self.queue: deque[FakeSocket] = deque()

    def enqueue(self, *sockets: FakeSocket) -> None:
        self.queue.extend(sockets)

    def open(self) -> FakeSocket:
        socket = self.queue.popleft() if self.queue else self._cls()
        self.created.append(socket)
        return socket

    def __call__(self, url: str, **kwargs: Any) -> FakeSocket:
        return self.open()

    def __getitem__(self, index: int) -> FakeSocket:
        return self.created[index]

    def __len__(self) -> int:
        return len(self.created)


@pytest.fixture
def sockets(monkeypatch: pytest.MonkeyPatch) -> SocketFactory:
    """Patch the sync connector with a scriptable socket factory."""
    factory = SocketFactory()
    monkeypatch.setattr("pylightningfx.realtime.sync_connect", factory)
    return factory


class TestAuth:
    def test_signature_is_hmac_of_timestamp_then_nonce(
        self, sockets: SocketFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("pylightningfx.realtime.time.time", lambda: 1_700_000_000)
        monkeypatch.setattr("pylightningfx.realtime.secrets.token_hex", lambda n: "ab" * n)

        with RealtimeClient(FAKE_KEY, FAKE_SECRET) as rt:
            rt.connect()
            assert rt.authenticated

        params = sockets[0].requests[0]["params"]
        assert sockets[0].requests[0]["method"] == "auth"
        assert params["api_key"] == FAKE_KEY
        assert params["timestamp"] == 1_700_000_000
        nonce = params["nonce"]
        assert 16 <= len(nonce) <= 255
        expected = hmac.new(
            FAKE_SECRET.encode(), f"1700000000{nonce}".encode(), hashlib.sha256
        ).hexdigest()
        assert params["signature"] == expected

    def test_no_auth_without_credentials(self, sockets: SocketFactory) -> None:
        with RealtimeClient() as rt:
            rt.connect()
            assert not rt.authenticated
        assert sockets[0].sent_methods() == []

    def test_auth_error_is_raised(self, sockets: SocketFactory) -> None:
        sockets.enqueue(
            FakeSocket(errors={"auth": {"code": -32602, "message": "Invalid Timestamp"}})
        )
        with RealtimeClient(FAKE_KEY, FAKE_SECRET) as rt, pytest.raises(RealtimeError) as caught:
            rt.connect()
        assert "Invalid Timestamp" in str(caught.value)

    def test_auth_returning_non_true_is_an_error(self, sockets: SocketFactory) -> None:
        sockets.enqueue(FakeSocket(results={"auth": False}))
        with RealtimeClient(FAKE_KEY, FAKE_SECRET) as rt, pytest.raises(RealtimeError):
            rt.connect()


class TestSubscribe:
    def test_public_channel_needs_no_credentials(self, sockets: SocketFactory) -> None:
        with RealtimeClient() as rt:
            rt.subscribe(channels.ticker("FX_BTC_JPY"))
            assert rt.subscriptions == ("lightning_ticker_FX_BTC_JPY",)
        assert sockets[0].channels_subscribed() == ["lightning_ticker_FX_BTC_JPY"]

    def test_subscribing_connects_on_demand(self, sockets: SocketFactory) -> None:
        with RealtimeClient() as rt:
            rt.subscribe(channels.board("BTC_JPY"))
        assert len(sockets) == 1

    def test_invalid_channel_raises_instead_of_going_quiet(self, sockets: SocketFactory) -> None:
        """The server answers an unknown prefix with an error; surface it."""
        sockets.enqueue(
            FakeSocket(errors={"subscribe": {"code": -32602, "message": "invalid channel"}})
        )
        with RealtimeClient() as rt, pytest.raises(RealtimeError, match="invalid channel"):
            rt.subscribe("lightning_nonsense_BTC_JPY")

    def test_private_channel_without_credentials_fails_fast(self, sockets: SocketFactory) -> None:
        """Refuse locally rather than let the server answer 'authentication required'."""
        with RealtimeClient() as rt, pytest.raises(RealtimeError, match="requires authentication"):
            rt.subscribe(channels.CHILD_ORDER_EVENTS)

    def test_private_channel_after_auth(self, sockets: SocketFactory) -> None:
        with RealtimeClient(FAKE_KEY, FAKE_SECRET) as rt:
            rt.subscribe(channels.CHILD_ORDER_EVENTS)
        assert sockets[0].sent_methods() == ["auth", "subscribe"]

    def test_auth_precedes_any_private_subscribe(self, sockets: SocketFactory) -> None:
        with RealtimeClient(FAKE_KEY, FAKE_SECRET) as rt:
            rt.subscribe(channels.ticker("BTC_JPY"), channels.CHILD_ORDER_EVENTS)
        assert sockets[0].sent_methods()[0] == "auth"

    def test_multiple_channels_get_distinct_ids(self, sockets: SocketFactory) -> None:
        with RealtimeClient() as rt:
            rt.subscribe(channels.ticker("BTC_JPY"), channels.board("BTC_JPY"))
        ids = [r["id"] for r in sockets[0].requests]
        assert len(set(ids)) == len(ids)

    def test_unsubscribe_drops_the_channel(self, sockets: SocketFactory) -> None:
        with RealtimeClient() as rt:
            rt.subscribe(channels.ticker("BTC_JPY"))
            rt.unsubscribe(channels.ticker("BTC_JPY"))
            assert rt.subscriptions == ()
        assert sockets[0].sent_methods() == ["subscribe", "unsubscribe"]

    def test_channel_helpers_build_documented_names(self) -> None:
        assert channels.board_snapshot("BTC_JPY") == "lightning_board_snapshot_BTC_JPY"
        assert channels.board("FX_BTC_JPY") == "lightning_board_FX_BTC_JPY"
        assert channels.ticker("ETH_BTC") == "lightning_ticker_ETH_BTC"
        assert channels.executions("BTC_JPY") == "lightning_executions_BTC_JPY"
        assert {"child_order_events", "parent_order_events"} == channels.PRIVATE_CHANNELS


class TestMessageParsing:
    def _one(self, sockets: SocketFactory, channel: str, payload: Any) -> RealtimeMessage:
        sockets.enqueue(FakeSocket(stream=[channel_message(channel, payload)]))
        with RealtimeClient(reconnect=False) as rt:
            return next(iter(rt.listen()))

    def test_ticker_becomes_a_ticker_model(self, sockets: SocketFactory) -> None:
        message = self._one(sockets, "lightning_ticker_FX_BTC_JPY", TICKER_PAYLOAD)
        assert isinstance(message.data, Ticker)
        assert message.data.ltp == 5_000_050
        assert message.channel == "lightning_ticker_FX_BTC_JPY"
        assert message.raw == TICKER_PAYLOAD

    def test_board_snapshot_becomes_a_board(self, sockets: SocketFactory) -> None:
        message = self._one(sockets, "lightning_board_snapshot_BTC_JPY", BOARD_PAYLOAD)
        assert isinstance(message.data, Board)
        assert message.data.bids[0].price == 5_000_000

    def test_board_diff_becomes_a_board(self, sockets: SocketFactory) -> None:
        message = self._one(sockets, "lightning_board_FX_BTC_JPY", BOARD_PAYLOAD)
        assert isinstance(message.data, Board)

    def test_executions_become_a_list(self, sockets: SocketFactory) -> None:
        message = self._one(sockets, "lightning_executions_BTC_JPY", EXECUTIONS_PAYLOAD)
        assert isinstance(message.data, list)
        assert isinstance(message.data[0], Execution)

    def test_auction_execution_with_empty_side_parses(self, sockets: SocketFactory) -> None:
        """Opening-auction trades have no taker, so side is an empty string."""
        payload = [{**EXECUTIONS_PAYLOAD[0], "side": ""}]
        message = self._one(sockets, "lightning_executions_BTC_JPY", payload)
        assert message.data[0].side == ""

    def test_child_order_events_become_models(self, sockets: SocketFactory) -> None:
        sockets.enqueue(
            FakeSocket(stream=[channel_message("child_order_events", CHILD_EVENT_PAYLOAD)]),
        )
        with RealtimeClient(FAKE_KEY, FAKE_SECRET, reconnect=False) as rt:
            message = next(iter(rt.listen()))
        assert isinstance(message.data[0], ChildOrderEvent)
        assert message.data[0].event_type == "EXECUTION"
        assert message.data[0].exec_id == 99

    def test_unknown_channel_passes_through_raw(self, sockets: SocketFactory) -> None:
        message = self._one(sockets, "lightning_future_thing_BTC_JPY", {"anything": 1})
        assert message.data == {"anything": 1}

    def test_non_channel_frames_are_skipped(self, sockets: SocketFactory) -> None:
        """A late response to an earlier request must not surface as a message."""
        sockets.enqueue(
            FakeSocket(
                stream=[
                    json.dumps({"jsonrpc": "2.0", "id": 99, "result": True}),
                    channel_message("lightning_ticker_BTC_JPY", TICKER_PAYLOAD),
                ]
            ),
        )
        with RealtimeClient(reconnect=False) as rt:
            messages = list(itertools.islice(rt.listen(), 1))
        assert len(messages) == 1
        assert isinstance(messages[0].data, Ticker)


class TestPushesDuringHandshake:
    def test_messages_arriving_mid_subscribe_are_not_lost(self, sockets: SocketFactory) -> None:
        """Subscribing to a second channel must not drop data from the first."""
        pushed = channel_message("lightning_ticker_BTC_JPY", TICKER_PAYLOAD)
        sockets.enqueue(FakeSocket(inject=[pushed]))
        with RealtimeClient(reconnect=False) as rt:
            rt.subscribe(channels.ticker("BTC_JPY"))
            messages = list(itertools.islice(rt.listen(), 1))
        assert len(messages) == 1
        assert isinstance(messages[0].data, Ticker)


class TestReconnect:
    def test_resubscribes_everything_after_a_drop(
        self, sockets: SocketFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("pylightningfx.realtime.time.sleep", lambda _: None)
        first = FakeSocket()  # drops as soon as listen() reads
        second = FakeSocket(stream=[channel_message("lightning_ticker_BTC_JPY", TICKER_PAYLOAD)])
        sockets.enqueue(first, second)

        with RealtimeClient(reconnect=True) as rt:
            rt.subscribe(channels.ticker("BTC_JPY"), channels.board("BTC_JPY"))
            messages = list(itertools.islice(rt.listen(), 1))

        assert len(messages) == 1
        assert second.channels_subscribed() == [
            "lightning_ticker_BTC_JPY",
            "lightning_board_BTC_JPY",
        ]
        assert rt.subscriptions == ("lightning_ticker_BTC_JPY", "lightning_board_BTC_JPY")

    def test_reauthenticates_after_a_drop(
        self, sockets: SocketFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("pylightningfx.realtime.time.sleep", lambda _: None)
        second = FakeSocket(stream=[channel_message("child_order_events", CHILD_EVENT_PAYLOAD)])
        sockets.enqueue(FakeSocket(), second)

        with RealtimeClient(FAKE_KEY, FAKE_SECRET, reconnect=True) as rt:
            rt.subscribe(channels.CHILD_ORDER_EVENTS)
            list(itertools.islice(rt.listen(), 1))

        assert second.sent_methods() == ["auth", "subscribe"]

    def test_disabled_reconnect_propagates_the_close(self, sockets: SocketFactory) -> None:
        with RealtimeClient(reconnect=False) as rt, pytest.raises(ConnectionClosedOK):
            list(rt.listen())

    def test_gives_up_after_the_attempt_cap(
        self, sockets: SocketFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("pylightningfx.realtime.time.sleep", lambda _: None)

        def always_fail(url: str, **kwargs: Any) -> FakeSocket:
            raise OSError("connection refused")

        with RealtimeClient(reconnect=True, max_reconnect_attempts=2) as rt:
            rt.subscribe(channels.ticker("BTC_JPY"))
            monkeypatch.setattr("pylightningfx.realtime.sync_connect", always_fail)
            with pytest.raises(RealtimeError, match="giving up"):
                list(rt.listen())

    def test_backoff_grows_and_is_capped(self) -> None:
        rt = RealtimeClient(reconnect_backoff=1.0, max_reconnect_backoff=8.0)
        assert 0.5 <= rt._backoff(1) <= 1.0
        assert 2.0 <= rt._backoff(3) <= 4.0
        assert all(rt._backoff(20) <= 8.0 for _ in range(20))


class TestLifecycle:
    def test_close_is_idempotent(self, sockets: SocketFactory) -> None:
        rt = RealtimeClient()
        rt.connect()
        rt.close()
        rt.close()
        assert sockets[0].closed

    def test_context_manager_closes(self, sockets: SocketFactory) -> None:
        with RealtimeClient() as rt:
            rt.connect()
        assert sockets[0].closed

    def test_reconnecting_closes_the_old_socket(self, sockets: SocketFactory) -> None:
        rt = RealtimeClient()
        rt.connect()
        rt.connect()
        assert sockets[0].closed
        rt.close()

    def test_auth_request_without_credentials_raises(self) -> None:
        with pytest.raises(CredentialsError):
            RealtimeClient()._auth_request(1)


class TestAsyncRealtime:
    @pytest.fixture
    def async_sockets(self, monkeypatch: pytest.MonkeyPatch) -> SocketFactory:
        factory = SocketFactory(AsyncFakeSocket)

        async def connect(url: str, **kwargs: Any) -> FakeSocket:
            return factory.open()

        monkeypatch.setattr("pylightningfx.realtime.async_connect", connect)
        return factory

    async def test_subscribe_and_receive(self, async_sockets: SocketFactory) -> None:
        async_sockets.enqueue(
            AsyncFakeSocket(stream=[channel_message("lightning_ticker_BTC_JPY", TICKER_PAYLOAD)])
        )
        async with AsyncRealtimeClient(reconnect=False) as rt:
            await rt.subscribe(channels.ticker("BTC_JPY"))
            async for message in rt.listen():
                assert isinstance(message.data, Ticker)
                break
        assert async_sockets[0].channels_subscribed() == ["lightning_ticker_BTC_JPY"]

    async def test_auth_then_private_channel(self, async_sockets: SocketFactory) -> None:
        async with AsyncRealtimeClient(FAKE_KEY, FAKE_SECRET) as rt:
            await rt.subscribe(channels.CHILD_ORDER_EVENTS)
            assert rt.authenticated
        assert async_sockets[0].sent_methods() == ["auth", "subscribe"]

    async def test_private_channel_without_credentials_fails_fast(
        self, async_sockets: SocketFactory
    ) -> None:
        async with AsyncRealtimeClient() as rt:
            with pytest.raises(RealtimeError, match="requires authentication"):
                await rt.subscribe(channels.CHILD_ORDER_EVENTS)

    async def test_invalid_channel_raises(self, async_sockets: SocketFactory) -> None:
        async_sockets.enqueue(
            AsyncFakeSocket(errors={"subscribe": {"code": -32602, "message": "invalid channel"}})
        )
        async with AsyncRealtimeClient() as rt:
            with pytest.raises(RealtimeError, match="invalid channel"):
                await rt.subscribe("lightning_nope_BTC_JPY")

    async def test_resubscribes_after_a_drop(
        self, async_sockets: SocketFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def no_sleep(_: float) -> None:
            return None

        monkeypatch.setattr("pylightningfx.realtime.asyncio.sleep", no_sleep)
        second = AsyncFakeSocket(
            stream=[channel_message("lightning_ticker_BTC_JPY", TICKER_PAYLOAD)]
        )
        async_sockets.enqueue(AsyncFakeSocket(), second)

        async with AsyncRealtimeClient(reconnect=True) as rt:
            await rt.subscribe(channels.ticker("BTC_JPY"))
            async for _ in rt.listen():
                break
        assert second.channels_subscribed() == ["lightning_ticker_BTC_JPY"]

    async def test_close_is_idempotent(self, async_sockets: SocketFactory) -> None:
        rt = AsyncRealtimeClient()
        await rt.connect()
        await rt.aclose()
        await rt.aclose()
        assert async_sockets[0].closed
