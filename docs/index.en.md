# pylightningfx

Python client for [bitFlyer Lightning API](https://lightning.bitflyer.com/docs).

## Installation

```bash
pip install pylightningfx
```

## Quick Start

```python
from pylightningfx import Client

# Public API (no authentication required)
client = Client()
ticker = client.get_ticker("BTC_JPY")
print(ticker["ltp"])  # Last traded price

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
