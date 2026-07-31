# Errors

Every error raised by this library derives from `BitflyerError`, so a single
`except BitflyerError` catches all of them. `httpx` transport errors are not
wrapped and propagate as-is.

::: pylightningfx.BitflyerError

::: pylightningfx.CredentialsError

::: pylightningfx.APIError

::: pylightningfx.RateLimitError

::: pylightningfx.RealtimeError
