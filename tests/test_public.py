"""Endpoint coverage for :class:`~pylightningfx.PublicAPI`.

One test per method: the parsed model, the path that was hit, and the query
string that carried the arguments there.
"""

from pylightningfx import (
    Board,
    BoardState,
    Chat,
    CorporateLeverage,
    Execution,
    FundingRate,
    FundingRateHistory,
    Health,
    Market,
    ProductCode,
    Ticker,
)

from .conftest import ok, sync_client

MARKETS = [
    {"product_code": "BTC_JPY", "market_type": "Spot"},
    {"product_code": "FX_BTC_JPY", "market_type": "FX"},
]

BOARD = {
    "mid_price": 33320.0,
    "bids": [{"price": 30000.0, "size": 0.1}, {"price": 29000.0, "size": 1.5}],
    "asks": [{"price": 36640.0, "size": 5.0}],
}

TICKER = {
    "product_code": "BTC_JPY",
    "state": "RUNNING",
    "timestamp": "2015-07-08T02:50:59.97",
    "tick_id": 3579,
    "best_bid": 30000.0,
    "best_ask": 36640.0,
    "best_bid_size": 0.1,
    "best_ask_size": 5.0,
    "total_bid_depth": 15.13,
    "total_ask_depth": 20.0,
    "market_bid_size": 0.0,
    "market_ask_size": 0.0,
    "ltp": 31690.0,
    "volume": 16819.26,
    "volume_by_product": 6819.26,
}

EXECUTIONS = [
    {
        "id": 39287,
        "side": "BUY",
        "price": 31690.0,
        "size": 0.1,
        "exec_date": "2015-07-07T09:57:40.397",
        "buy_child_order_acceptance_id": "JRF20150707-095740-006668",
        "sell_child_order_acceptance_id": "JRF20150707-095740-006669",
    }
]

BOARD_STATE = {"health": "NORMAL", "state": "RUNNING"}

HEALTH = {"status": "NORMAL"}

FUNDING_RATE = {
    "current_funding_rate": 0.0001,
    "next_funding_rate_settledate": "2024-01-01T09:00:00",
}

FUNDING_RATE_HISTORY = [
    {
        "calculation_date": "2024-01-01T04:00:00",
        "settlement_date": "2024-01-01T09:00:00",
        "rate": 0.000123,
    }
]

CORPORATE_LEVERAGE = {
    "current_max": 2.0,
    "current_startdate": "2023-01-01T00:00:00",
    "next_max": 4.0,
    "next_startdate": "2024-01-01T00:00:00",
}

CHATS = [{"nickname": "Nanashi", "message": "Hello, bitFlyer!", "date": "2016-02-16T10:58:08.833"}]


def test_get_markets():
    client, api = sync_client(ok(MARKETS))
    with client:
        result = client.get_markets()

    assert isinstance(result, list)
    assert all(isinstance(m, Market) for m in result)
    assert result[1].product_code == "FX_BTC_JPY"
    assert result[1].market_type == "FX"
    assert api.request.url.path == "/v1/getmarkets"
    assert api.request.url.query == b""


def test_get_board():
    client, api = sync_client(ok(BOARD))
    with client:
        result = client.get_board(ProductCode.FX_BTC_JPY)

    assert isinstance(result, Board)
    assert result.mid_price == 33320.0
    assert result.bids[0].price == 30000.0
    assert api.request.url.path == "/v1/getboard"
    assert api.request.url.params["product_code"] == "FX_BTC_JPY"


def test_get_ticker():
    client, api = sync_client(ok(TICKER))
    with client:
        result = client.get_ticker()

    assert isinstance(result, Ticker)
    assert result.ltp == 31690.0
    assert result.tick_id == 3579
    assert api.request.url.path == "/v1/getticker"
    assert api.request.url.params["product_code"] == ProductCode.BTC_JPY


def test_get_executions():
    client, api = sync_client(ok(EXECUTIONS))
    with client:
        result = client.get_executions(ProductCode.BTC_JPY, count=5, before=100, after=1)

    assert isinstance(result, list)
    assert isinstance(result[0], Execution)
    assert result[0].id == 39287
    assert result[0].side == "BUY"
    assert api.request.url.path == "/v1/getexecutions"
    params = api.request.url.params
    assert params["product_code"] == "BTC_JPY"
    assert params["count"] == "5"
    assert params["before"] == "100"
    assert params["after"] == "1"


def test_get_board_state():
    client, api = sync_client(ok(BOARD_STATE))
    with client:
        result = client.get_board_state(ProductCode.ETH_JPY)

    assert isinstance(result, BoardState)
    assert result.health == "NORMAL"
    assert result.state == "RUNNING"
    assert api.request.url.path == "/v1/getboardstate"
    assert api.request.url.params["product_code"] == "ETH_JPY"


