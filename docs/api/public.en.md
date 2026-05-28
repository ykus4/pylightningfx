# Public API

Endpoints that do not require authentication.

## get_markets

```python
client.get_markets() -> list[dict]
```

Returns a list of available markets.

**Example response:**
```json
[
  {"product_code": "BTC_JPY", "market_type": "Spot"},
  {"product_code": "FX_BTC_JPY", "market_type": "FX"}
]
```

---

## get_board

```python
client.get_board(product_code: str = "BTC_JPY") -> dict
```

Returns the order book for the specified market.

---

## get_ticker

```python
client.get_ticker(product_code: str = "BTC_JPY") -> dict
```

Returns the latest ticker for the specified market.

| Field | Description |
|-------|-------------|
| `ltp` | Last traded price |
| `best_bid` / `best_ask` | Best bid / ask price |
| `volume` | 24-hour trading volume |

---

## get_executions

```python
client.get_executions(
    product_code: str = "BTC_JPY",
    count: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> list[dict]
```

Returns execution history (up to 31 days in the past).

---

## get_board_state

```python
client.get_board_state(product_code: str = "BTC_JPY") -> dict
```

Returns the current state of the order book, including `health` and `state`.

---

## get_health

```python
client.get_health(product_code: str = "BTC_JPY") -> dict
```

Returns the current operational status of the exchange.

---

## get_funding_rate

```python
client.get_funding_rate(product_code: str) -> dict
```

Returns the next scheduled funding rate. `product_code` is required (e.g. `FX_BTC_JPY`).

---

## get_funding_rate_history

```python
client.get_funding_rate_history(
    product_code: str,
    count: int | None = None,
    from_: str | None = None,
    to: str | None = None,
) -> list[dict]
```

Returns historical funding rates.

---

## get_corporate_leverage

```python
client.get_corporate_leverage() -> dict
```

Returns the maximum leverage for corporate accounts.

---

## get_chats

```python
client.get_chats(from_date: str | None = None) -> list[dict]
```

Returns chat messages. Defaults to messages from the past 5 days if `from_date` is omitted.
