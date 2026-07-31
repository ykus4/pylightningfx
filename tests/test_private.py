"""Endpoint coverage for :class:`~pylightningfx.PrivateAPI`.

One test per method, each checking the parsed model, the path, and that the
request was signed. The extra tests at the bottom pin down the empty-body cancel
responses, the request bodies of the two order endpoints, and the missing
credentials guard.
"""

import json
from collections.abc import Callable
from typing import Any

import pytest

from pylightningfx import (
    Address,
    Balance,
    BalanceHistory,
    BankAccount,
    ChildOrder,
    ChildOrderResponse,
    ChildOrderType,
    CoinIn,
    CoinOut,
    Collateral,
    CollateralAccount,
    CollateralHistory,
    ConditionType,
    CredentialsError,
    Deposit,
    MyExecution,
    OrderMethod,
    ParentOrder,
    ParentOrderDetail,
    ParentOrderParameter,
    ParentOrderResponse,
    Position,
    ProductCode,
    Side,
    TradingCommission,
    Withdrawal,
    WithdrawResponse,
)

from .conftest import empty, ok, sync_client

SIGNED_HEADERS = ("ACCESS-KEY", "ACCESS-TIMESTAMP", "ACCESS-SIGN")

PERMISSIONS = ["/v1/me/getpermissions", "/v1/me/getbalance", "/v1/me/sendchildorder"]

BALANCE = [
    {"currency_code": "JPY", "amount": 1024078.0, "available": 508000.0},
    {"currency_code": "BTC", "amount": 10.24, "available": 4.12},
]

COLLATERAL = {
    "collateral": 100000.0,
    "open_position_pnl": -715.0,
    "require_collateral": 19857.0,
    "keep_rate": 5.0,
    "margin_call_amount": 0.0,
    "margin_call_due_date": None,
}

COLLATERAL_ACCOUNTS = [
    {"currency_code": "JPY", "amount": 10000.0},
    {"currency_code": "BTC", "amount": 1.5},
]

ADDRESSES = [
    {"type": "NORMAL", "currency_code": "BTC", "address": "3AYrDq8zfhr1SYgWKAG9bUQvbGjXhF3Zcy"}
]

COIN_INS = [
    {
        "id": 100,
        "order_id": "CDP20151227-024141-055555",
        "currency_code": "BTC",
        "amount": 0.1,
        "address": "1G5aTLNP94rMYFmYm1BqmQAmDBGKY2b1Nb",
        "tx_hash": "9f92ee65a176bb9545f7becb8706c50d07d4cee5ffca34d8be3ef11d411405ae",
        "status": "COMPLETED",
        "event_date": "2015-11-27T08:59:20.301",
    }
]

COIN_OUTS = [
    {
        "id": 500,
        "order_id": "CWD20151224-014040-077777",
        "currency_code": "BTC",
        "amount": 0.03,
        "address": "1WriteySQufKZ2pVuM1oMhPrTtTVFq35j",
        "tx_hash": "fbc6f5f9b2b3fc4a5e1c1c9c1d6d38e0e34c66ba6b1a3f9f9b7f7c8b7fbb3d6c",
        "fee": 0.0005,
        "additional_fee": 0.0002,
        "status": "COMPLETED",
        "event_date": "2015-12-24T01:39:41.013",
    }
]

BANK_ACCOUNTS = [
    {
        "id": 3402,
        "is_verified": True,
        "bank_name": "three sacred treasures bank",
        "branch_name": "aoyama",
        "account_type": "toza",
        "account_number": "0123456",
        "account_name": "TARO YAMADA",
    }
]

DEPOSITS = [
    {
        "id": 300,
        "order_id": "MDP20151014-101010-033333",
        "currency_code": "JPY",
        "amount": 10000.0,
        "status": "COMPLETED",
        "event_date": "2015-10-14T10:10:10.01",
    }
]

WITHDRAW_RESPONSE = {"message_id": "69476620-5056-4003-bcbe-42658a2b041b"}

WITHDRAWALS = [
    {
        "id": 700,
        "order_id": "MWD20151020-090909-011111",
        "currency_code": "JPY",
        "amount": 12000.0,
        "status": "COMPLETED",
        "event_date": "2015-10-20T09:09:09.09",
    }
]

CHILD_ORDER_RESPONSE = {"child_order_acceptance_id": "JRF20150707-050237-639234"}

PARENT_ORDER_RESPONSE = {"parent_order_acceptance_id": "JRF20150707-050237-639234"}