def test_get_health():
    client, api = sync_client(ok(HEALTH))
    with client:
        result = client.get_health(ProductCode.BTC_JPY)

    assert isinstance(result, Health)
    assert result.status == "NORMAL"
    assert api.request.url.path == "/v1/gethealth"
    assert api.request.url.params["product_code"] == "BTC_JPY"


def test_get_funding_rate():
    client, api = sync_client(ok(FUNDING_RATE))
    with client:
        result = client.get_funding_rate()

    assert isinstance(result, FundingRate)
    assert result.current_funding_rate == 0.0001
    assert result.next_funding_rate_settledate.year == 2024
    assert api.request.url.path == "/v1/getfundingrate"
    assert api.request.url.params["product_code"] == ProductCode.FX_BTC_JPY


def test_get_funding_rate_history():
    client, api = sync_client(ok(FUNDING_RATE_HISTORY))
    with client:
        result = client.get_funding_rate_history(count=10)

    assert isinstance(result, list)
    assert isinstance(result[0], FundingRateHistory)
    assert result[0].rate == 0.000123
    assert api.request.url.path == "/v1/getfundingratehistory"
    params = api.request.url.params
    assert params["product_code"] == "FX_BTC_JPY"
    assert params["count"] == "10"


def test_get_corporate_leverage():
    client, api = sync_client(ok(CORPORATE_LEVERAGE))
    with client:
        result = client.get_corporate_leverage()

    assert isinstance(result, CorporateLeverage)
    assert result.current_max == 2.0
    assert result.next_max == 4.0
    assert api.request.url.path == "/v1/getcorporateleverage"
    assert api.request.url.query == b""


def test_get_chats():
    client, api = sync_client(ok(CHATS))
    with client:
        result = client.get_chats(from_date="2016-02-16T00:00:00")

    assert isinstance(result, list)
    assert isinstance(result[0], Chat)
    assert result[0].nickname == "Nanashi"
    assert result[0].message == "Hello, bitFlyer!"
    assert api.request.url.path == "/v1/getchats"
    assert api.request.url.params["from_date"] == "2016-02-16T00:00:00"


# --- parameter naming and omission -------------------------------------------


def test_funding_rate_history_sends_from_without_trailing_underscore():
    """``from_`` is only a Python-keyword workaround; the wire name is ``from``."""
    client, api = sync_client(ok(FUNDING_RATE_HISTORY))
    with client:
        client.get_funding_rate_history(from_="2024-01-01")

    params = api.request.url.params
    assert params["from"] == "2024-01-01"
    assert "from_" not in params


def test_funding_rate_history_sends_both_date_bounds():
    client, api = sync_client(ok(FUNDING_RATE_HISTORY))
    with client:
        client.get_funding_rate_history(from_="2024-01-01", to="2024-01-31")

    params = api.request.url.params
    assert params["from"] == "2024-01-01"
    assert params["to"] == "2024-01-31"
    assert set(params.keys()) == {"product_code", "from", "to"}


def test_get_executions_omits_unset_pagination():
    client, api = sync_client(ok(EXECUTIONS))
    with client:
        client.get_executions()

    assert api.request.url.query == b"product_code=BTC_JPY"
    assert set(api.request.url.params.keys()) == {"product_code"}


def test_get_chats_omits_unset_from_date():
    client, api = sync_client(ok(CHATS))
    with client:
        client.get_chats()

    assert api.request.url.query == b""


# --- undocumented ticker fields ----------------------------------------------


def test_get_ticker_parses_null_undocumented_fields():
    payload = TICKER | {"preopen_end": None, "circuit_break_end": None}
    client, api = sync_client(ok(payload))
    with client:
        result = client.get_ticker()

    assert isinstance(result, Ticker)
    assert result.preopen_end is None
    assert result.circuit_break_end is None
    assert api.request.url.path == "/v1/getticker"


def test_get_ticker_parses_populated_undocumented_fields():
    payload = TICKER | {
        "state": "PREOPEN",
        "preopen_end": "2024-06-01T12:00:00",
        "circuit_break_end": "2024-06-01T12:05:30.5",
    }
    client, api = sync_client(ok(payload))
    with client:
        result = client.get_ticker()

    assert result.state == "PREOPEN"
    assert result.preopen_end is not None
    assert (result.preopen_end.year, result.preopen_end.hour) == (2024, 12)
    assert result.circuit_break_end is not None
    assert result.circuit_break_end.minute == 5
    assert api.request.url.path == "/v1/getticker"


def test_get_ticker_defaults_undocumented_fields_when_absent():
    client, _ = sync_client(ok(TICKER))
    with client:
        result = client.get_ticker()

    assert result.preopen_end is None
    assert result.circuit_break_end is None
