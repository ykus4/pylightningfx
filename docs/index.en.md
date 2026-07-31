# pylightningfx

Python client for the [bitFlyer Lightning API](https://lightning.bitflyer.com/docs).

Two HTTP clients — `Client` and `AsyncClient` — cover every Public and Private
endpoint and return validated Pydantic models. Two WebSocket clients —
`RealtimeClient` and `AsyncRealtimeClient` — cover the streaming Realtime API.

## Installation

```bash
pip install pylightningfx
```

## Quick start

Public endpoints need no credentials; Private endpoints take an API key and
secret. Use the context manager so the connection pool is closed for you.

```python
from pylightningfx import ChildOrderType, Client, ProductCode, Side

with Client() as client:
    ticker = client.get_ticker(ProductCode.FX_BTC_JPY)
    print(ticker.ltp)

with Client(api_key, api_secret) as client:
    ack = client.send_child_order(
        ProductCode.BTC_JPY, ChildOrderType.LIMIT, Side.BUY, 0.001, price=5_000_000
    )
    print(ack.child_order_acceptance_id)
```

## Streaming

Subscribe to any number of channels on one connection and iterate the messages.
Payloads arrive parsed into the same models the HTTP clients return.

```python
from pylightningfx import ProductCode, RealtimeClient, channels

with RealtimeClient() as rt:
    rt.subscribe(channels.ticker(ProductCode.FX_BTC_JPY))
    for message in rt.listen():
        print(message.channel, message.data.ltp)
```

The `asyncio` twin is the same shape with `await` and `async for`:

```python
import asyncio

from pylightningfx import AsyncRealtimeClient, ProductCode, channels


async def main() -> None:
    async with AsyncRealtimeClient() as rt:
        await rt.subscribe(channels.executions(ProductCode.BTC_JPY))
        async for message in rt.listen():
            for trade in message.data:
                print(trade.price, trade.size)


asyncio.run(main())
```

## Where to go next

- [Clients](api/client.md) — the HTTP clients and every endpoint method.
- [Realtime](api/realtime.md) — WebSocket clients and channel names.
- [Models](api/models.md) — the response models.
- [Configuration](api/config.md) — retries and client-side rate limiting.
- [Errors](api/errors.md) — the exception hierarchy.
- [Enums](api/enums.md) — product codes, order types, states.
