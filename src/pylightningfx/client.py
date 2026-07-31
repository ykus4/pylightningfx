"""The synchronous client."""

from .private import PrivateAPI
from .public import PublicAPI


class Client(PublicAPI, PrivateAPI):
    """bitFlyer Lightning API client.

    Exposes every Public and Private HTTP endpoint as a method. The
    constructor arguments are listed below; the key and secret are only
    needed for Private endpoints.

    Prefer the context manager, or call [`close()`][pylightningfx.Client.close] yourself, so the
    connection pool does not outlive its use::

        with Client() as client:
            print(client.get_ticker(ProductCode.FX_BTC_JPY).ltp)

        with Client(api_key, api_secret) as client:
            ack = client.send_child_order(
                ProductCode.BTC_JPY, ChildOrderType.LIMIT, Side.BUY, 0.001, price=5_000_000
            )
            client.cancel_child_order(
                ProductCode.BTC_JPY, child_order_acceptance_id=ack.child_order_acceptance_id
            )

    Instances are safe to share between threads: the underlying
    `httpx.Client` is thread-safe and the rate limiter is locked.

    For streaming market data and order events see
    [`RealtimeClient`][pylightningfx.RealtimeClient], and for ``asyncio`` see
    [`AsyncClient`][pylightningfx.AsyncClient].
    """
