"""The async client must be a faithful mirror of the sync one.

Rather than duplicating every endpoint test, these run a representative set of
calls through *both* clients and assert the two produced the same request and the
same parsed result, then check that neither surface has drifted from the other.
"""

import json
from collections.abc import Callable
from typing import Any, NamedTuple

import pytest
from pydantic import BaseModel

from pylightningfx import (
    AsyncClient,
    Balance,
    Board,
    ChildOrder,
    ChildOrderResponse,
    ChildOrderType,
    Client,
    Collateral,
    CredentialsError,
    Execution,
    FundingRateHistory,
    Health,
    Market,
    ParentOrderParameter,
    Position,
    ProductCode,
    Side,
    Ticker,
)

from .conftest import async_client, empty, ok, sync_client
from .test_private import (
    BALANCE,
    CHILD_ORDER_RESPONSE,
    CHILD_ORDERS,
    COLLATERAL,
    POSITIONS,
    SIGNED_HEADERS,
)
from .test_public import BOARD, EXECUTIONS, FUNDING_RATE_HISTORY, HEALTH, MARKETS, TICKER


class Case(NamedTuple):
    """One endpoint call, run identically through both clients."""

    name: str
    kwargs: dict[str, Any]
    payload: Any
    path: str
    params: dict[str, str]
    check: Callable[[Any], bool]
    authed: bool = False


CASES = [
    Case(
        "get_markets",
        {},
        MARKETS,
        "/v1/getmarkets",
        {},
        lambda r: isinstance(r[0], Market) and r[0].product_code == "BTC_JPY",
    ),
    Case(
        "get_board",
        {"product_code": ProductCode.FX_BTC_JPY},
        BOARD,
        "/v1/getboard",
        {"product_code": "FX_BTC_JPY"},
        lambda r: isinstance(r, Board) and r.mid_price == 33320.0,
    ),
    Case(
        "get_ticker",
        {},
        TICKER,
        "/v1/getticker",
        {"product_code": "BTC_JPY"},
        lambda r: isinstance(r, Ticker) and r.ltp == 31690.0,
    ),
    Case(
        "get_executions",
        {"count": 3},
        EXECUTIONS,
        "/v1/getexecutions",
        {"product_code": "BTC_JPY", "count": "3"},
        lambda r: isinstance(r[0], Execution) and r[0].id == 39287,
    ),
    Case(
        "get_health",
        {},
        HEALTH,
        "/v1/gethealth",
        {"product_code": "BTC_JPY"},
        lambda r: isinstance(r, Health) and r.status == "NORMAL",
    ),
    Case(
        "get_funding_rate_history",
        {"from_": "2024-01-01"},
        FUNDING_RATE_HISTORY,
        "/v1/getfundingratehistory",
        {"product_code": "FX_BTC_JPY", "from": "2024-01-01"},
        lambda r: isinstance(r[0], FundingRateHistory) and r[0].rate == 0.000123,
    ),
    Case(
        "get_balance",
        {},
        BALANCE,
        "/v1/me/getbalance",
        {},
        lambda r: isinstance(r[0], Balance) and r[0].currency_code == "JPY",
        authed=True,
    ),
    Case(
        "get_collateral",
        {},
        COLLATERAL,
        "/v1/me/getcollateral",
        {},
        lambda r: isinstance(r, Collateral) and r.keep_rate == 5.0,
        authed=True,
    ),
    Case(
        "get_child_orders",
        {"child_order_state": "ACTIVE"},
        CHILD_ORDERS,
        "/v1/me/getchildorders",
        {"product_code": "BTC_JPY", "child_order_state": "ACTIVE"},
        lambda r: isinstance(r[0], ChildOrder) and r[0].id == 138398,
        authed=True,
    ),
    Case(
        "get_positions",
        {},
        POSITIONS,
        "/v1/me/getpositions",
        {"product_code": "FX_BTC_JPY"},
        lambda r: isinstance(r[0], Position) and r[0].pnl == 965.0,
        authed=True,
    ),
    Case(
        "send_child_order",
        {
            "product_code": ProductCode.FX_BTC_JPY,
            "child_order_type": ChildOrderType.MARKET,
            "side": Side.BUY,
            "size": 0.01,
        },
        CHILD_ORDER_RESPONSE,
        "/v1/me/sendchildorder",
        {},
        lambda r: isinstance(r, ChildOrderResponse),
        authed=True,
    ),
]


