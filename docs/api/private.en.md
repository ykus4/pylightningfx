# Private API

These endpoints require authentication via API key and secret.

```python
from pylightningfx import Client

client = Client(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
```

---

## get_permissions

```python
client.get_permissions() -> list[str]
```

Returns a list of endpoints accessible with the current API key.

---

## get_balance

```python
client.get_balance() -> list[dict]
```

Returns the account balance for each currency.

---

## get_collateral / get_collateral_accounts

```python
client.get_collateral() -> dict
client.get_collateral_accounts() -> list[dict]
```

Returns collateral status and per-currency collateral amounts.

---

## get_addresses

```python
client.get_addresses() -> list[dict]
```

Returns deposit addresses for each cryptocurrency.

---

## get_coin_ins / get_coin_outs

```python
client.get_coin_ins(count, before, after) -> list[dict]
client.get_coin_outs(count, before, after) -> list[dict]
```

Returns cryptocurrency deposit and withdrawal history.

---

## get_bank_accounts

```python
client.get_bank_accounts() -> list[dict]
```

Returns a list of registered bank accounts.

---

## get_deposits / get_withdrawals

```python
client.get_deposits(count, before, after) -> list[dict]
client.get_withdrawals(count, before, after, message_id) -> list[dict]
```

Returns fiat deposit and withdrawal history.

---

## withdraw

```python
client.withdraw(
    currency_code: str,
    bank_account_id: int,
    amount: int,
    code: str | None = None,
) -> dict
```

Submits a withdrawal request. Pass `code` if two-factor authentication is required.

---

## send_child_order

```python
client.send_child_order(
    product_code: str,
    child_order_type: str,   # "LIMIT" or "MARKET"
    side: str,               # "BUY" or "SELL"
    size: float,
    price: float | None = None,
    minute_to_expire: int = 43200,
    time_in_force: str = "GTC",
) -> dict
```

Places a new order.

---

## cancel_child_order

```python
client.cancel_child_order(
    product_code: str,
    child_order_id: str | None = None,
    child_order_acceptance_id: str | None = None,
) -> None
```

Cancels an existing order. Provide either `child_order_id` or `child_order_acceptance_id`.

---

## send_parent_order

```python
client.send_parent_order(
    parameters: list[dict],
    order_method: str = "SIMPLE",  # SIMPLE / IFD / OCO / IFDOCO
    minute_to_expire: int = 43200,
    time_in_force: str = "GTC",
) -> dict
```

Places a special order (IFD / OCO / IFDOCO).

---

## cancel_parent_order / cancel_all_child_orders

```python
client.cancel_parent_order(product_code, parent_order_id, parent_order_acceptance_id) -> None
client.cancel_all_child_orders(product_code: str) -> None
```

Cancels a parent order or all open orders for a product.

---

## get_child_orders / get_parent_orders / get_parent_order

```python
client.get_child_orders(product_code, count, before, after, child_order_state, ...) -> list[dict]
client.get_parent_orders(product_code, count, before, after, parent_order_state) -> list[dict]
client.get_parent_order(parent_order_id, parent_order_acceptance_id) -> dict
```

Returns order lists and details.

---

## get_my_executions

```python
client.get_my_executions(
    product_code, count, before, after,
    child_order_id, child_order_acceptance_id,
) -> list[dict]
```

Returns your personal execution history.

---

## get_balance_history

```python
client.get_balance_history(currency_code: str = "JPY", count, before, after) -> list[dict]
```

Returns balance change history for the specified currency.

---

## get_positions

```python
client.get_positions(product_code: str = "FX_BTC_JPY") -> list[dict]
```

Returns open CFD positions.

---

## get_collateral_history

```python
client.get_collateral_history(count, before, after) -> list[dict]
```

Returns collateral change history.

---

## get_trading_commission

```python
client.get_trading_commission(product_code: str) -> dict
```

Returns the trading commission rate for the specified product.
