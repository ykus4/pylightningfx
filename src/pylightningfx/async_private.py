"""Private API endpoints, which require an API key and secret. (async variant)"""

from collections.abc import Sequence
from typing import Any

from ._engine import AsyncEngine
from ._params import build_params
from .enums import OrderMethod, ProductCode, TimeInForce
from .models.private import (
    Address,
    Balance,
    BalanceHistory,
    BankAccount,
    ChildOrder,
    ChildOrderResponse,
    CoinIn,
    CoinOut,
    Collateral,
    CollateralAccount,
    CollateralHistory,
    Deposit,
    MyExecution,
    ParentOrder,
    ParentOrderDetail,
    ParentOrderParameter,
    ParentOrderResponse,
    Position,
    TradingCommission,
    Withdrawal,
    WithdrawResponse,
)


def _legs(parameters: Sequence[ParentOrderParameter | dict[str, Any]]) -> list[dict[str, Any]]:
    """Serialise parent order legs, dropping unset optional fields.

    Model legs and dict legs are treated identically — a key whose value is
    ``None`` is omitted either way — so the two documented input forms really do
    produce the same request body.
    """
    legs: list[dict[str, Any]] = []
    for leg in parameters:
        raw = leg.model_dump() if isinstance(leg, ParentOrderParameter) else dict(leg)
        legs.append({key: value for key, value in raw.items() if value is not None})
    return legs


