import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.bitflyer.com"


class Client:
    """bitFlyer Lightning API client.

    Args:
        api_key: API key (required for Private API).
        api_secret: API secret (required for Private API).
    """

    def __init__(self, api_key: str = "", api_secret: str = "") -> None:
        self._api_key = api_key
        self._api_secret = api_secret

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        private: bool = False,
    ) -> Any:
        url = BASE_URL + path
        body_str = json.dumps(body) if body else ""

        if params:
            url += "?" + urlencode(params)

        headers: dict[str, str] = {"Content-Type": "application/json"}

        if private:
            timestamp = str(int(time.time()))
            query = "?" + urlencode(params) if params else ""
            sign_text = timestamp + method + path + query + body_str
            sign = hmac.new(
                self._api_secret.encode(),
                sign_text.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["ACCESS-KEY"] = self._api_key
            headers["ACCESS-TIMESTAMP"] = timestamp
            headers["ACCESS-SIGN"] = sign

        req = Request(
            url,
            data=body_str.encode() if body_str else None,
            headers=headers,
            method=method,
        )
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())

    def _get(self, path: str, params: dict[str, Any] | None = None, private: bool = False) -> Any:
        return self._request("GET", path, params=params, private=private)

    def _post(self, path: str, body: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, body=body, private=True)

    # ------------------------------------------------------------------
    # HTTP Public API
    # ------------------------------------------------------------------

    def get_markets(self) -> list[dict]:
        """GET /v1/getmarkets — マーケットの一覧"""
        return self._get("/v1/getmarkets")

    def get_board(self, product_code: str = "BTC_JPY") -> dict:
        """GET /v1/getboard — 板情報"""
        return self._get("/v1/getboard", {"product_code": product_code})

    def get_ticker(self, product_code: str = "BTC_JPY") -> dict:
        """GET /v1/getticker — Ticker"""
        return self._get("/v1/getticker", {"product_code": product_code})

    def get_executions(
        self,
        product_code: str = "BTC_JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[dict]:
        """GET /v1/getexecutions — 約定履歴"""
        params: dict[str, Any] = {"product_code": product_code}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after
        return self._get("/v1/getexecutions", params)

    def get_board_state(self, product_code: str = "BTC_JPY") -> dict:
        """GET /v1/getboardstate — 板の状態"""
        return self._get("/v1/getboardstate", {"product_code": product_code})

    def get_health(self, product_code: str = "BTC_JPY") -> dict:
        """GET /v1/gethealth — 取引所の状態"""
        return self._get("/v1/gethealth", {"product_code": product_code})

    def get_funding_rate(self, product_code: str) -> dict:
        """GET /v1/getfundingrate — ファンディングレート"""
        return self._get("/v1/getfundingrate", {"product_code": product_code})

    def get_funding_rate_history(
        self,
        product_code: str,
        count: int | None = None,
        from_: str | None = None,
        to: str | None = None,
    ) -> list[dict]:
        """GET /v1/getfundingratehistory — ファンディングレート履歴"""
        params: dict[str, Any] = {"product_code": product_code}
        if count is not None:
            params["count"] = count
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        return self._get("/v1/getfundingratehistory", params)

    def get_corporate_leverage(self) -> dict:
        """GET /v1/getcorporateleverage — 法人アカウント最大レバレッジ"""
        return self._get("/v1/getcorporateleverage")

    def get_chats(self, from_date: str | None = None) -> list[dict]:
        """GET /v1/getchats — チャット"""
        params: dict[str, Any] = {}
        if from_date is not None:
            params["from_date"] = from_date
        return self._get("/v1/getchats", params or None)

    # ------------------------------------------------------------------
    # HTTP Private API
    # ------------------------------------------------------------------

    def get_permissions(self) -> list[str]:
        """GET /v1/me/getpermissions — APIキーの権限を取得"""
        return self._get("/v1/me/getpermissions", private=True)

    def get_balance(self) -> list[dict]:
        """GET /v1/me/getbalance — 資産残高を取得"""
        return self._get("/v1/me/getbalance", private=True)

    def get_collateral(self) -> dict:
        """GET /v1/me/getcollateral — 証拠金の状態を取得"""
        return self._get("/v1/me/getcollateral", private=True)

    def get_collateral_accounts(self) -> list[dict]:
        """GET /v1/me/getcollateralaccounts — 通貨別証拠金を取得"""
        return self._get("/v1/me/getcollateralaccounts", private=True)

    def get_addresses(self) -> list[dict]:
        """GET /v1/me/getaddresses — 預入用アドレス取得"""
        return self._get("/v1/me/getaddresses", private=True)

    def get_coin_ins(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[dict]:
        """GET /v1/me/getcoinins — 仮想通貨預入履歴"""
        params: dict[str, Any] = {}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after
        return self._get("/v1/me/getcoinins", params or None, private=True)

    def get_coin_outs(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[dict]:
        """GET /v1/me/getcoinouts — 仮想通貨送付履歴"""
        params: dict[str, Any] = {}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after
        return self._get("/v1/me/getcoinouts", params or None, private=True)

    def get_bank_accounts(self) -> list[dict]:
        """GET /v1/me/getbankaccounts — 銀行口座一覧取得"""
        return self._get("/v1/me/getbankaccounts", private=True)

    def get_deposits(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[dict]:
        """GET /v1/me/getdeposits — 入金履歴"""
        params: dict[str, Any] = {}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after
        return self._get("/v1/me/getdeposits", params or None, private=True)

    def withdraw(
        self,
        currency_code: str,
        bank_account_id: int,
        amount: int,
        code: str | None = None,
    ) -> dict:
        """POST /v1/me/withdraw — 出金"""
        body: dict[str, Any] = {
            "currency_code": currency_code,
            "bank_account_id": bank_account_id,
            "amount": amount,
        }
        if code is not None:
            body["code"] = code
        return self._post("/v1/me/withdraw", body)

    def get_withdrawals(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        message_id: str | None = None,
    ) -> list[dict]:
        """GET /v1/me/getwithdrawals — 出金履歴"""
        params: dict[str, Any] = {}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after
        if message_id is not None:
            params["message_id"] = message_id
        return self._get("/v1/me/getwithdrawals", params or None, private=True)

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
        body: dict[str, Any] = {
            "product_code": product_code,
            "child_order_type": child_order_type,
            "side": side,
            "size": size,
            "minute_to_expire": minute_to_expire,
            "time_in_force": time_in_force,
        }
        if price is not None:
            body["price"] = price
        return self._post("/v1/me/sendchildorder", body)

    def cancel_child_order(
        self,
        product_code: str,
        child_order_id: str | None = None,
        child_order_acceptance_id: str | None = None,
    ) -> None:
        """POST /v1/me/cancelchildorder — 注文をキャンセルする"""
        body: dict[str, Any] = {"product_code": product_code}
        if child_order_id is not None:
            body["child_order_id"] = child_order_id
        elif child_order_acceptance_id is not None:
            body["child_order_acceptance_id"] = child_order_acceptance_id
        self._post("/v1/me/cancelchildorder", body)

    def send_parent_order(
        self,
        parameters: list[dict[str, Any]],
        order_method: str = "SIMPLE",
        minute_to_expire: int = 43200,
        time_in_force: str = "GTC",
    ) -> dict:
        """POST /v1/me/sendparentorder — 新規の親注文を出す（特殊注文）"""
        body: dict[str, Any] = {
            "order_method": order_method,
            "minute_to_expire": minute_to_expire,
            "time_in_force": time_in_force,
            "parameters": parameters,
        }
        return self._post("/v1/me/sendparentorder", body)

    def cancel_parent_order(
        self,
        product_code: str,
        parent_order_id: str | None = None,
        parent_order_acceptance_id: str | None = None,
    ) -> None:
        """POST /v1/me/cancelparentorder — 親注文をキャンセルする"""
        body: dict[str, Any] = {"product_code": product_code}
        if parent_order_id is not None:
            body["parent_order_id"] = parent_order_id
        elif parent_order_acceptance_id is not None:
            body["parent_order_acceptance_id"] = parent_order_acceptance_id
        self._post("/v1/me/cancelparentorder", body)

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
    ) -> list[dict]:
        """GET /v1/me/getchildorders — 注文の一覧を取得"""
        params: dict[str, Any] = {"product_code": product_code}
        for key, val in [
            ("count", count),
            ("before", before),
            ("after", after),
            ("child_order_state", child_order_state),
            ("child_order_id", child_order_id),
            ("child_order_acceptance_id", child_order_acceptance_id),
            ("parent_order_id", parent_order_id),
        ]:
            if val is not None:
                params[key] = val
        return self._get("/v1/me/getchildorders", params, private=True)

    def get_parent_orders(
        self,
        product_code: str = "BTC_JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        parent_order_state: str | None = None,
    ) -> list[dict]:
        """GET /v1/me/getparentorders — 親注文の一覧を取得"""
        params: dict[str, Any] = {"product_code": product_code}
        for key, val in [
            ("count", count),
            ("before", before),
            ("after", after),
            ("parent_order_state", parent_order_state),
        ]:
            if val is not None:
                params[key] = val
        return self._get("/v1/me/getparentorders", params, private=True)

    def get_parent_order(
        self,
        parent_order_id: str | None = None,
        parent_order_acceptance_id: str | None = None,
    ) -> dict:
        """GET /v1/me/getparentorder — 親注文の詳細を取得"""
        params: dict[str, Any] = {}
        if parent_order_id is not None:
            params["parent_order_id"] = parent_order_id
        elif parent_order_acceptance_id is not None:
            params["parent_order_acceptance_id"] = parent_order_acceptance_id
        return self._get("/v1/me/getparentorder", params, private=True)

    def get_my_executions(
        self,
        product_code: str = "BTC_JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
        child_order_id: str | None = None,
        child_order_acceptance_id: str | None = None,
    ) -> list[dict]:
        """GET /v1/me/getexecutions — 約定の一覧を取得"""
        params: dict[str, Any] = {"product_code": product_code}
        for key, val in [
            ("count", count),
            ("before", before),
            ("after", after),
            ("child_order_id", child_order_id),
            ("child_order_acceptance_id", child_order_acceptance_id),
        ]:
            if val is not None:
                params[key] = val
        return self._get("/v1/me/getexecutions", params, private=True)

    def get_balance_history(
        self,
        currency_code: str = "JPY",
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[dict]:
        """GET /v1/me/getbalancehistory — 残高履歴を取得"""
        params: dict[str, Any] = {"currency_code": currency_code}
        for key, val in [("count", count), ("before", before), ("after", after)]:
            if val is not None:
                params[key] = val
        return self._get("/v1/me/getbalancehistory", params, private=True)

    def get_positions(self, product_code: str = "FX_BTC_JPY") -> list[dict]:
        """GET /v1/me/getpositions — 建玉の一覧を取得"""
        return self._get("/v1/me/getpositions", {"product_code": product_code}, private=True)

    def get_collateral_history(
        self,
        count: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> list[dict]:
        """GET /v1/me/getcollateralhistory — 証拠金の変動履歴を取得"""
        params: dict[str, Any] = {}
        for key, val in [("count", count), ("before", before), ("after", after)]:
            if val is not None:
                params[key] = val
        return self._get("/v1/me/getcollateralhistory", params or None, private=True)

    def get_trading_commission(self, product_code: str) -> dict:
        """GET /v1/me/gettradingcommission — 取引手数料を取得"""
        return self._get(
            "/v1/me/gettradingcommission", {"product_code": product_code}, private=True
        )
