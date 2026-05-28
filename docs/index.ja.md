# pylightningfx

[bitFlyer Lightning API](https://lightning.bitflyer.com/docs) の Python クライアントです。

## インストール

```bash
pip install pylightningfx
```

## クイックスタート

```python
from pylightningfx import Client

# Public API（認証不要）
client = Client()
ticker = client.get_ticker("BTC_JPY")
print(ticker["ltp"])  # 最終取引価格

# Private API
client = Client(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
balance = client.get_balance()
print(balance)
```

## 特徴

- [HTTP Public API](api/public.md) を完全網羅
- [HTTP Private API](api/private.md) を完全網羅
- 外部依存ゼロ（標準ライブラリのみ）
- HMAC-SHA256 認証を内蔵
