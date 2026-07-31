# 設定

クライアントのコンストラクタに `retry` と `rate_limits` を渡すと、リクエストのリトライ方法と
送信ペースを調整できます。`RateLimitState` は bitFlyer 側のカウンタをクライアントが
`rate_limit` プロパティで報告するためのものです。

::: pylightningfx.RetryPolicy

::: pylightningfx.RateLimits

::: pylightningfx.RateLimitState
