"""Channel names for the Realtime API.

Build names with these helpers rather than by hand. ``subscribe`` validates only
the channel *prefix*, so a typo in the product code — ``lightning_ticker_BTCJPY``
— is answered with ``result: true`` and then silently delivers nothing, forever.
"""

CHILD_ORDER_EVENTS = "child_order_events"
"""Your own order lifecycle events. Requires authentication."""

PARENT_ORDER_EVENTS = "parent_order_events"
"""Your own parent order lifecycle events. Requires authentication."""

PRIVATE_CHANNELS = frozenset({CHILD_ORDER_EVENTS, PARENT_ORDER_EVENTS})
"""Channels that can only be subscribed after a successful ``auth``."""


def board_snapshot(product_code: str) -> str:
    """Full order book snapshots, sent periodically.

    Delivery is throttled, and the ``bids``/``asks`` order is not guaranteed.
    """
    return f"lightning_board_snapshot_{product_code}"


def board(product_code: str) -> str:
    """Incremental order book updates.

    Each entry carries the new *total* size at that price; ``size: 0`` means the
    level is gone. Apply these on top of a [`board_snapshot`][pylightningfx.channels.board_snapshot]
    to maintain a
    local book.
    """
    return f"lightning_board_{product_code}"


def ticker(product_code: str) -> str:
    """Ticker updates.

    Throttled, so the ``ltp`` here can lag. Use [`executions`][pylightningfx.channels.executions] if
    you need
    every trade.
    """
    return f"lightning_ticker_{product_code}"


def executions(product_code: str) -> str:
    """Public trades, delivered in batches."""
    return f"lightning_executions_{product_code}"
