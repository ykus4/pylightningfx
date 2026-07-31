"""Sync/async mirror parity, enforced across every endpoint.

``async_public.py`` and ``async_private.py`` are hand-maintained mirrors of their
sync counterparts. A missing ``await``, a mistyped path or a dropped parameter in
one of the less-used methods would otherwise sit there uncaught, so this module
derives the endpoint list by introspection and drives *all* of them through both
clients, asserting the two produce byte-identical requests.

Because the list is introspected rather than written out, a newly added endpoint
is covered the moment it exists.
"""

import contextlib
import inspect
from typing import Any

import pytest

from pylightningfx import (
    AsyncClient,
    AsyncPrivateAPI,
    AsyncPublicAPI,
    Client,
    ParentOrderParameter,
    PrivateAPI,
    PublicAPI,
)

from .conftest import async_client, ok, sync_client

# Values good enough to build a request with. Keyed by parameter name, since the
# annotations are all plain `str`/`float` and carry no hint of what is expected.
ARGUMENTS: dict[str, Any] = {
    "product_code": "FX_BTC_JPY",
    "child_order_type": "LIMIT",
    "side": "BUY",
    "size": 0.01,
    "currency_code": "JPY",
    "bank_account_id": 1234,
    "amount": 10_000,
    "parameters": [
        ParentOrderParameter(
            product_code="FX_BTC_JPY",
            condition_type="STOP",
            side="SELL",
            size=0.01,
            trigger_price=9_000_000,
        )
    ],
}


def endpoint_names() -> list[str]:
    """Every public endpoint method, taken from the sync mixins."""
    names: set[str] = set()
    for mixin in (PublicAPI, PrivateAPI):
        names.update(
            name
            for name, value in vars(mixin).items()
            if not name.startswith("_") and inspect.isfunction(value)
        )
    return sorted(names)


def required_arguments(method: Any) -> list[Any]:
    """Positional arguments for a method, one per parameter with no default."""
    args = []
    for name, parameter in inspect.signature(method).parameters.items():
        if name == "self" or parameter.default is not inspect.Parameter.empty:
            continue
        if name not in ARGUMENTS:
            raise AssertionError(
                f"no test value for required parameter {name!r}; add it to ARGUMENTS"
            )
        args.append(ARGUMENTS[name])
    return args


def describe(request: Any) -> tuple[str, str, str, bytes]:
    """The parts of a request that must match between sync and async."""
    return (request.method, request.url.path, str(request.url.params), request.content)


def test_the_mixins_expose_the_same_endpoints() -> None:
    """Neither mirror may drift by gaining or losing a method."""
    sync = {n for n in dir(Client) if not n.startswith("_")} - {"close"}
    asyn = {n for n in dir(AsyncClient) if not n.startswith("_")} - {"aclose"}
    assert sync == asyn

    for sync_mixin, async_mixin in ((PublicAPI, AsyncPublicAPI), (PrivateAPI, AsyncPrivateAPI)):
        sync_methods = {n for n in vars(sync_mixin) if not n.startswith("_")}
        async_methods = {n for n in vars(async_mixin) if not n.startswith("_")}
        assert sync_methods == async_methods, f"{async_mixin.__name__} drifted"


def test_every_async_endpoint_is_a_coroutine() -> None:
    for name in endpoint_names():
        method = getattr(AsyncClient, name)
        assert inspect.iscoroutinefunction(method), f"{name} is not async"


@pytest.mark.parametrize("name", endpoint_names())
async def test_sync_and_async_build_identical_requests(name: str) -> None:
    """Same arguments in, same bytes on the wire out.

    The response is deliberately unusable for most endpoints, so parsing it may
    raise. That is fine and even useful: the parse line still executes, and the
    assertion here is about the request the mirror produced.
    """
    args = required_arguments(getattr(Client, name))

    sync, sync_api = sync_client(ok([]), authed=True)
    with sync, contextlib.suppress(Exception):
        getattr(sync, name)(*args)

    asyn, async_api = async_client(ok([]), authed=True)
    async with asyn:
        with contextlib.suppress(Exception):
            await getattr(asyn, name)(*args)

    assert sync_api.count == 1, f"{name} sent no request"
    assert async_api.count == 1, f"{name} sent no request"
    assert describe(sync_api.request) == describe(async_api.request)


@pytest.mark.parametrize("name", endpoint_names())
async def test_async_endpoints_return_what_sync_returns(name: str) -> None:
    """For the endpoints an empty list satisfies, the parsed results must match."""
    args = required_arguments(getattr(Client, name))

    sync, _ = sync_client(ok([]), authed=True)
    with sync:
        try:
            expected = getattr(sync, name)(*args)
        except Exception:
            pytest.skip(f"{name} cannot be satisfied by an empty list")

    asyn, _ = async_client(ok([]), authed=True)
    async with asyn:
        assert await getattr(asyn, name)(*args) == expected