CHILD_ORDERS = [
    {
        "id": 138398,
        "child_order_id": "JOR20150707-084555-022523",
        "product_code": "BTC_JPY",
        "side": "BUY",
        "child_order_type": "LIMIT",
        "price": 30000.0,
        "average_price": 30000.0,
        "size": 0.1,
        "child_order_state": "COMPLETED",
        "expire_date": "2015-07-14T07:25:52",
        "child_order_date": "2015-07-07T08:45:53",
        "child_order_acceptance_id": "JRF20150707-084552-030929",
        "outstanding_size": 0.0,
        "cancel_size": 0.0,
        "executed_size": 0.1,
        "total_commission": 0.0,
        "time_in_force": "GTC",
    }
]

PARENT_ORDERS = [
    {
        "id": 177052,
        "parent_order_id": "JCP20150707-084555-022523",
        "product_code": "FX_BTC_JPY",
        "side": "BUY",
        "parent_order_type": "STOP",
        "price": 30000.0,
        "average_price": 30000.0,
        "size": 0.1,
        "parent_order_state": "COMPLETED",
        "expire_date": "2015-07-14T07:25:52",
        "parent_order_date": "2015-07-07T08:45:53",
        "parent_order_acceptance_id": "JRF20150707-084552-030929",
        "outstanding_size": 0.0,
        "cancel_size": 0.0,
        "executed_size": 0.1,
        "total_commission": 0.0,
    }
]

PARENT_ORDER_DETAIL = {
    "id": 177052,
    "parent_order_id": "JCP20150707-084555-022523",
    "order_method": "IFD",
    "expire_date": "2015-07-14T07:25:52",
    "time_in_force": "GTC",
    "parameters": [
        {
            "product_code": "BTC_JPY",
            "condition_type": "LIMIT",
            "side": "BUY",
            "size": 0.1,
            "price": 30000.0,
            "trigger_price": None,
            "offset": None,
        },
        {
            "product_code": "BTC_JPY",
            "condition_type": "STOP",
            "side": "SELL",
            "size": 0.1,
            "price": None,
            "trigger_price": 29000.0,
            "offset": None,
        },
    ],
    "parent_order_acceptance_id": "JRF20150707-084552-030929",
}

MY_EXECUTIONS = [
    {
        "id": 37233,
        "child_order_id": "JOR20150707-060559-021935",
        "side": "BUY",
        "price": 33470.0,
        "size": 0.01,
        "commission": 0.0,
        "exec_date": "2015-07-07T09:57:40.397",
        "child_order_acceptance_id": "JRF20150707-060559-014939",
    }
]

BALANCE_HISTORY = [
    {
        "id": 674374,
        "trade_date": "2015-11-17T01:22:29.14",
        "event_date": "2015-11-17T01:22:29.14",
        "product_code": "BTC_JPY",
        "currency_code": "JPY",
        "trade_type": "BUY",
        "price": 51000.0,
        "amount": -35700.0,
        "quantity": 0.0,
        "commission": 0.0,
        "balance": 1024078.0,
        "order_id": "JOR20150707-060559-021935",
    }
]

POSITIONS = [
    {
        "product_code": "FX_BTC_JPY",
        "side": "BUY",
        "price": 36000.0,
        "size": 0.01,
        "commission": 0.0,
        "swap_point_accumulate": -35.0,
        "require_collateral": 120.0,
        "open_date": "2015-11-03T10:04:45.011",
        "leverage": 4.0,
        "pnl": 965.0,
        "sfd": -0.5,
        "funding_fees": -1.2,
    }
]

COLLATERAL_HISTORY = [
    {
        "id": 4995,
        "currency_code": "JPY",
        "change": -6.0,
        "amount": -6.0,
        "reason_code": "CLEAR_COLL",
        "date": "2017-05-19T02:18:09.343",
    }
]

TRADING_COMMISSION = {"commission_rate": 0.0015}


def assert_signed(request: Any) -> None:
    """Every Private call carries the three authentication headers."""
    for header in SIGNED_HEADERS:
        assert header in request.headers, f"missing {header}"
    assert request.headers["ACCESS-KEY"] == "test-key"
    assert request.headers["ACCESS-TIMESTAMP"].isdigit()
    assert len(request.headers["ACCESS-SIGN"]) == 64


def test_get_permissions():
    client, api = sync_client(ok(PERMISSIONS), authed=True)
    with client:
        result = client.get_permissions()

    assert result == PERMISSIONS
    assert api.request.url.path == "/v1/me/getpermissions"
    assert_signed(api.request)


