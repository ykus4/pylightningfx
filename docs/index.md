# bitflyerpy

Python client for [bitFlyer Lightning API](https://lightning.bitflyer.com/docs).

## Installation

```bash
pip install bitflyerpy
```

## Quick Start

```python
from bitflyerpy import Client

# Public API (no authentication required)
client = Client()
ticker = client.get_ticker("BTC_JPY")
print(ticker["ltp"])  # 最終取引価格

# Private API
client = Client(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
balance = client.get_balance()
print(balance)
```

## Features

- Full coverage of [HTTP Public API](api/public.md)
- Full coverage of [HTTP Private API](api/private.md)
- Zero external dependencies (stdlib only)
- HMAC-SHA256 authentication built-in
