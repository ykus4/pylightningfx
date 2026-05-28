from typing import Any

from ._http import HttpMixin, _build_params
from .models.private import (
    Address,
    Balance,
    BalanceHistory,
    BankAccount,
    ChildOrder,
    CoinIn,
    CoinOut,
    Collateral,
    CollateralAccount,
    CollateralHistory,
    Deposit,
    MyExecution,
    ParentOrder,
    ParentOrderDetail,
    Position,
    TradingCommission,
    Withdrawal,
)


class PrivateAPI(HttpMixin):
    def get_permissions(self) -> list[str]:
        """GET /v1/me/getpermissions — APIキーの権限を取得"""
        return self._get("/v1/me/getpermissions", private=True)

    def get_balance(self) -> list[Balance]:
        """GET /v1/me/getbalance — 資産残高を取得"""
        return [Balance(**b) for b in self._get("/v1/me/getbalance", private=True)]

    def get_collateral(self) -> Collateral:
        """GET /v1/me/getcollateral — 証拠金の状態を取得"""
        return Collateral(**self._get("/v1/me/getcollateral", private=True))

    def get_collateral_accounts(self) -> list[CollateralAccount]:
        """GET /v1/me/getcollateralaccounts — 通貨別証拠金を取得"""
        return [
            CollateralAccount(**a) for a in self._get("/v1/me/getcollateralaccounts", private=True)
        ]

    def get_addresses(self) -> list[Address]:
        """GET /v1/me/getaddresses — 預入用アドレス取得"""
        return [Address(**a) for a in self._get("/v1/me/getaddresses", private=True)]

    def get_coin_ins(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[CoinIn]:
        """GET /v1/me/getcoinins — 仮想通貨預入履歴"""
        data = self._get(
            "/v1/me/getcoinins",
            _build_params(count=count, before=before, after=after),
            private=True,
        )
        return [CoinIn(**c) for c in data]

    def get_coin_outs(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[CoinOut]:
        """GET /v1/me/getcoinouts — 仮想通貨送付履歴"""
        data = self._get(
            "/v1/me/getcoinouts",
            _build_params(count=count, before=before, after=after),
            private=True,
        )
        return [CoinOut(**c) for c in data]

    def get_bank_accounts(self) -> list[BankAccount]:
        """GET /v1/me/getbankaccounts — 銀行口座一覧取得"""
        return [BankAccount(**b) for b in self._get("/v1/me/getbankaccounts", private=True)]

    def get_deposits(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[Deposit]:
        """GET /v1/me/getdeposits — 入金履歴"""
        data = self._get(
            "/v1/me/getdeposits",
            _build_params(count=count, before=before, after=after),
            private=True,
        )
        return [Deposit(**d) for d in data]

    def withdraw(
        self,
        currency_code: str,
        bank_account_id: int,
        amount: int,
        code: str | None = None,
    ) -> dict:
        """POST /v1/me/withdraw — 出金"""
        return self._post(
            "/v1/me/withdraw",
            _build_params(
                currency_code=currency_code,
                bank_account_id=bank_account_id,
                amount=amount,
                code=code,
            ),
        )

    def get_withdrawals(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        message_id: str | None = None,
    ) -> list[Withdrawal]:
        """GET /v1/me/getwithdrawals — 出金履歴"""
        data = self._get(
            "/v1/me/getwithdrawals",
            _build_params(count=count, before=before, after=after, message_id=message_id),
            private=True,
        )
        return [Withdrawal(**w) for w in data]

    def send_child_order(
        self,
        product_code: str,
        child_order_type: str,
        side: str,
        size: float,
        price: float | None = None,
        minute_to_expire: int = 43200,
        time_in_force: str = "GTC",
    ) -> dict:
        """POST /v1/me/sendchildorder — 新規注文を出す"""
        return self._post(
            "/v1/me/sendchildorder",
            _build_params(
                product_code=product_code,
                child_order_type=child_order_type,
                side=side,
                size=size,
                price=price,
                minute_to_expire=minute_to_expire,
                time_in_force=time_in_force,
            ),
        )

    def cancel_child_order(
        self,
        product_code: str,
        child_order_id: str | None = None,
        child_order_acceptance_id: str | None = None,
    ) -> None:
        """POST /v1/me/cancelchildorder — 注文をキャンセルする"""
        self._post(
            "/v1/me/cancelchildorder",
            _build_params(
                product_code=product_code,
                child_order_id=child_order_id,
                child_order_acceptance_id=child_order_acceptance_id,
            ),
        )

    def send_parent_order(
        self,
        parameters: list[dict[str, Any]],
        order_method: str = "SIMPLE",
        minute_to_expire: int = 43200,
        time_in_force: str = "GTC",
    ) -> dict:
        """POST /v1/me/sendparentorder — 新規の親注文を出す（特殊注文）"""
        return self._post(
            "/v1/me/sendparentorder",
            {
                "order_method": order_method,
                "minute_to_expire": minute_to_expire,
                "time_in_force": time_in_force,
                "parameters": parameters,
            },
        )

    def cancel_parent_order(
        self,
        product_code: str,
        parent_order_id: str | None = None,
        parent_order_acceptance_id: str | None = None,
    ) -> None:
        """POST /v1/me/cancelparentorder — 親注文をキャンセルする"""
        self._post(
            "/v1/me/cancelparentorder",
            _build_params(
                product_code=product_code,
                parent_order_id=parent_order_id,
                parent_order_acceptance_id=parent_order_acceptance_id,
            ),
        )

    def cancel_all_child_orders(self, product_code: str) -> None:
        """POST /v1/me/cancelallchildorders — すべての注文をキャンセルする"""
        self._post("/v1/me/cancelallchildorders", {"product_code": product_code})

    def get_child_orders(
        self,
        product_code: str = "BTC_JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        child_order_state: str | None = None,
        child_order_id: str | None = None,
        child_order_acceptance_id: str | None = None,
        parent_order_id: str | None = None,
    ) -> list[ChildOrder]:
        """GET /v1/me/getchildorders — 注文の一覧を取得"""
        data = self._get(
            "/v1/me/getchildorders",
            _build_params(
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
        return [ChildOrder(**o) for o in data]

    def get_parent_orders(
        self,
        product_code: str = "BTC_JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        parent_order_state: str | None = None,
    ) -> list[ParentOrder]:
        """GET /v1/me/getparentorders — 親注文の一覧を取得"""
        data = self._get(
            "/v1/me/getparentorders",
            _build_params(
                product_code=product_code,
                count=count,
                before=before,
                after=after,
                parent_order_state=parent_order_state,
            ),
            private=True,
        )
        return [ParentOrder(**o) for o in data]

    def get_parent_order(
        self,
        parent_order_id: str | None = None,
        parent_order_acceptance_id: str | None = None,
    ) -> ParentOrderDetail:
        """GET /v1/me/getparentorder — 親注文の詳細を取得"""
        return ParentOrderDetail(
            **self._get(
                "/v1/me/getparentorder",
                _build_params(
                    parent_order_id=parent_order_id,
                    parent_order_acceptance_id=parent_order_acceptance_id,
                ),
                private=True,
            )
        )

    def get_my_executions(
        self,
        product_code: str = "BTC_JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        child_order_id: str | None = None,
        child_order_acceptance_id: str | None = None,
    ) -> list[MyExecution]:
        """GET /v1/me/getexecutions — 約定の一覧を取得"""
        data = self._get(
            "/v1/me/getexecutions",
            _build_params(
                product_code=product_code,
                count=count,
                before=before,
                after=after,
                child_order_id=child_order_id,
                child_order_acceptance_id=child_order_acceptance_id,
            ),
            private=True,
        )
        return [MyExecution(**e) for e in data]

    def get_balance_history(
        self,
        currency_code: str = "JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[BalanceHistory]:
        """GET /v1/me/getbalancehistory — 残高履歴を取得"""
        data = self._get(
            "/v1/me/getbalancehistory",
            _build_params(currency_code=currency_code, count=count, before=before, after=after),
            private=True,
        )
        return [BalanceHistory(**b) for b in data]

    def get_positions(self, product_code: str = "FX_BTC_JPY") -> list[Position]:
        """GET /v1/me/getpositions — 建玉の一覧を取得"""
        return [
            Position(**p)
            for p in self._get("/v1/me/getpositions", {"product_code": product_code}, private=True)
        ]

    def get_collateral_history(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[CollateralHistory]:
        """GET /v1/me/getcollateralhistory — 証拠金の変動履歴を取得"""
        data = self._get(
            "/v1/me/getcollateralhistory",
            _build_params(count=count, before=before, after=after),
            private=True,
        )
        return [CollateralHistory(**c) for c in data]

    def get_trading_commission(self, product_code: str) -> TradingCommission:
        """GET /v1/me/gettradingcommission — 取引手数料を取得"""
        return TradingCommission(
            **self._get("/v1/me/gettradingcommission", {"product_code": product_code}, private=True)
        )
