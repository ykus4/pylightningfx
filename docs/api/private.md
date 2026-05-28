# Private API

API key と API secret による認証が必要です。

```python
from bitflyerpy import Client

client = Client(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
```

---

## get_permissions

```python
client.get_permissions() -> list[str]
```

この API キーで呼出可能なエンドポイントの一覧を取得します。

---

## get_balance

```python
client.get_balance() -> list[dict]
```

資産残高を取得します。

---

## get_collateral / get_collateral_accounts

```python
client.get_collateral() -> dict
client.get_collateral_accounts() -> list[dict]
```

証拠金の状態・通貨別数量を取得します。

---

## get_addresses

```python
client.get_addresses() -> list[dict]
```

仮想通貨の預入用アドレスを取得します。

---

## get_coin_ins / get_coin_outs

```python
client.get_coin_ins(count, before, after) -> list[dict]
client.get_coin_outs(count, before, after) -> list[dict]
```

仮想通貨の預入・送付履歴を取得します。

---

## get_bank_accounts

```python
client.get_bank_accounts() -> list[dict]
```

登録済み銀行口座の一覧を取得します。

---

## get_deposits / get_withdrawals

```python
client.get_deposits(count, before, after) -> list[dict]
client.get_withdrawals(count, before, after, message_id) -> list[dict]
```

入金・出金履歴を取得します。

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

出金を行います。二段階認証が必要な場合は `code` を指定してください。

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

新規注文を発注します。

---

## cancel_child_order

```python
client.cancel_child_order(
    product_code: str,
    child_order_id: str | None = None,
    child_order_acceptance_id: str | None = None,
) -> None
```

注文をキャンセルします。

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

特殊注文（IFD/OCO/IFDOCO）を発注します。

---

## cancel_parent_order / cancel_all_child_orders

```python
client.cancel_parent_order(product_code, parent_order_id, parent_order_acceptance_id) -> None
client.cancel_all_child_orders(product_code: str) -> None
```

親注文・全注文をキャンセルします。

---

## get_child_orders / get_parent_orders / get_parent_order

```python
client.get_child_orders(product_code, count, before, after, child_order_state, ...) -> list[dict]
client.get_parent_orders(product_code, count, before, after, parent_order_state) -> list[dict]
client.get_parent_order(parent_order_id, parent_order_acceptance_id) -> dict
```

注文の一覧・詳細を取得します。

---

## get_my_executions

```python
client.get_my_executions(product_code, count, before, after, child_order_id, child_order_acceptance_id) -> list[dict]
```

自分の約定一覧を取得します。

---

## get_balance_history

```python
client.get_balance_history(currency_code: str = "JPY", count, before, after) -> list[dict]
```

残高履歴を取得します。

---

## get_positions

```python
client.get_positions(product_code: str = "FX_BTC_JPY") -> list[dict]
```

建玉の一覧を取得します。

---

## get_collateral_history

```python
client.get_collateral_history(count, before, after) -> list[dict]
```

証拠金の変動履歴を取得します。

---

## get_trading_commission

```python
client.get_trading_commission(product_code: str) -> dict
```

取引手数料を取得します。
