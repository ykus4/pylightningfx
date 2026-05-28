# Public API

認証不要で利用できるエンドポイントです。

## get_markets

```python
client.get_markets() -> list[dict]
```

マーケットの一覧を取得します。

**レスポンス例:**
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

指定したマーケットの板情報を取得します。

---

## get_ticker

```python
client.get_ticker(product_code: str = "BTC_JPY") -> dict
```

指定したマーケットの最新 Ticker を取得します。

| フィールド | 説明 |
|------------|------|
| `ltp` | 最終取引価格 |
| `best_bid` / `best_ask` | ベストビッド / アスク価格 |
| `volume` | 24 時間の取引量 |

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

約定履歴を取得します（過去 31 日分）。

---

## get_board_state

```python
client.get_board_state(product_code: str = "BTC_JPY") -> dict
```

板の状態（`health` と `state`）を取得します。

---

## get_health

```python
client.get_health(product_code: str = "BTC_JPY") -> dict
```

取引所の稼動状態を取得します。

---

## get_funding_rate

```python
client.get_funding_rate(product_code: str) -> dict
```

次回徴収・付与予定のファンディングレート授受率を取得します。`product_code` は必須（例: `FX_BTC_JPY`）。

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

過去のファンディングレート履歴を取得します。

---

## get_corporate_leverage

```python
client.get_corporate_leverage() -> dict
```

法人アカウントの最大レバレッジを取得します。

---

## get_chats

```python
client.get_chats(from_date: str | None = None) -> list[dict]
```

チャットの発言一覧を取得します。`from_date` を省略すると 5 日前からの発言を返します。