def test_get_balance():
    client, api = sync_client(ok(BALANCE), authed=True)
    with client:
        result = client.get_balance()

    assert all(isinstance(b, Balance) for b in result)
    assert result[0].currency_code == "JPY"
    assert result[0].available == 508000.0
    assert api.request.url.path == "/v1/me/getbalance"
    assert_signed(api.request)


def test_get_collateral():
    client, api = sync_client(ok(COLLATERAL), authed=True)
    with client:
        result = client.get_collateral()

    assert isinstance(result, Collateral)
    assert result.keep_rate == 5.0
    assert result.margin_call_due_date is None
    assert api.request.url.path == "/v1/me/getcollateral"
    assert_signed(api.request)


def test_get_collateral_accounts():
    client, api = sync_client(ok(COLLATERAL_ACCOUNTS), authed=True)
    with client:
        result = client.get_collateral_accounts()

    assert all(isinstance(a, CollateralAccount) for a in result)
    assert result[1].currency_code == "BTC"
    assert result[1].amount == 1.5
    assert api.request.url.path == "/v1/me/getcollateralaccounts"
    assert_signed(api.request)


def test_get_addresses():
    client, api = sync_client(ok(ADDRESSES), authed=True)
    with client:
        result = client.get_addresses()

    assert isinstance(result[0], Address)
    assert result[0].currency_code == "BTC"
    assert result[0].type == "NORMAL"
    assert api.request.url.path == "/v1/me/getaddresses"
    assert_signed(api.request)


def test_get_coin_ins():
    client, api = sync_client(ok(COIN_INS), authed=True)
    with client:
        result = client.get_coin_ins(count=10, before=500, after=1)

    assert isinstance(result[0], CoinIn)
    assert result[0].amount == 0.1
    assert result[0].status == "COMPLETED"
    assert api.request.url.path == "/v1/me/getcoinins"
    assert set(api.request.url.params.keys()) == {"count", "before", "after"}
    assert_signed(api.request)


def test_get_coin_outs():
    client, api = sync_client(ok(COIN_OUTS), authed=True)
    with client:
        result = client.get_coin_outs(count=25)

    assert isinstance(result[0], CoinOut)
    assert result[0].fee == 0.0005
    assert result[0].additional_fee == 0.0002
    assert api.request.url.path == "/v1/me/getcoinouts"
    assert api.request.url.params["count"] == "25"
    assert_signed(api.request)


def test_get_bank_accounts():
    client, api = sync_client(ok(BANK_ACCOUNTS), authed=True)
    with client:
        result = client.get_bank_accounts()

    assert isinstance(result[0], BankAccount)
    assert result[0].id == 3402
    assert result[0].is_verified is True
    assert api.request.url.path == "/v1/me/getbankaccounts"
    assert_signed(api.request)


def test_get_deposits():
    client, api = sync_client(ok(DEPOSITS), authed=True)
    with client:
        result = client.get_deposits(count=5)

    assert isinstance(result[0], Deposit)
    assert result[0].amount == 10000.0
    assert result[0].currency_code == "JPY"
    assert api.request.url.path == "/v1/me/getdeposits"
    assert api.request.url.params["count"] == "5"
    assert_signed(api.request)


def test_withdraw():
    client, api = sync_client(ok(WITHDRAW_RESPONSE), authed=True)
    with client:
        result = client.withdraw("JPY", 3402, 12000, code="012345")

    assert isinstance(result, WithdrawResponse)
    assert result.message_id == "69476620-5056-4003-bcbe-42658a2b041b"
    assert api.request.url.path == "/v1/me/withdraw"
    assert api.request.method == "POST"
    assert json.loads(api.request.content) == {
        "currency_code": "JPY",
        "bank_account_id": 3402,
        "amount": 12000,
        "code": "012345",
    }
    assert_signed(api.request)


def test_get_withdrawals():
    client, api = sync_client(ok(WITHDRAWALS), authed=True)
    with client:
        result = client.get_withdrawals(message_id="69476620-5056-4003-bcbe-42658a2b041b")

    assert isinstance(result[0], Withdrawal)
    assert result[0].id == 700
    assert api.request.url.path == "/v1/me/getwithdrawals"
    params = api.request.url.params
    assert params["message_id"] == "69476620-5056-4003-bcbe-42658a2b041b"
    assert set(params.keys()) == {"message_id"}
    assert_signed(api.request)


