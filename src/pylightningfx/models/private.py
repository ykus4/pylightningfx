from datetime import datetime

from pydantic import BaseModel


class Balance(BaseModel):
    currency_code: str
    amount: float
    available: float


class Collateral(BaseModel):
    collateral: float
    open_position_pnl: float
    require_collateral: float
    keep_rate: float
    margin_call_amount: float | None = None
    margin_call_due_date: datetime | None = None


class CollateralAccount(BaseModel):
    currency_code: str
    amount: float


class Address(BaseModel):
    type: str
    currency_code: str
    address: str


class CoinIn(BaseModel):
    id: int
    order_id: str
    currency_code: str
    amount: float
    address: str
    tx_hash: str
    status: str
    event_date: datetime


class CoinOut(BaseModel):
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
    id: int
    is_verified: bool
    bank_name: str
    branch_name: str
    account_type: str
    account_number: str
    account_name: str


class Deposit(BaseModel):
    id: int
    order_id: str
    currency_code: str
    amount: float
    status: str
    event_date: datetime


class Withdrawal(BaseModel):
    id: int
    order_id: str
    currency_code: str
    amount: float
    status: str
    event_date: datetime


class ChildOrder(BaseModel):
    id: int
    child_order_id: str
    product_code: str
    side: str
    child_order_type: str
    price: float
    average_price: float
    size: float
    child_order_state: str
    expire_date: datetime
    child_order_date: datetime
    child_order_acceptance_id: str
    outstanding_size: float
    cancel_size: float
    executed_size: float
    total_commission: float
    time_in_force: str


class ParentOrder(BaseModel):
    id: int
    parent_order_id: str
    product_code: str
    side: str
    parent_order_type: str
    price: float
    average_price: float
    size: float
    parent_order_state: str
    expire_date: datetime
    parent_order_date: datetime
    parent_order_acceptance_id: str
    outstanding_size: float
    cancel_size: float
    executed_size: float
    total_commission: float


class ParentOrderParameter(BaseModel):
    product_code: str
    condition_type: str
    side: str
    price: float
    size: float
    trigger_price: float
    offset: float


class ParentOrderDetail(BaseModel):
    id: int
    parent_order_id: str
    order_method: str
    expire_date: datetime
    time_in_force: str
    parameters: list[ParentOrderParameter]
    parent_order_acceptance_id: str


class MyExecution(BaseModel):
    id: int
    child_order_id: str
    side: str
    price: float
    size: float
    commission: float
    exec_date: datetime
    child_order_acceptance_id: str


class BalanceHistory(BaseModel):
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
    order_id: str


class Position(BaseModel):
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
    funding_fees: float


class CollateralHistory(BaseModel):
    id: int
    currency_code: str
    change: float
    amount: float
    reason_code: str
    date: datetime


class TradingCommission(BaseModel):
    commission_rate: float
