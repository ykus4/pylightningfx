# Clients

The two HTTP clients. Both expose every Public and Private endpoint as a method
and return the models documented under [Models](models.md). Constructor
arguments, `rate_limit` and the close/context-manager protocol come from the
underlying engine and are listed inline below.

::: pylightningfx.Client
    options:
      inherited_members: true

::: pylightningfx.AsyncClient
    options:
      inherited_members: true
