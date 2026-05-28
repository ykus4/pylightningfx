from typing import Any

import httpx

from ._http import BASE_URL
from .private import PrivateAPI
from .public import PublicAPI


class Client(PublicAPI, PrivateAPI):
    """bitFlyer Lightning API client.

    Args:
        api_key: API key (required for Private API).
        api_secret: API secret (required for Private API).
    """

    def __init__(self, api_key: str = "", api_secret: str = "") -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._http = httpx.Client(base_url=BASE_URL)

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_: Any) -> None:
        self._http.close()
