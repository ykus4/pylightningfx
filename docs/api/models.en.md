# Models

Every endpoint returns Pydantic models rather than raw dictionaries, so fields
are validated, timestamps arrive as `datetime`, and your editor can complete
them. All of them are importable from the package root:

```python
from pylightningfx import Board, ChildOrder, Ticker
```

Fields such as `product_code`, `side` and `child_order_state` are typed `str`
rather than as enums on purpose — bitFlyer adds products and state values without
warning, and a closed enum would reject a valid response. See
[Enums](enums.md) for the known values.

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

The public streaming channels reuse the models above. Only the private order
event channels have models of their own.

::: pylightningfx.models.realtime
    options:
      heading_level: 3
      show_if_no_docstring: true
