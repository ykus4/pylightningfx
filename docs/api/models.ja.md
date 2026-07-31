# モデル

各エンドポイントは生の辞書ではなく Pydantic モデルを返します。そのためフィールドは
検証済みで、日時は `datetime` として受け取れ、エディタの補完も効きます。すべて
パッケージのルートからインポートできます:

```python
from pylightningfx import Board, ChildOrder, Ticker
```

`product_code` や `side`、`child_order_state` などのフィールドは、意図的に enum では
なく `str` として定義しています。bitFlyer は予告なく銘柄や状態値を追加するため、
閉じた enum にすると正当なレスポンスを弾いてしまうからです。既知の値は
[Enums](enums.md) を参照してください。

なお、以下の説明文（docstring）は英語で記述されています。

## Public API

::: pylightningfx.models.public
    options:
      heading_level: 3
      show_if_no_docstring: true

## Private API

::: pylightningfx.models.private
    options:
      heading_level: 3
      show_if_no_docstring: true

## Realtime API

配信チャンネルのうち公開系は上記のモデルをそのまま再利用します。専用のモデルを
持つのは、自分の注文イベントを流すプライベートチャンネルだけです。

::: pylightningfx.models.realtime
    options:
      heading_level: 3
      show_if_no_docstring: true