def normalise(result: Any) -> Any:
    """Reduce a parsed result to something comparable across two clients."""
    if isinstance(result, BaseModel):
        return result.model_dump()
    if isinstance(result, list):
        return [normalise(item) for item in result]
    return result


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
async def test_async_mirrors_sync(case: Case) -> None:
    sync, sync_api = sync_client(ok(case.payload), authed=case.authed)
    with sync:
        expected = getattr(sync, case.name)(**case.kwargs)

    client, api = async_client(ok(case.payload), authed=case.authed)
    async with client:
        result = await getattr(client, case.name)(**case.kwargs)

    assert case.check(result)
    assert normalise(result) == normalise(expected)
    assert api.request.url.path == case.path
    assert dict(api.request.url.params) == case.params
    assert api.request.url.path == sync_api.request.url.path
    assert api.request.url.query == sync_api.request.url.query
    assert api.request.content == sync_api.request.content
    if case.authed:
        for header in SIGNED_HEADERS:
            assert header in api.request.headers
    else:
        assert "ACCESS-KEY" not in api.request.headers


ENDPOINT_PREFIXES = ("get_", "send_", "cancel_", "withdraw")


def test_async_client_exposes_the_same_endpoints():
    sync_names = {n for n in dir(Client) if not n.startswith("_")}
    async_names = {n for n in dir(AsyncClient) if not n.startswith("_")}

    endpoints = {n for n in sync_names if n.startswith(ENDPOINT_PREFIXES)}
    assert endpoints == {n for n in async_names if n.startswith(ENDPOINT_PREFIXES)}
    assert len(endpoints) == 34, "10 Public + 24 Private endpoints"

    # Everything else matches too, apart from the close/aclose naming.
    assert sync_names - async_names == {"close"}
    assert async_names - sync_names == {"aclose"}


ASYNC_CANCELS: list[tuple[str, Callable[[Any], Any]]] = [
    ("cancel_child_order", lambda c: c.cancel_child_order(child_order_id="JOR-1")),
    ("cancel_parent_order", lambda c: c.cancel_parent_order(parent_order_id="JCP-1")),
    ("cancel_all_child_orders", lambda c: c.cancel_all_child_orders()),
]


@pytest.mark.parametrize(("name", "call"), ASYNC_CANCELS, ids=[name for name, _ in ASYNC_CANCELS])
async def test_async_cancel_handles_empty_body(name: str, call: Callable[[Any], Any]) -> None:
    client, api = async_client(empty(), authed=True)
    async with client:
        assert await call(client) is None

    assert api.request.url.path.startswith("/v1/me/cancel")
    assert api.request.method == "POST"
    for header in SIGNED_HEADERS:
        assert header in api.request.headers


async def test_async_private_requires_credentials():
    client, api = async_client()
    async with client:
        with pytest.raises(CredentialsError):
            await client.get_balance()

    assert api.count == 0


async def test_async_send_parent_order_body_matches_sync():
    leg = ParentOrderParameter(
        product_code=ProductCode.FX_BTC_JPY,
        condition_type="STOP",
        side=Side.SELL,
        size=0.01,
        trigger_price=9_000_000,
    )
    sync, sync_api = sync_client(ok({"parent_order_acceptance_id": "JRF-1"}), authed=True)
    with sync:
        sync.send_parent_order([leg])

    client, api = async_client(ok({"parent_order_acceptance_id": "JRF-1"}), authed=True)
    async with client:
        result = await client.send_parent_order([leg])

    assert result.parent_order_acceptance_id == "JRF-1"
    assert api.request.content == sync_api.request.content
    body = json.loads(api.request.content)
    assert body["parameters"] == [
        {
            "product_code": "FX_BTC_JPY",
            "condition_type": "STOP",
            "side": "SELL",
            "size": 0.01,
            "trigger_price": 9_000_000,
        }
    ]
