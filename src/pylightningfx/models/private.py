"""Request and response models for the Private API.

String fields such as ``product_code``, ``side`` and ``child_order_state`` are
typed ``str`` rather than as enums so that a value bitFlyer adds after this
release still parses. See [`pylightningfx.enums`][pylightningfx.enums] for the known values.
"""

from datetime import datetime

from pydantic import BaseModel

__all__ = [
    "Address",
    "Balance",
    "BalanceHistory",
    "BankAccount",
    "ChildOrder",
    "ChildOrderResponse",
    "CoinIn",
    "CoinOut",
    "Collateral",
    "CollateralAccount",
    "CollateralHistory",
    "Deposit",
    "MyExecution",
    "ParentOrder",
    "ParentOrderDetail",
    "ParentOrderParameter",
    "ParentOrderResponse",
    "Position",
    "TradingCommission",
    "WithdrawResponse",
    "Withdrawal",
]


class Balance(BaseModel):
    """Balance of one currency.

    ``available`` excludes amounts reserved by open orders, so it is the figure
    to size new orders against.
    """

    currency_code: str
    amount: float
    available: float


class Collateral(BaseModel):
    """Margin status for the account as a whole."""

    collateral: float
    open_position_pnl: float
    require_collateral: float
    keep_rate: float
    """Maintenance margin ratio. A margin call follows once this falls far enough."""
    margin_call_amount: float | None = None
    margin_call_due_date: datetime | None = None


class CollateralAccount(BaseModel):
    """Collateral held in one currency."""

    currency_code: str
    amount: float


class Address(BaseModel):
    """A deposit address for one crypto asset."""

    type: str
    currency_code: str
    address: str


class CoinIn(BaseModel):
    """An incoming crypto transfer."""

    id: int
    order_id: str
    currency_code: str
    amount: float
    address: str
    tx_hash: str
    status: str
    event_date: datetime


class CoinOut(BaseModel):
    """An outgoing crypto transfer."""

    id: int
    order_id: str
    currency_code: str
    amount: float
    address: str
    tx_hash: str
    fee: float
    additional_fee: float
    status: str
    event_date: datetime


class BankAccount(BaseModel):
    """A registered bank account, usable as a withdrawal destination."""

    id: int
    """Pass as ``bank_account_id`` to ``withdraw``."""
    is_verified: bool
    bank_name: str
    branch_name: str
    account_type: str
    account_number: str
    account_name: str


class Deposit(BaseModel):
    """A cash deposit."""

    id: int
    order_id: str
    currency_code: str
    amount: float
    status: str
    event_date: datetime


class Withdrawal(BaseModel):
    """A cash withdrawal."""

    id: int
    order_id: str
    currency_code: str
    amount: float
    status: str
    event_date: datetime


class WithdrawResponse(BaseModel):
    """Acknowledgement of a withdrawal request."""

    message_id: str
    """Pass as ``message_id`` to ``get_withdrawals`` to follow up on this request."""


class ChildOrderResponse(BaseModel):
    """Acknowledgement of an order submission.

    The exchange has accepted the order, not necessarily filled or even placed
    it. Poll ``get_child_orders`` with the acceptance id, or subscribe to
    ``child_order_events`` on the Realtime API, to learn what happened.
    """

    child_order_acceptance_id: str


class ParentOrderResponse(BaseModel):
    """Acknowledgement of a parent order submission."""

    parent_order_acceptance_id: str


class ChildOrder(BaseModel):
    """One of your orders."""

    id: int
    child_order_id: str
    product_code: str
    side: str
    child_order_type: str
    price: float
    average_price: float
    size: float
    child_order_state: str
    """One of [`ChildOrderState`][pylightningfx.enums.ChildOrderState]."""
    expire_date: datetime
    child_order_date: datetime
    child_order_acceptance_id: str
    outstanding_size: float
    cancel_size: float
    executed_size: float
    total_commission: float
    time_in_force: str


class ParentOrder(BaseModel):
    """One of your parent (conditional) orders, as listed."""

    id: int
    parent_order_id: str
    product_code: str
    side: str
    parent_order_type: str
    price: float
    average_price: float
    size: float
    parent_order_state: str
    """One of [`ParentOrderState`][pylightningfx.enums.ParentOrderState]."""
    expire_date: datetime
    parent_order_date: datetime
    parent_order_acceptance_id: str
    outstanding_size: float
    cancel_size: float
    executed_size: float
    total_commission: float


class ParentOrderParameter(BaseModel):
    """One leg of a parent order.

    Serves as both the input to ``send_parent_order`` and an element of
    [`parameters`][pylightningfx.models.private.ParentOrderDetail.parameters]. Fields that only
    apply to certain
    condition types default to ``None`` and are left out of the request body::

        client.send_parent_order(
            [
                ParentOrderParameter(
                    product_code=ProductCode.FX_BTC_JPY,
                    condition_type=ConditionType.STOP,
                    side=Side.SELL,
                    size=0.01,
                    trigger_price=9_000_000,
                )
            ]
        )
    """

    product_code: str
    condition_type: str
    """One of [`ConditionType`][pylightningfx.enums.ConditionType]."""
    side: str
    size: float
    price: float | None = None
    """Required for ``LIMIT`` and ``STOP_LIMIT``."""
    trigger_price: float | None = None
    """Required for ``STOP`` and ``STOP_LIMIT``."""
    offset: float | None = None
    """Required for ``TRAIL``; the trailing distance in the quote currency."""


class ParentOrderDetail(BaseModel):
    """A parent order together with its legs."""

    id: int
    parent_order_id: str
    order_method: str
    """One of [`OrderMethod`][pylightningfx.enums.OrderMethod]."""
    expire_date: datetime
    time_in_force: str
    parameters: list[ParentOrderParameter]
    parent_order_acceptance_id: str


class MyExecution(BaseModel):
    """One of your fills."""

    id: int
    child_order_id: str
    side: str
    price: float
    size: float
    commission: float
    exec_date: datetime
    child_order_acceptance_id: str


class BalanceHistory(BaseModel):
    """One entry from the balance ledger."""

    id: int
    trade_date: datetime
    event_date: datetime
    product_code: str
    currency_code: str
    trade_type: str
    price: float
    amount: float
    quantity: float
    commission: float
    balance: float
    """Running balance after this entry."""
    order_id: str


class Position(BaseModel):
    """An open leveraged position.

    bitFlyer reports positions individually rather than netted, so a single
    market can hold several entries on the same side.
    """

    product_code: str
    side: str
    price: float
    size: float
    commission: float
    swap_point_accumulate: float
    require_collateral: float
    open_date: datetime
    leverage: float
    pnl: float
    sfd: float
    """Swap For Difference charge, applied when FX_BTC_JPY diverges from BTC_JPY."""
    funding_fees: float


class CollateralHistory(BaseModel):
    """One change to the collateral balance."""

    id: int
    currency_code: str
    change: float
    amount: float
    reason_code: str
    date: datetime


class TradingCommission(BaseModel):
    """The commission rate applied to your trades on one market."""

    commission_rate: float
    """Fraction of notional, so ``0.0015`` means 0.15%."""
