"""Query and body parameter construction."""

from typing import Any


def build_params(**kwargs: Any) -> dict[str, Any] | None:
    """Build a request parameter mapping from keyword arguments.

    Drops every ``None`` value, so callers can pass their optional arguments
    through unconditionally, and strips a single trailing underscore from each
    name. The underscore lets a method expose ``from_`` for bitFlyer's ``from``
    parameter without colliding with the Python keyword.

    Returns ``None`` when nothing is left, which both httpx and the signing code
    treat as "no query string" / "no body".
    """
    params = {k.removesuffix("_"): v for k, v in kwargs.items() if v is not None}
    return params or None