def test_send_child_order():
    client, api = sync_client(ok(CHILD_ORDER_RESPONSE), authed=True)
    with client:
        result = client.send_child_order(
            ProductCode.BTC_JPY, ChildOrderType.LIMIT, Side.BUY, 0.1, price=5_000_000
        )

    assert isinstance(result, ChildOrderResponse)
    assert result.child_order_acceptance_id == "JRF20150707-050237-639234"
    assert api.request.url.path == "/v1/me/sendchildorder"
    assert json.loads(api.request.content) == {
        "product_code": "BTC_JPY",
        "child_order_type": "LIMIT",
        "side": "BUY",
        "size": 0.1,
        "price": 5_000_000,
        "time_in_force": "GTC",
    }
    assert_signed(api.request)


def test_cancel_child_order():
    client, api = sync_client(empty(), authed=True)
    with client:
        client.cancel_child_order(ProductCode.BTC_JPY, child_order_id="JOR20150707-084555-022523")

    assert api.request.url.path == "/v1/me/cancelchildorder"
    assert json.loads(api.request.content) == {
        "product_code": "BTC_JPY",
        "child_order_id": "JOR20150707-084555-022523",
    }
    assert_signed(api.request)


def test_send_parent_order():
    client, api = sync_client(ok(PARENT_ORDER_RESPONSE), authed=True)
    with client:
        result = client.send_parent_order(
            [
                ParentOrderParameter(
                    product_code=ProductCode.FX_BTC_JPY,
                    condition_type=ConditionType.LIMIT,
                    side=Side.BUY,
                    size=0.01,
                    price=9_000_000,
                )
            ],
            order_method=OrderMethod.SIMPLE,
            minute_to_expire=10,
        )

    assert isinstance(result, ParentOrderResponse)
    assert result.parent_order_acceptance_id == "JRF20150707-050237-639234"
    assert api.request.url.path == "/v1/me/sendparentorder"
    body = json.loads(api.request.content)
    assert body["order_method"] == "SIMPLE"
    assert body["minute_to_expire"] == 10
    assert body["parameters"][0]["price"] == 9_000_000
    assert_signed(api.request)


def test_cancel_parent_order():
    client, api = sync_client(empty(), authed=True)
    with client:
        client.cancel_parent_order(
            ProductCode.FX_BTC_JPY, parent_order_acceptance_id="JRF20150707-084552-030929"
        )

    assert api.request.url.path == "/v1/me/cancelparentorder"
    assert json.loads(api.request.content) == {
        "product_code": "FX_BTC_JPY",
        "parent_order_acceptance_id": "JRF20150707-084552-030929",
    }
    assert_signed(api.request)


def test_cancel_all_child_orders():
    client, api = sync_client(empty(), authed=True)
    with client:
        client.cancel_all_child_orders(ProductCode.ETH_JPY)

    assert api.request.url.path == "/v1/me/cancelallchildorders"
    assert json.loads(api.request.content) == {"product_code": "ETH_JPY"}
    assert_signed(api.request)


def test_get_child_orders():
    client, api = sync_client(ok(CHILD_ORDERS), authed=True)
    with client:
        result = client.get_child_orders(ProductCode.BTC_JPY, child_order_state="COMPLETED")

    assert isinstance(result[0], ChildOrder)
    assert result[0].child_order_state == "COMPLETED"
    assert result[0].executed_size == 0.1
    assert api.request.url.path == "/v1/me/getchildorders"
    params = api.request.url.params
    assert params["product_code"] == "BTC_JPY"
    assert params["child_order_state"] == "COMPLETED"
    assert set(params.keys()) == {"product_code", "child_order_state"}
    assert_signed(api.request)


def test_get_parent_orders():
    client, api = sync_client(ok(PARENT_ORDERS), authed=True)
    with client:
        result = client.get_parent_orders(ProductCode.FX_BTC_JPY, parent_order_state="COMPLETED")

    assert isinstance(result[0], ParentOrder)
    assert result[0].parent_order_type == "STOP"
    assert result[0].parent_order_state == "COMPLETED"
    assert api.request.url.path == "/v1/me/getparentorders"
    params = api.request.url.params
    assert params["product_code"] == "FX_BTC_JPY"
    assert params["parent_order_state"] == "COMPLETED"
    assert_signed(api.request)


