from ._http import HttpMixin, _build_params
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


class PublicAPI(HttpMixin):
    def get_markets(self) -> list[Market]:
        """GET /v1/getmarkets — マーケットの一覧"""
        return [Market(**m) for m in self._get("/v1/getmarkets")]

    def get_board(self, product_code: str = "BTC_JPY") -> Board:
        """GET /v1/getboard — 板情報"""
        return Board(**self._get("/v1/getboard", {"product_code": product_code}))

    def get_ticker(self, product_code: str = "BTC_JPY") -> Ticker:
        """GET /v1/getticker — Ticker"""
        return Ticker(**self._get("/v1/getticker", {"product_code": product_code}))

    def get_executions(
        self,
        product_code: str = "BTC_JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[Execution]:
        """GET /v1/getexecutions — 約定履歴"""
        data = self._get(
            "/v1/getexecutions",
            _build_params(product_code=product_code, count=count, before=before, after=after),
        )
        return [Execution(**e) for e in data]

    def get_board_state(self, product_code: str = "BTC_JPY") -> BoardState:
        """GET /v1/getboardstate — 板の状態"""
        return BoardState(**self._get("/v1/getboardstate", {"product_code": product_code}))

    def get_health(self, product_code: str = "BTC_JPY") -> Health:
        """GET /v1/gethealth — 取引所の状態"""
        return Health(**self._get("/v1/gethealth", {"product_code": product_code}))

    def get_funding_rate(self, product_code: str) -> FundingRate:
        """GET /v1/getfundingrate — ファンディングレート"""
        return FundingRate(**self._get("/v1/getfundingrate", {"product_code": product_code}))

    def get_funding_rate_history(
        self,
        product_code: str,
        count: int | None = None,
        from_: str | None = None,
        to: str | None = None,
    ) -> list[FundingRateHistory]:
        """GET /v1/getfundingratehistory — ファンディングレート履歴"""
        params = _build_params(product_code=product_code, count=count, to=to) or {}
        if from_ is not None:
            params["from"] = from_
        return [FundingRateHistory(**r) for r in self._get("/v1/getfundingratehistory", params)]

    def get_corporate_leverage(self) -> CorporateLeverage:
        """GET /v1/getcorporateleverage — 法人アカウント最大レバレッジ"""
        return CorporateLeverage(**self._get("/v1/getcorporateleverage"))

    def get_chats(self, from_date: str | None = None) -> list[Chat]:
        """GET /v1/getchats — チャット"""
        return [Chat(**c) for c in self._get("/v1/getchats", _build_params(from_date=from_date))]
