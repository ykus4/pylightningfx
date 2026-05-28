from datetime import datetime

from pydantic import BaseModel


class Market(BaseModel):
    product_code: str
    market_type: str


class BoardEntry(BaseModel):
    price: float
    size: float


class Board(BaseModel):
    mid_price: float
    bids: list[BoardEntry]
    asks: list[BoardEntry]


class Ticker(BaseModel):
    product_code: str
    state: str
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
    volume: float
    volume_by_product: float


class Execution(BaseModel):
    id: int
    side: str
    price: float
    size: float
    exec_date: datetime
    buy_child_order_acceptance_id: str
    sell_child_order_acceptance_id: str


class BoardState(BaseModel):
    health: str
    state: str


class Health(BaseModel):
    status: str


class FundingRate(BaseModel):
    current_funding_rate: float
    next_funding_rate_settledate: datetime


class FundingRateHistory(BaseModel):
    calculation_date: datetime
    settlement_date: datetime
    rate: float


class CorporateLeverage(BaseModel):
    current_max: float
    current_startdate: datetime
    next_max: float | None = None
    next_startdate: datetime | None = None


class Chat(BaseModel):
    nickname: str
    message: str
    date: datetime