def test_get_parent_order():
    client, api = sync_client(ok(PARENT_ORDER_DETAIL), authed=True)
    with client:
        result = client.get_parent_order(parent_order_id="JCP20150707-084555-022523")

    assert isinstance(result, ParentOrderDetail)
    assert result.order_method == "IFD"
    assert len(result.parameters) == 2
    assert isinstance(result.parameters[0], ParentOrderParameter)
    assert result.parameters[1].trigger_price == 29000.0
    assert result.parameters[1].price is None
    assert api.request.url.path == "/v1/me/getparentorder"
    params = api.request.url.params
    assert params["parent_order_id"] == "JCP20150707-084555-022523"
    assert set(params.keys()) == {"parent_order_id"}
    assert_signed(api.request)


def test_get_my_executions():
    client, api = sync_client(ok(MY_EXECUTIONS), authed=True)
    with client:
        result = client.get_my_executions(
            ProductCode.BTC_JPY, child_order_acceptance_id="JRF20150707-060559-014939"
        )

    assert isinstance(result[0], MyExecution)
    assert result[0].price == 33470.0
    assert result[0].child_order_id == "JOR20150707-060559-021935"
    assert api.request.url.path == "/v1/me/getexecutions"
    params = api.request.url.params
    assert params["product_code"] == "BTC_JPY"
    assert params["child_order_acceptance_id"] == "JRF20150707-060559-014939"
    assert_signed(api.request)


def test_get_balance_history():
    client, api = sync_client(ok(BALANCE_HISTORY), authed=True)
    with client:
        result = client.get_balance_history("JPY", count=1)

    assert isinstance(result[0], BalanceHistory)
    assert result[0].balance == 1024078.0
    assert result[0].trade_type == "BUY"
    assert api.request.url.path == "/v1/me/getbalancehistory"
    params = api.request.url.params
    assert params["currency_code"] == "JPY"
    assert params["count"] == "1"
    assert_signed(api.request)


def test_get_positions():
    client, api = sync_client(ok(POSITIONS), authed=True)
    with client:
        result = client.get_positions()

    assert isinstance(result[0], Position)
    assert result[0].pnl == 965.0
    assert result[0].sfd == -0.5
    assert api.request.url.path == "/v1/me/getpositions"
    assert api.request.url.params["product_code"] == ProductCode.FX_BTC_JPY
    assert_signed(api.request)


def test_get_collateral_history():
    client, api = sync_client(ok(COLLATERAL_HISTORY), authed=True)
    with client:
        result = client.get_collateral_history(count=1)

    assert isinstance(result[0], CollateralHistory)
    assert result[0].reason_code == "CLEAR_COLL"
    assert result[0].change == -6.0
    assert api.request.url.path == "/v1/me/getcollateralhistory"
    assert api.request.url.params["count"] == "1"
    assert_signed(api.request)


def test_get_trading_commission():
    client, api = sync_client(ok(TRADING_COMMISSION), authed=True)
    with client:
        result = client.get_trading_commission(ProductCode.BTC_JPY)

    assert isinstance(result, TradingCommission)
    assert result.commission_rate == 0.0015
    assert api.request.url.path == "/v1/me/gettradingcommission"
    assert api.request.url.params["product_code"] == "BTC_JPY"
    assert_signed(api.request)


# --- empty cancel bodies ------------------------------------------------------

CANCELS: list[tuple[str, Callable[[Any], None]]] = [
    ("cancel_child_order", lambda c: c.cancel_child_order(child_order_id="JOR-1")),
    ("cancel_parent_order", lambda c: c.cancel_parent_order(parent_order_id="JCP-1")),
    ("cancel_all_child_orders", lambda c: c.cancel_all_child_orders()),
]


@pytest.mark.parametrize(("name", "call"), CANCELS, ids=[name for name, _ in CANCELS])
def test_cancel_returns_none_on_empty_body(name: str, call: Callable[[Any], None]) -> None:
    """A zero-length 200 must not reach ``response.json()``."""
    client, api = sync_client(empty(), authed=True)
    with client:
        call(client)

    assert api.count == 1
    assert api.request.url.path.startswith("/v1/me/cancel")


# --- request bodies -----------------------------------------------------------


def test_send_child_order_market_omits_price():
    client, api = sync_client(ok(CHILD_ORDER_RESPONSE), authed=True)
    with client:
        result = client.send_child_order(
            ProductCode.FX_BTC_JPY, ChildOrderType.MARKET, Side.SELL, 0.01, price=None
        )

    assert isinstance(result, ChildOrderResponse)
    body = json.loads(api.request.content)
    assert "price" not in body
    assert "minute_to_expire" not in body
    assert body == {
        "product_code": "FX_BTC_JPY",
        "child_order_type": "MARKET",
        "side": "SELL",
        "size": 0.01,
        "time_in_force": "GTC",
    }


