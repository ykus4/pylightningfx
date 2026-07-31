"""Response models for the Public API.

String fields such as ``product_code``, ``state`` and ``side`` are typed ``str``
rather than as enums so that a product or state bitFlyer adds after this release
still parses. See [`pylightningfx.enums`][pylightningfx.enums] for the known values.
"""

from datetime import datetime

from pydantic import BaseModel

__all__ = [
    "Board",
    "BoardEntry",
    "BoardState",
    "Chat",
    "CorporateLeverage",
    "Execution",
    "FundingRate",
    "FundingRateHistory",
    "Health",
    "Market",
    "Ticker",
]


class Market(BaseModel):
    """A tradable market."""

    product_code: str
    market_type: str
    """One of [`MarketType`][pylightningfx.enums.MarketType]."""


class BoardEntry(BaseModel):
    """A single price level in the order book."""

    price: float
    size: float


class Board(BaseModel):
    """A snapshot of the order book.

    The order of ``bids`` and ``asks`` is not guaranteed, so sort before
    treating the first element as the best price::

        best_bid = max(board.bids, key=lambda e: e.price)
    """

    mid_price: float
    bids: list[BoardEntry]
    asks: list[BoardEntry]


class Ticker(BaseModel):
    """Best bid and ask, last traded price, and rolling volume."""

    product_code: str
    state: str
    """One of [`MarketState`][pylightningfx.enums.MarketState]."""
    timestamp: datetime
    tick_id: int
    best_bid: float
    best_ask: float
    best_bid_size: float
    best_ask_size: float
    total_bid_depth: float
    total_ask_depth: float
    market_bid_size: float
    market_ask_size: float
    ltp: float
    """Last traded price."""
    volume: float
    """24-hour volume across every market of the underlying asset."""
    volume_by_product: float
    """24-hour volume for this ``product_code`` alone."""
    preopen_end: datetime | None = None
    """When the pre-open auction ends. Undocumented by bitFlyer; usually ``None``."""
    circuit_break_end: datetime | None = None
    """When the circuit breaker lifts. Undocumented by bitFlyer; usually ``None``."""


class Execution(BaseModel):
    """A public trade."""

    id: int
    side: str
    """Taker side; one of [`Side`][pylightningfx.enums.Side].

    Empty for trades matched by the opening auction, which have no taker.
    """
    price: float
    size: float
    exec_date: datetime
    buy_child_order_acceptance_id: str
    sell_child_order_acceptance_id: str


class BoardState(BaseModel):
    """Order book availability, which is finer-grained than
    [`Health`][pylightningfx.models.public.Health]."""

    health: str
    """One of [`HealthStatus`][pylightningfx.enums.HealthStatus]."""
    state: str
    """One of [`MarketState`][pylightningfx.enums.MarketState]."""


class Health(BaseModel):
    """Exchange health for one market."""

    status: str
    """One of [`HealthStatus`][pylightningfx.enums.HealthStatus]."""


class FundingRate(BaseModel):
    """The current funding rate for a perpetual market."""

    current_funding_rate: float
    next_funding_rate_settledate: datetime


class FundingRateHistory(BaseModel):
    """One settled funding rate."""

    calculation_date: datetime
    settlement_date: datetime
    rate: float


class CorporateLeverage(BaseModel):
    """Maximum leverage for corporate accounts, current and upcoming."""

    current_max: float
    current_startdate: datetime
    next_max: float | None = None
    next_startdate: datetime | None = None


class Chat(BaseModel):
    """A message from the exchange chat room."""

    nickname: str
    message: str
    date: datetime
