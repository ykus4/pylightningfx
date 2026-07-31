# クライアント

2 種類の HTTP クライアントです。どちらも Public / Private の全エンドポイントをメソッドとして
公開し、[モデル](models.md) に記載のモデルを返します。コンストラクタ引数、`rate_limit`、
クローズ処理とコンテキストマネージャーは内部のエンジン由来で、以下に併記されています。

::: pylightningfx.Client
    options:
      inherited_members: true

::: pylightningfx.AsyncClient
    options:
      inherited_members: true
