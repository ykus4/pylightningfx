# pylightningfx

[bitFlyer Lightning API](https://lightning.bitflyer.com/docs) の Python クライアントです。

HTTP クライアントは `Client` と `AsyncClient` の 2 つで、Public / Private の全エンドポイントに
対応し、検証済みの Pydantic モデルを返します。WebSocket クライアントは `RealtimeClient` と
`AsyncRealtimeClient` の 2 つで、ストリーミングの Realtime API に対応します。

## インストール

```bash
pip install pylightningfx
```

## クイックスタート

Public エンドポイントは認証不要です。Private エンドポイントには API キーとシークレットを渡します。
コネクションプールを確実に閉じるため、コンテキストマネージャーの利用を推奨します。

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

## ストリーミング

1 本の接続で任意の数のチャンネルを購読し、届いたメッセージを順に処理できます。
ペイロードは HTTP クライアントが返すものと同じモデルにパースされた状態で渡されます。

```python
from pylightningfx import ProductCode, RealtimeClient, channels

with RealtimeClient() as rt:
    rt.subscribe(channels.ticker(ProductCode.FX_BTC_JPY))
    for message in rt.listen():
        print(message.channel, message.data.ltp)
```

`asyncio` 版も同じ形で、`await` と `async for` を使います。

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

## 次に読むページ

- [クライアント](api/client.md) — HTTP クライアントと全エンドポイントメソッド。
- [Realtime](api/realtime.md) — WebSocket クライアントとチャンネル名。
- [モデル](api/models.md) — レスポンスモデル。
- [設定](api/config.md) — リトライとクライアント側のレート制限。
- [エラー](api/errors.md) — 例外の階層。
- [列挙型](api/enums.md) — プロダクトコード、注文種別、各種ステート。
