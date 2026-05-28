# bitflyerpy

Python client for [bitFlyer Lightning API](https://lightning.bitflyer.com/docs).

[![PyPI](https://img.shields.io/pypi/v/bitflyerpy)](https://pypi.org/project/bitflyerpy/)
[![Python](https://img.shields.io/pypi/pyversions/bitflyerpy)](https://pypi.org/project/bitflyerpy/)
[![CI](https://github.com/ykus4/bitflyerpy/actions/workflows/ci.yml/badge.svg)](https://github.com/ykus4/bitflyerpy/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/ykus4/bitflyerpy)](LICENSE)

**[Documentation](https://ykus4.github.io/bitflyerpy)** | [English](https://ykus4.github.io/bitflyerpy) | [日本語](https://ykus4.github.io/bitflyerpy/ja)

## Features

- Full coverage of HTTP Public and Private API
- Zero external dependencies (stdlib only)
- HMAC-SHA256 authentication built-in

## Installation

```bash
pip install bitflyerpy
```

## Quick Start

```python
from bitflyerpy import Client

# Public API — no authentication required
client = Client()

ticker = client.get_ticker("BTC_JPY")
print(ticker["ltp"])  # Last traded price

board = client.get_board("BTC_JPY")
print(board["best_bid"], board["best_ask"])

# Private API
client = Client(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")

balance = client.get_balance()
order = client.send_child_order("BTC_JPY", "LIMIT", "BUY", size=0.1, price=5_000_000)
print(order["child_order_acceptance_id"])
```

## API Reference

See the full documentation at **[ykus4.github.io/bitflyerpy](https://ykus4.github.io/bitflyerpy)**.

| Category | Methods |
|----------|---------|
| Market data | `get_markets`, `get_board`, `get_ticker`, `get_executions`, `get_board_state`, `get_health` |
| CFD | `get_funding_rate`, `get_funding_rate_history`, `get_positions` |
| Account | `get_balance`, `get_collateral`, `get_addresses`, `get_permissions` |
| Orders | `send_child_order`, `cancel_child_order`, `send_parent_order`, `cancel_parent_order`, `cancel_all_child_orders` |
| History | `get_child_orders`, `get_parent_orders`, `get_my_executions`, `get_balance_history` |
| Funds | `withdraw`, `get_deposits`, `get_withdrawals`, `get_coin_ins`, `get_coin_outs` |

## License

MIT
