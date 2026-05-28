import hashlib
import hmac
import time
from typing import Any

import httpx

BASE_URL = "https://api.bitflyer.com"


def _build_params(**kwargs: Any) -> dict[str, Any] | None:
    params = {k: v for k, v in kwargs.items() if v is not None}
    return params or None


class HttpMixin:
    _api_key: str
    _api_secret: str
    _http: httpx.Client

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        private: bool = False,
    ) -> Any:
        headers: dict[str, str] = {}

        if private:
            timestamp = str(int(time.time()))
            query = "?" + httpx.QueryParams(params).encode() if params else ""
            body_str = httpx.Request("POST", "/", json=body).content.decode() if body else ""
            sign = hmac.new(
                self._api_secret.encode(),
                (timestamp + method + path + query + body_str).encode(),
                hashlib.sha256,
            ).hexdigest()
            headers = {
                "ACCESS-KEY": self._api_key,
                "ACCESS-TIMESTAMP": timestamp,
                "ACCESS-SIGN": sign,
            }

        resp = self._http.request(method, path, params=params, json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _get(
        self, path: str, params: dict[str, Any] | None = None, *, private: bool = False
    ) -> Any:
        return self._request("GET", path, params=params, private=private)

    def _post(self, path: str, body: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, body=body, private=True)
