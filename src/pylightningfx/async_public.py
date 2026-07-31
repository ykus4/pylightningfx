"""Public API endpoints, which need no authentication. (async variant)"""

from ._engine import AsyncEngine
from ._params import build_params
from .enums import ProductCode
from .models.public import (
    Board,
    BoardState,
    Chat,
    CorporateLeverage,
    Execution,
    FundingRate,
    FundingRateHistory,
    Health,
    Market,
    Ticker,
)


class AsyncPublicAPI(AsyncEngine):
    """Market data endpoints.

    Mixed into [`AsyncClient`][pylightningfx.AsyncClient]; not meant to be instantiated on
    its own.

    Endpoints that return a history take ``count``, ``before`` and ``after``.
    ``count`` caps the number of records, default 100 and maximum 500. ``before``
    and ``after`` bound the ``id`` field exclusively, so paging backwards means
    passing the lowest ``id`` you have seen as ``before``.
    """

    async def get_markets(self) -> list[Market]:
        """List the available markets.

        Wraps ``GET /v1/getmarkets``.
        """
        return [Market.model_validate(m) for m in await self._get("/v1/getmarkets")]

    async def get_board(self, product_code: str = ProductCode.BTC_JPY) -> Board:
        """Fetch the order book.

        Wraps ``GET /v1/getboard``.

        Args:
            product_code: Market to query.
        """
        return Board.model_validate(await self._get("/v1/getboard", {"product_code": product_code}))

    async def get_ticker(self, product_code: str = ProductCode.BTC_JPY) -> Ticker:
        """Fetch the ticker.

        Wraps ``GET /v1/getticker``.

        Args:
            product_code: Market to query.
        """
        return Ticker.model_validate(
            await self._get("/v1/getticker", {"product_code": product_code})
        )

    async def get_executions(
        self,
        product_code: str = ProductCode.BTC_JPY,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[Execution]:
        """List recent public trades, newest first.

        Wraps ``GET /v1/getexecutions``.

        Args:
            product_code: Market to query.
            count: Maximum records to return.
            before: Return only trades with a lower ``id``.
            after: Return only trades with a higher ``id``.
        """
        data = await self._get(
            "/v1/getexecutions",
            build_params(product_code=product_code, count=count, before=before, after=after),
        )
        return [Execution.model_validate(e) for e in data]

    async def get_board_state(self, product_code: str = ProductCode.BTC_JPY) -> BoardState:
        """Fetch the order book state.

        Wraps ``GET /v1/getboardstate``. Use this rather than
        [`get_health()`][pylightningfx.AsyncClient.get_health]
        to decide whether orders are being accepted right now.

        Args:
            product_code: Market to query.
        """
        return BoardState.model_validate(
            await self._get("/v1/getboardstate", {"product_code": product_code})
        )

    async def get_health(self, product_code: str = ProductCode.BTC_JPY) -> Health:
        """Fetch exchange health.

        Wraps ``GET /v1/gethealth``.

        Args:
            product_code: Market to query.
        """
        return Health.model_validate(
            await self._get("/v1/gethealth", {"product_code": product_code})
        )

    async def get_funding_rate(self, product_code: str = ProductCode.FX_BTC_JPY) -> FundingRate:
        """Fetch the current funding rate.

        Wraps ``GET /v1/getfundingrate``. Only perpetual markets have one.

        Args:
            product_code: Perpetual market to query.
        """
        return FundingRate.model_validate(
            await self._get("/v1/getfundingrate", {"product_code": product_code})
        )

    async def get_funding_rate_history(
        self,
        product_code: str = ProductCode.FX_BTC_JPY,
        count: int | None = None,
        from_: str | None = None,
        to: str | None = None,
    ) -> list[FundingRateHistory]:
        """List settled funding rates.

        Wraps ``GET /v1/getfundingratehistory``.

        Args:
            product_code: Perpetual market to query.
            count: Maximum records to return.
            from_: Inclusive start date, ``YYYY-MM-DD``. Sent as ``from``, which
                is a Python keyword, hence the trailing underscore.
            to: Inclusive end date, ``YYYY-MM-DD``.
        """
        data = await self._get(
            "/v1/getfundingratehistory",
            build_params(product_code=product_code, count=count, from_=from_, to=to),
        )
        return [FundingRateHistory.model_validate(r) for r in data]

    async def get_corporate_leverage(self) -> CorporateLeverage:
        """Fetch the maximum leverage available to corporate accounts.

        Wraps ``GET /v1/getcorporateleverage``.
        """
        return CorporateLeverage.model_validate(await self._get("/v1/getcorporateleverage"))

    async def get_chats(self, from_date: str | None = None) -> list[Chat]:
        """List recent chat room messages.

        Wraps ``GET /v1/getchats``.

        Args:
            from_date: ISO 8601 timestamp; only messages after it are returned.
                Defaults to the last five days.
        """
        data = await self._get("/v1/getchats", build_params(from_date=from_date))
        return [Chat.model_validate(c) for c in data]
