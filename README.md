# pylightningfx

Python client for the [bitFlyer Lightning API](https://lightning.bitflyer.com/docs).

[![PyPI](https://img.shields.io/pypi/v/pylightningfx)](https://pypi.org/project/pylightningfx/)
[![Python](https://img.shields.io/pypi/pyversions/pylightningfx)](https://pypi.org/project/pylightningfx/)
[![CI](https://github.com/ykus4/pylightningfx/actions/workflows/ci.yml/badge.svg)](https://github.com/ykus4/pylightningfx/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/ykus4/pylightningfx)](LICENSE)

**[Documentation](https://ykus4.github.io/pylightningfx)** · [日本語](https://ykus4.github.io/pylightningfx/ja)

- Every HTTP endpoint, Public and Private, with Pydantic response models
- `asyncio` support with an identical API surface
- The Realtime WebSocket API, with automatic reconnect and resubscribe
- Request signing, client-side rate limiting, and retries that never replay an order
- Fully typed, checked under `mypy --strict`

## Installation

```bash
pip install pylightningfx
```

Requires Python 3.13 or newer.

## Usage

### Market data

```python
from pylightningfx import Client, ProductCode

with Client() as client:
    ticker = client.get_ticker(ProductCode.FX_BTC_JPY)
    print(ticker.ltp, ticker.best_bid, ticker.best_ask)
```

### Trading

```python
from pylightningfx import ChildOrderType, Client, ProductCode, Side

with Client("YOUR_API_KEY", "YOUR_API_SECRET") as client:
    ack = client.send_child_order(
        ProductCode.BTC_JPY, ChildOrderType.LIMIT, Side.BUY, 0.001, price=5_000_000
    )
    print(ack.child_order_acceptance_id)

    for order in client.get_child_orders(ProductCode.BTC_JPY, child_order_state="ACTIVE"):
        print(order.child_order_id, order.outstanding_size)
```

### Streaming

```python
from pylightningfx import ProductCode, RealtimeClient, channels

with RealtimeClient() as rt:
    rt.subscribe(channels.executions(ProductCode.FX_BTC_JPY))
    for message in rt.listen():
        for trade in message.data:
            print(trade.exec_date, trade.side, trade.price, trade.size)
```

Subscribe to `channels.CHILD_ORDER_EVENTS` with credentials to stream your own
order events. The connection reconnects and resubscribes on its own if it drops.

### asyncio

```python
import asyncio

from pylightningfx import AsyncClient, ProductCode


async def main() -> None:
    async with AsyncClient() as client:
        board, ticker = await asyncio.gather(
            client.get_board(ProductCode.FX_BTC_JPY),
            client.get_ticker(ProductCode.FX_BTC_JPY),
        )
        print(board.mid_price, ticker.ltp)


asyncio.run(main())
```

`AsyncRealtimeClient` is the streaming equivalent.

## Notes on safety

Orders are real money, so a few defaults are deliberately conservative:

- **Retries never replay a write.** A 5xx or a timeout on `send_child_order` is
  ambiguous — the order may already be live — so only safe methods are retried by
  default. Opt in with `RetryPolicy(retry_unsafe_methods=True)` if you reconcile
  orders afterwards. HTTP 429 is always retried, since a rate-limited request
  never reached the matching engine.
- **`withdraw` is never retried**, whatever the policy says.
- **Rate limits are respected client-side.** The client tracks bitFlyer's 500-per-5-minutes
  general budget and the tighter 300-per-5-minutes order budget, and spreads bursts
  rather than collecting 429s. Configure with `RateLimits`, or pass
  `RateLimits.disabled()` to opt out.

Errors arrive as `APIError` carrying bitFlyer's numeric `status` and
`error_message`, not just an HTTP code.

See the [documentation](https://ykus4.github.io/pylightningfx) for the full API reference.
