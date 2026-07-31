# Configuration

Pass `retry` and `rate_limits` to a client constructor to tune how requests are
retried and paced. `RateLimitState` is what the client reports back about
bitFlyer's own counters, via the `rate_limit` property.

::: pylightningfx.RetryPolicy

::: pylightningfx.RateLimits

::: pylightningfx.RateLimitState
