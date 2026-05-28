import json
from unittest.mock import MagicMock, patch

from bitflyerpy import Client


def _mock_urlopen(response_data):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


@patch("bitflyerpy.client.urlopen")
def test_get_markets(mock_urlopen):
    data = [{"product_code": "BTC_JPY", "market_type": "Spot"}]
    mock_urlopen.return_value = _mock_urlopen(data)
    client = Client()
    result = client.get_markets()
    assert result == data


@patch("bitflyerpy.client.urlopen")
def test_get_ticker(mock_urlopen):
    data = {"product_code": "BTC_JPY", "ltp": 5000000}
    mock_urlopen.return_value = _mock_urlopen(data)
    client = Client()
    result = client.get_ticker("BTC_JPY")
    assert result["product_code"] == "BTC_JPY"


@patch("bitflyerpy.client.urlopen")
def test_get_board(mock_urlopen):
    data = {"mid_price": 5000000, "bids": [], "asks": []}
    mock_urlopen.return_value = _mock_urlopen(data)
    client = Client()
    result = client.get_board()
    assert "mid_price" in result


@patch("bitflyerpy.client.urlopen")
def test_send_child_order(mock_urlopen):
    data = {"child_order_acceptance_id": "JRF20150707-050237-639234"}
    mock_urlopen.return_value = _mock_urlopen(data)
    client = Client(api_key="key", api_secret="secret")
    result = client.send_child_order("BTC_JPY", "LIMIT", "BUY", 0.1, price=5000000)
    assert "child_order_acceptance_id" in result
