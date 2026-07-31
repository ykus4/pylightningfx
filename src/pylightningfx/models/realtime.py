"""Models for the private Realtime API channels.

The public channels reuse the Public API models: ``lightning_board*`` delivers a
[`Board`][pylightningfx.models.public.Board], ``lightning_ticker_*`` a
[`Ticker`][pylightningfx.models.public.Ticker], and ``lightning_executions_*`` a list of
[`Execution`][pylightningfx.models.public.Execution].

Most fields below are optional because bitFlyer sends a different subset per
``event_type``; each one documents when it is present.
"""

from datetime import datetime

from pydantic import BaseModel

__all__ = ["ChildOrderEvent", "ParentOrderEvent"]


class ChildOrderEvent(BaseModel):
    """One lifecycle event for one of your orders.

    Delivered on the ``child_order_events`` channel. Watch ``event_type`` to
    decide which optional fields to read; see
    [`ChildOrderEventType`][pylightningfx.enums.ChildOrderEventType].
    """

    product_code: str
    child_order_id: str
    child_order_acceptance_id: str
    event_date: datetime
    event_type: str
    """``ORDER``, ``ORDER_FAILED``, ``CANCEL``, ``CANCEL_FAILED``, ``EXECUTION``
    or ``EXPIRE``."""

    child_order_type: str | None = None
    """``ORDER`` only."""
    expire_date: datetime | None = None
    """``ORDER`` and ``EXECUTION``."""
    reason: str | None = None
    """``ORDER_FAILED`` only: why the exchange rejected the order."""
    exec_id: int | None = None
    """``EXECUTION`` only."""
    side: str | None = None
    """``ORDER`` and ``EXECUTION``."""
    price: float | None = None
    """``ORDER``, ``EXECUTION``, ``CANCEL`` and ``EXPIRE``."""
    size: float | None = None
    """``ORDER``, ``EXECUTION``, ``CANCEL`` and ``EXPIRE``."""
    commission: float | None = None
    """``EXECUTION`` only."""
    sfd: float | None = None
    """``EXECUTION`` only: the Swap For Difference charge."""
    outstanding_size: float | None = None
    """``EXECUTION`` only: how much of the order is still unfilled."""


class ParentOrderEvent(BaseModel):
    """One lifecycle event for one of your parent orders.

    Delivered on the ``parent_order_events`` channel. See
    [`ParentOrderEventType`][pylightningfx.enums.ParentOrderEventType] for the ``event_type``
    values,
    which differ from the child order set: parent orders report ``TRIGGER`` and
    ``COMPLETE`` instead of ``CANCEL_FAILED`` and ``EXECUTION``.
    """

    product_code: str
    parent_order_id: str
    parent_order_acceptance_id: str
    event_date: datetime
    event_type: str
    """``ORDER``, ``ORDER_FAILED``, ``CANCEL``, ``TRIGGER``, ``COMPLETE`` or
    ``EXPIRE``."""

    parent_order_type: str | None = None
    """``ORDER`` only, e.g. ``STOP`` or ``IFD``."""
    reason: str | None = None
    """``ORDER_FAILED`` only."""
    child_order_type: str | None = None
    """``TRIGGER`` only: the order type of the child that fired."""
    parameter_index: int | None = None
    """``TRIGGER`` and ``COMPLETE``: which leg, 1-based."""
    child_order_acceptance_id: str | None = None
    """``TRIGGER`` and ``COMPLETE``: links to the resulting child order."""
    side: str | None = None
    """``TRIGGER`` only."""
    price: float | None = None
    """``TRIGGER`` only."""
    size: float | None = None
    """``TRIGGER`` only."""
    expire_date: datetime | None = None
    """``ORDER`` and ``TRIGGER``."""
