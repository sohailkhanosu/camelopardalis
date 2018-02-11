import requests_mock
import re
import crypto.hitbtc.sample_responses as responses

mock_adapter = requests_mock.Adapter()

matcher = re.compile('/public/ticker')
mock_adapter.register_uri('GET', matcher, text=responses.ticker_res)

matcher = re.compile('/public/trades')
mock_adapter.register_uri('GET', matcher, text=responses.market_trades_res)

matcher = re.compile('/public/orderbook')
mock_adapter.register_uri('GET', matcher, text=responses.orderbook_res)

matcher = re.compile('/trading/balance')
mock_adapter.register_uri('GET', matcher, text=responses.balance_res)

# matcher = re.compile('/trading/balance')
# mock_adapter.register_uri('GET', matcher, text=responses.error_res, status_code=400)

matcher = re.compile('/order/$')
mock_adapter.register_uri('GET', matcher, text=responses.orders_res)

matcher = re.compile('/order')
mock_adapter.register_uri('POST', matcher, text=responses.bid_res)

matcher = re.compile('/order/.{10,}')
mock_adapter.register_uri('DELETE', matcher, text=responses.cancel_one_res)

matcher = re.compile('/order$')
mock_adapter.register_uri('DELETE', matcher, text=responses.cancel_mul_res)