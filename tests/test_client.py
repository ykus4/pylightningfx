import httpx

from bitflyerpy import Board, Client, Market, Ticker


def _client(response_data) -> Client:
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=response_data))
    client = Client()
    client._http = httpx.Client(base_url="https://api.bitflyer.com", transport=transport)
    return client


def test_get_markets():
    data = [{"product_code": "BTC_JPY", "market_type": "Spot"}]
    result = _client(data).get_markets()
    assert len(result) == 1
    assert isinstance(result[0], Market)
    assert result[0].product_code == "BTC_JPY"


def test_get_ticker():
    data = {
        "product_code": "BTC_JPY",
        "state": "RUNNING",
        "timestamp": "2015-07-08T02:50:59.97",
        "tick_id": 3579,
        "best_bid": 30000,
        "best_ask": 36640,
        "best_bid_size": 0.1,
        "best_ask_size": 5,
        "total_bid_depth": 15.13,
        "total_ask_depth": 20,
        "market_bid_size": 0,
        "market_ask_size": 0,
        "ltp": 31690,
        "volume": 16819.26,
        "volume_by_product": 6819.26,
    }
    result = _client(data).get_ticker("BTC_JPY")
    assert isinstance(result, Ticker)
    assert result.ltp == 31690


def test_get_board():
    data = {
        "mid_price": 33320,
        "bids": [{"price": 30000, "size": 0.1}],
        "asks": [{"price": 36640, "size": 5}],
    }
    result = _client(data).get_board()
    assert isinstance(result, Board)
    assert result.mid_price == 33320
    assert result.bids[0].price == 30000


def test_send_child_order():
    data = {"child_order_acceptance_id": "JRF20150707-050237-639234"}
    result = _client(data).send_child_order("BTC_JPY", "LIMIT", "BUY", 0.1, price=5_000_000)
    assert result["child_order_acceptance_id"] == "JRF20150707-050237-639234"
