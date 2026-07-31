"""String constants for bitFlyer API parameters and response fields.

Every member is a `enum.StrEnum`, so it can be passed anywhere a plain
``str`` is accepted and compares equal to its literal value::

    client.send_child_order(ProductCode.FX_BTC_JPY, ChildOrderType.MARKET, Side.BUY, 0.01)
    client.get_health().status == HealthStatus.NORMAL

These are *convenience constants, not validators*. Request parameters and model
fields are typed ``str`` on purpose: bitFlyer adds and removes products and
introduces new state values without warning, and a closed enum would reject
valid values. Prefer the constants for the values you know, pass a string for
anything newer than this release.
"""

from enum import StrEnum

__all__ = [
    "ChildOrderEventType",
    "ChildOrderState",
    "ChildOrderType",
    "ConditionType",
    "HealthStatus",
    "MarketState",
    "MarketType",
    "OrderMethod",
    "ParentOrderEventType",
    "ParentOrderState",
    "ProductCode",
    "Side",
    "TimeInForce",
]


class ProductCode(StrEnum):
    """Market identifiers, as returned by ``GET /v1/getmarkets``."""

    BTC_JPY = "BTC_JPY"
    XRP_JPY = "XRP_JPY"
    ETH_JPY = "ETH_JPY"
    XLM_JPY = "XLM_JPY"
    MONA_JPY = "MONA_JPY"
    ELF_JPY = "ELF_JPY"
    ETH_BTC = "ETH_BTC"
    BCH_BTC = "BCH_BTC"
    FX_BTC_JPY = "FX_BTC_JPY"


class MarketType(StrEnum):
    """The ``market_type`` field of a [`Market`][pylightningfx.models.public.Market]."""

    SPOT = "Spot"
    FX = "FX"
    FUTURES = "Futures"


class Side(StrEnum):
    """Order and execution direction."""

    BUY = "BUY"
    SELL = "SELL"


class ChildOrderType(StrEnum):
    """Order type for ``send_child_order``."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"


class TimeInForce(StrEnum):
    """Execution condition for an order."""

    GTC = "GTC"
    """Good 'Til Canceled."""

    IOC = "IOC"
    """Immediate Or Cancel."""

    FOK = "FOK"
    """Fill Or Kill."""


class OrderMethod(StrEnum):
    """Order method for ``send_parent_order``."""

    SIMPLE = "SIMPLE"
    IFD = "IFD"
    OCO = "OCO"
    IFDOCO = "IFDOCO"


class ConditionType(StrEnum):
    """Trigger condition for a parent order parameter."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAIL = "TRAIL"


class ChildOrderState(StrEnum):
    """Lifecycle state of a child order.

    Note that ``ACTIVE``, ``COMPLETED``, ``CANCELED``, ``EXPIRED`` and
    ``REJECTED`` are also accepted as the ``child_order_state`` *filter* of
    ``get_child_orders``.
    """

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class ParentOrderState(StrEnum):
    """Lifecycle state of a parent order."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class ChildOrderEventType(StrEnum):
    """``event_type`` of a [`ChildOrderEvent`][pylightningfx.models.realtime.ChildOrderEvent]."""

    ORDER = "ORDER"
    """The order was accepted and is now on the book."""
    ORDER_FAILED = "ORDER_FAILED"
    """The order was rejected; read ``reason``."""
    CANCEL = "CANCEL"
    CANCEL_FAILED = "CANCEL_FAILED"
    EXECUTION = "EXECUTION"
    """A fill, whole or partial; read ``outstanding_size`` for the remainder."""
    EXPIRE = "EXPIRE"


class ParentOrderEventType(StrEnum):
    """``event_type`` of a [`ParentOrderEvent`][pylightningfx.models.realtime.ParentOrderEvent]."""

    ORDER = "ORDER"
    ORDER_FAILED = "ORDER_FAILED"
    CANCEL = "CANCEL"
    TRIGGER = "TRIGGER"
    """A condition fired and placed a child order."""
    COMPLETE = "COMPLETE"
    EXPIRE = "EXPIRE"


class HealthStatus(StrEnum):
    """Exchange health, as returned by ``GET /v1/gethealth``."""

    NORMAL = "NORMAL"
    BUSY = "BUSY"
    VERY_BUSY = "VERY BUSY"
    SUPER_BUSY = "SUPER BUSY"
    NO_ORDER = "NO ORDER"
    STOP = "STOP"


class MarketState(StrEnum):
    """Trading session state of a market.

    Shared by the ``state`` field of both [`Ticker`][pylightningfx.models.public.Ticker] and
    [`BoardState`][pylightningfx.models.public.BoardState].
    """

    RUNNING = "RUNNING"
    CLOSED = "CLOSED"
    STARTING = "STARTING"
    PREOPEN = "PREOPEN"
    CIRCUIT_BREAK = "CIRCUIT BREAK"
    AWAITING_SQ = "AWAITING SQ"
    MATURED = "MATURED"
