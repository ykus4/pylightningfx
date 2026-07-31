"""The asyncio client."""

from .async_private import AsyncPrivateAPI
from .async_public import AsyncPublicAPI


class AsyncClient(AsyncPublicAPI, AsyncPrivateAPI):
    """Asyncio bitFlyer Lightning API client.

    The same surface as [`Client`][pylightningfx.Client], with every endpoint
    as a coroutine. Constructor arguments are listed below.

    Use it as an async context manager, or await [`aclose()`][pylightningfx.AsyncClient.aclose]::

        async with AsyncClient() as client:
            board, ticker = await asyncio.gather(
                client.get_board(ProductCode.FX_BTC_JPY),
                client.get_ticker(ProductCode.FX_BTC_JPY),
            )

    Concurrent calls on one instance share the connection pool and the
    client-side rate limiter, so fanning out with `asyncio.gather()` will be
    throttled as one budget rather than overrunning it.

    For streaming market data and order events see
    [`AsyncRealtimeClient`][pylightningfx.AsyncRealtimeClient].
    """
