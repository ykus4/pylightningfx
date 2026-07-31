# エラー

このライブラリが送出する例外はすべて `BitflyerError` を継承しているため、
`except BitflyerError` 一つですべて捕捉できます。`httpx` のトランスポート例外はラップされず、
そのまま伝播します。

::: pylightningfx.BitflyerError

::: pylightningfx.CredentialsError

::: pylightningfx.APIError

::: pylightningfx.RateLimitError

::: pylightningfx.RealtimeError