STOP_LEG_MODEL = ParentOrderParameter(
    product_code=ProductCode.FX_BTC_JPY,
    condition_type=ConditionType.STOP,
    side=Side.SELL,
    size=0.01,
    trigger_price=9_000_000,
)

STOP_LEG_DICT = {
    "product_code": "FX_BTC_JPY",
    "condition_type": "STOP",
    "side": "SELL",
    "size": 0.01,
    "trigger_price": 9_000_000,
}


@pytest.mark.parametrize("leg", [STOP_LEG_MODEL, STOP_LEG_DICT], ids=["model", "dict"])
def test_send_parent_order_accepts_models_and_dicts(leg: Any) -> None:
    client, api = sync_client(ok(PARENT_ORDER_RESPONSE), authed=True)
    with client:
        result = client.send_parent_order([leg])

    assert isinstance(result, ParentOrderResponse)
    assert api.request.url.path == "/v1/me/sendparentorder"
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
    assert "price" not in body["parameters"][0]
    assert "offset" not in body["parameters"][0]


def test_send_parent_order_omits_minute_to_expire_when_unset():
    client, api = sync_client(ok(PARENT_ORDER_RESPONSE), authed=True)
    with client:
        client.send_parent_order([STOP_LEG_MODEL])

    body = json.loads(api.request.content)
    assert "minute_to_expire" not in body
    assert set(body) == {"order_method", "time_in_force", "parameters"}


def test_send_parent_order_multi_leg_ifdoco():
    entry = ParentOrderParameter(
        product_code=ProductCode.FX_BTC_JPY,
        condition_type=ConditionType.LIMIT,
        side=Side.BUY,
        size=0.1,
        price=8_000_000,
    )
    trail = ParentOrderParameter(
        product_code=ProductCode.FX_BTC_JPY,
        condition_type=ConditionType.TRAIL,
        side=Side.SELL,
        size=0.1,
        offset=100_000,
    )
    client, api = sync_client(ok(PARENT_ORDER_RESPONSE), authed=True)
    with client:
        client.send_parent_order([entry, trail, STOP_LEG_MODEL], order_method=OrderMethod.IFDOCO)

    body = json.loads(api.request.content)
    assert body["order_method"] == "IFDOCO"
    assert len(body["parameters"]) == 3
    assert set(body["parameters"][1]) == {
        "product_code",
        "condition_type",
        "side",
        "size",
        "offset",
    }


# --- missing credentials ------------------------------------------------------

PRIVATE_CALLS: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = [
    ("get_permissions", (), {}),
    ("get_balance", (), {}),
    ("get_collateral", (), {}),
    ("get_collateral_accounts", (), {}),
    ("get_addresses", (), {}),
    ("get_coin_ins", (), {}),
    ("get_coin_outs", (), {}),
    ("get_bank_accounts", (), {}),
    ("get_deposits", (), {}),
    ("withdraw", ("JPY", 3402, 10000), {}),
    ("get_withdrawals", (), {}),
    ("send_child_order", ("BTC_JPY", "MARKET", "BUY", 0.01), {}),
    ("cancel_child_order", (), {"child_order_id": "JOR-1"}),
    ("send_parent_order", ([STOP_LEG_MODEL],), {}),
    ("cancel_parent_order", (), {"parent_order_id": "JCP-1"}),
    ("cancel_all_child_orders", (), {}),
    ("get_child_orders", (), {}),
    ("get_parent_orders", (), {}),
    ("get_parent_order", (), {"parent_order_id": "JCP-1"}),
    ("get_my_executions", (), {}),
    ("get_balance_history", (), {}),
    ("get_positions", (), {}),
    ("get_collateral_history", (), {}),
    ("get_trading_commission", (), {}),
]


def test_private_calls_cover_every_method():
    """Guards the table below against a method being added and forgotten."""
    from pylightningfx import PrivateAPI

    declared = {n for n in vars(PrivateAPI) if not n.startswith("_")}
    assert declared == {name for name, _, _ in PRIVATE_CALLS}
    assert len(PRIVATE_CALLS) == 24


@pytest.mark.parametrize(
    ("name", "args", "kwargs"), PRIVATE_CALLS, ids=[c[0] for c in PRIVATE_CALLS]
)
def test_private_requires_credentials(
    name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> None:
    client, api = sync_client()
    with client, pytest.raises(CredentialsError):
        getattr(client, name)(*args, **kwargs)

    assert api.count == 0, "no request should reach the network unsigned"