class AsyncPrivateAPI(AsyncEngine):
    """Account, order and history endpoints.

    Mixed into [`AsyncClient`][pylightningfx.AsyncClient]; not meant to be instantiated on
    its own. Every method here raises
    [`CredentialsError`][pylightningfx.CredentialsError] if the client was built without an
    ``api_key`` and ``api_secret``.

    Endpoints that return a history take ``count``, ``before`` and ``after``.
    ``count`` caps the number of records, default 100 and maximum 500. ``before``
    and ``after`` bound the ``id`` field exclusively.
    """

    async def get_permissions(self) -> list[str]:
        """List the endpoints this API key is allowed to call.

        Wraps ``GET /v1/me/getpermissions``.
        """
        return list(await self._get("/v1/me/getpermissions", private=True))

    async def get_balance(self) -> list[Balance]:
        """Fetch balances for every currency.

        Wraps ``GET /v1/me/getbalance``.
        """
        return [
            Balance.model_validate(b) for b in await self._get("/v1/me/getbalance", private=True)
        ]

    async def get_collateral(self) -> Collateral:
        """Fetch margin status for the account.

        Wraps ``GET /v1/me/getcollateral``.
        """
        return Collateral.model_validate(await self._get("/v1/me/getcollateral", private=True))

    async def get_collateral_accounts(self) -> list[CollateralAccount]:
        """Fetch collateral held per currency.

        Wraps ``GET /v1/me/getcollateralaccounts``.
        """
        data = await self._get("/v1/me/getcollateralaccounts", private=True)
        return [CollateralAccount.model_validate(a) for a in data]

    async def get_addresses(self) -> list[Address]:
        """List your crypto deposit addresses.

        Wraps ``GET /v1/me/getaddresses``.
        """
        return [
            Address.model_validate(a) for a in await self._get("/v1/me/getaddresses", private=True)
        ]

    async def get_coin_ins(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[CoinIn]:
        """List incoming crypto transfers.

        Wraps ``GET /v1/me/getcoinins``.
        """
        data = await self._get(
            "/v1/me/getcoinins",
            build_params(count=count, before=before, after=after),
            private=True,
        )
        return [CoinIn.model_validate(c) for c in data]

    async def get_coin_outs(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[CoinOut]:
        """List outgoing crypto transfers.

        Wraps ``GET /v1/me/getcoinouts``.
        """
        data = await self._get(
            "/v1/me/getcoinouts",
            build_params(count=count, before=before, after=after),
            private=True,
        )
        return [CoinOut.model_validate(c) for c in data]

    async def get_bank_accounts(self) -> list[BankAccount]:
        """List your registered bank accounts.

        Wraps ``GET /v1/me/getbankaccounts``.
        """
        data = await self._get("/v1/me/getbankaccounts", private=True)
        return [BankAccount.model_validate(b) for b in data]

    async def get_deposits(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[Deposit]:
        """List cash deposits.

        Wraps ``GET /v1/me/getdeposits``.
        """
        data = await self._get(
            "/v1/me/getdeposits",
            build_params(count=count, before=before, after=after),
            private=True,
        )
        return [Deposit.model_validate(d) for d in data]

    async def withdraw(
        self,
        currency_code: str,
        bank_account_id: int,
        amount: int,
        code: str | None = None,
    ) -> WithdrawResponse:
        """Withdraw cash to a registered bank account.

        Wraps ``POST /v1/me/withdraw``. This moves real money and cannot be
        undone. It is never retried automatically, whatever
        [`RetryPolicy`][pylightningfx.RetryPolicy] says, because a timed-out withdrawal
        may still have been accepted.

        Args:
            currency_code: Currency to withdraw, e.g. ``"JPY"``.
            bank_account_id: [`id`][pylightningfx.models.private.BankAccount.id] of the
                destination, from
                [`get_bank_accounts()`][pylightningfx.AsyncClient.get_bank_accounts].
            amount: Amount to withdraw.
            code: Two-factor confirmation code, if your account requires one.
        """
        return WithdrawResponse.model_validate(
            await self._post(
                "/v1/me/withdraw",
                build_params(
                    currency_code=currency_code,
                    bank_account_id=bank_account_id,
                    amount=amount,
                    code=code,
                ),
            )
        )

    async def get_withdrawals(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        message_id: str | None = None,
    ) -> list[Withdrawal]:
        """List cash withdrawals.

        Wraps ``GET /v1/me/getwithdrawals``.

        Args:
            count: Maximum records to return.
            before: Return only records with a lower ``id``.
            after: Return only records with a higher ``id``.
            message_id: Narrow to the withdrawal started by this
                [`message_id`][pylightningfx.models.private.WithdrawResponse.message_id].
        """
        data = await self._get(
            "/v1/me/getwithdrawals",
            build_params(count=count, before=before, after=after, message_id=message_id),
            private=True,
        )
        return [Withdrawal.model_validate(w) for w in data]

    async def send_child_order(
        self,
        product_code: str,
        child_order_type: str,
        side: str,
        size: float,
        price: float | None = None,
        minute_to_expire: int | None = None,
        time_in_force: str = TimeInForce.GTC,
    ) -> ChildOrderResponse:
        """Place an order.

        Wraps ``POST /v1/me/sendchildorder``. A successful call means the order
        was *accepted*, not filled; see
        [`ChildOrderResponse`][pylightningfx.models.private.ChildOrderResponse].

        Args:
            product_code: Market to trade.
            child_order_type: ``LIMIT`` or ``MARKET``. See
                [`ChildOrderType`][pylightningfx.enums.ChildOrderType].
            side: ``BUY`` or ``SELL``. See [`Side`][pylightningfx.enums.Side].
            size: Order quantity in the base asset.
            price: Limit price. Required for ``LIMIT``, ignored for ``MARKET``.
            minute_to_expire: Minutes until the order expires. Defaults to
                bitFlyer's own default of 43200, i.e. 30 days.
            time_in_force: ``GTC``, ``IOC`` or ``FOK``. See
                [`TimeInForce`][pylightningfx.enums.TimeInForce].
        """
        return ChildOrderResponse.model_validate(
            await self._post(
                "/v1/me/sendchildorder",
                build_params(
                    product_code=product_code,
                    child_order_type=child_order_type,
                    side=side,
                    size=size,
                    price=price,
                    minute_to_expire=minute_to_expire,
                    time_in_force=time_in_force,
                ),
            )
        )

    async def cancel_child_order(
        self,
        product_code: str = ProductCode.BTC_JPY,
        child_order_id: str | None = None,
        child_order_acceptance_id: str | None = None,
    ) -> None:
        """Cancel one order.

        Wraps ``POST /v1/me/cancelchildorder``, which answers with an empty body
        on success. Pass exactly one of the two identifiers.

        Args:
            product_code: Market the order is on.
            child_order_id: Exchange-assigned order id.
            child_order_acceptance_id: Acceptance id returned by
                [`send_child_order()`][pylightningfx.AsyncClient.send_child_order].
        """
        await self._post(
            "/v1/me/cancelchildorder",
            build_params(
                product_code=product_code,
                child_order_id=child_order_id,
                child_order_acceptance_id=child_order_acceptance_id,
            ),
        )

    async def send_parent_order(
        self,
        parameters: Sequence[ParentOrderParameter | dict[str, Any]],
        order_method: str = OrderMethod.SIMPLE,
        minute_to_expire: int | None = None,
        time_in_force: str = TimeInForce.GTC,
    ) -> ParentOrderResponse:
        """Place a conditional or multi-leg order.

        Wraps ``POST /v1/me/sendparentorder``.

        Args:
            parameters: The legs, as
                [`ParentOrderParameter`][pylightningfx.models.private.ParentOrderParameter]
                instances or plain
                dicts. ``SIMPLE`` and ``IFD`` take one and two legs
                respectively; ``OCO`` takes two and ``IFDOCO`` three.
            order_method: ``SIMPLE``, ``IFD``, ``OCO`` or ``IFDOCO``. See
                [`OrderMethod`][pylightningfx.enums.OrderMethod].
            minute_to_expire: Minutes until the order expires. Defaults to
                bitFlyer's own default of 43200, i.e. 30 days.
            time_in_force: ``GTC``, ``IOC`` or ``FOK``. See
                [`TimeInForce`][pylightningfx.enums.TimeInForce].
        """
        body: dict[str, Any] = {
            "order_method": order_method,
            "time_in_force": time_in_force,
            "parameters": _legs(parameters),
        }
        if minute_to_expire is not None:
            body["minute_to_expire"] = minute_to_expire
        return ParentOrderResponse.model_validate(await self._post("/v1/me/sendparentorder", body))

    async def cancel_parent_order(
        self,
        product_code: str = ProductCode.BTC_JPY,
        parent_order_id: str | None = None,
        parent_order_acceptance_id: str | None = None,
    ) -> None:
        """Cancel one parent order.

        Wraps ``POST /v1/me/cancelparentorder``, which answers with an empty body
        on success. Pass exactly one of the two identifiers.
        """
        await self._post(
            "/v1/me/cancelparentorder",
            build_params(
                product_code=product_code,
                parent_order_id=parent_order_id,
                parent_order_acceptance_id=parent_order_acceptance_id,
            ),
        )

    async def cancel_all_child_orders(self, product_code: str = ProductCode.BTC_JPY) -> None:
        """Cancel every open order on one market.

        Wraps ``POST /v1/me/cancelallchildorders``, which answers with an empty
        body on success.
        """
        await self._post("/v1/me/cancelallchildorders", {"product_code": product_code})

    async def get_child_orders(
        self,
        product_code: str = ProductCode.BTC_JPY,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        child_order_state: str | None = None,
        child_order_id: str | None = None,
        child_order_acceptance_id: str | None = None,
        parent_order_id: str | None = None,
    ) -> list[ChildOrder]:
        """List your orders.

        Wraps ``GET /v1/me/getchildorders``.

        Args:
            product_code: Market to query.
            count: Maximum records to return.
            before: Return only orders with a lower ``id``.
            after: Return only orders with a higher ``id``.
            child_order_state: Filter by state, e.g. ``"ACTIVE"`` for open
                orders. See [`ChildOrderState`][pylightningfx.enums.ChildOrderState].
            child_order_id: Narrow to one order by exchange id.
            child_order_acceptance_id: Narrow to one order by acceptance id.
            parent_order_id: Narrow to the children of one parent order.
        """
        data = await self._get(
            "/v1/me/getchildorders",
            build_params(
                product_code=product_code,
                count=count,
                before=before,
                after=after,
                child_order_state=child_order_state,
                child_order_id=child_order_id,
                child_order_acceptance_id=child_order_acceptance_id,
                parent_order_id=parent_order_id,
            ),
            private=True,
        )
        return [ChildOrder.model_validate(o) for o in data]

    async def get_parent_orders(
        self,
        product_code: str = ProductCode.BTC_JPY,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        parent_order_state: str | None = None,
    ) -> list[ParentOrder]:
        """List your parent orders.

        Wraps ``GET /v1/me/getparentorders``. The rows summarise each parent
        order; call [`get_parent_order()`][pylightningfx.AsyncClient.get_parent_order] for its legs.

        Args:
            product_code: Market to query.
            count: Maximum records to return.
            before: Return only orders with a lower ``id``.
            after: Return only orders with a higher ``id``.
            parent_order_state: Filter by state. See
                [`ParentOrderState`][pylightningfx.enums.ParentOrderState].
        """
        data = await self._get(
            "/v1/me/getparentorders",
            build_params(
                product_code=product_code,
                count=count,
                before=before,
                after=after,
                parent_order_state=parent_order_state,
            ),
            private=True,
        )
        return [ParentOrder.model_validate(o) for o in data]

    async def get_parent_order(
        self,
        parent_order_id: str | None = None,
        parent_order_acceptance_id: str | None = None,
    ) -> ParentOrderDetail:
        """Fetch one parent order together with its legs.

        Wraps ``GET /v1/me/getparentorder``. Pass exactly one of the two
        identifiers.
        """
        return ParentOrderDetail.model_validate(
            await self._get(
                "/v1/me/getparentorder",
                build_params(
                    parent_order_id=parent_order_id,
                    parent_order_acceptance_id=parent_order_acceptance_id,
                ),
                private=True,
            )
        )

    async def get_my_executions(
        self,
        product_code: str = ProductCode.BTC_JPY,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        child_order_id: str | None = None,
        child_order_acceptance_id: str | None = None,
    ) -> list[MyExecution]:
        """List your fills.

        Wraps ``GET /v1/me/getexecutions``. Named ``get_my_executions`` to keep
        it distinct from the public [`get_executions()`][pylightningfx.AsyncClient.get_executions].

        Args:
            product_code: Market to query.
            count: Maximum records to return.
            before: Return only fills with a lower ``id``.
            after: Return only fills with a higher ``id``.
            child_order_id: Narrow to the fills of one order.
            child_order_acceptance_id: Narrow to the fills of one order by
                acceptance id.
        """
        data = await self._get(
            "/v1/me/getexecutions",
            build_params(
                product_code=product_code,
                count=count,
                before=before,
                after=after,
                child_order_id=child_order_id,
                child_order_acceptance_id=child_order_acceptance_id,
            ),
            private=True,
        )
        return [MyExecution.model_validate(e) for e in data]

    async def get_balance_history(
        self,
        currency_code: str = "JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[BalanceHistory]:
        """List balance ledger entries for one currency.

        Wraps ``GET /v1/me/getbalancehistory``.
        """
        data = await self._get(
            "/v1/me/getbalancehistory",
            build_params(currency_code=currency_code, count=count, before=before, after=after),
            private=True,
        )
        return [BalanceHistory.model_validate(b) for b in data]

    async def get_positions(self, product_code: str = ProductCode.FX_BTC_JPY) -> list[Position]:
        """List open leveraged positions.

        Wraps ``GET /v1/me/getpositions``. Positions come back individually
        rather than netted.

        Args:
            product_code: Leveraged market to query.
        """
        data = await self._get("/v1/me/getpositions", {"product_code": product_code}, private=True)
        return [Position.model_validate(p) for p in data]

    async def get_collateral_history(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[CollateralHistory]:
        """List changes to your collateral.

        Wraps ``GET /v1/me/getcollateralhistory``.
        """
        data = await self._get(
            "/v1/me/getcollateralhistory",
            build_params(count=count, before=before, after=after),
            private=True,
        )
        return [CollateralHistory.model_validate(c) for c in data]

    async def get_trading_commission(
        self, product_code: str = ProductCode.BTC_JPY
    ) -> TradingCommission:
        """Fetch your commission rate for one market.

        Wraps ``GET /v1/me/gettradingcommission``.
        """
        return TradingCommission.model_validate(
            await self._get(
                "/v1/me/gettradingcommission", {"product_code": product_code}, private=True
            )
        )
