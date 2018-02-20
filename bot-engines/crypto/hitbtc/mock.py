import requests_mock
import re
import json
import random
import string
import datetime as dt
import crypto.hitbtc.sample_responses as responses
from urllib.parse import parse_qs


class Mocker(object):
    CURRENCIES = ['BTC', 'ETH', 'LTC', 'ETC']
    SYMBOLS = ['ETHBTC', 'LTCBTC', 'ETCBTC']

    def __init__(self):
        self.active_orders = []
        self.wallet = [self.random_balance(c) for c in Mocker.CURRENCIES]
        self.values = {s: random.uniform(.0001, .9) for s in Mocker.SYMBOLS}
        self.trades = {s: [] for s in Mocker.SYMBOLS}

    @staticmethod
    def random_balance(currency):
        return {"currency": currency, "available": random.uniform(0, 100), "reserved": random.uniform(0, 100)}

    def orders(self, request, context):
        for _ in range(random.randint(0, len(self.active_orders))):
            # randomly turn 'complete' some orders and turn into trades
            o = random.choice(self.active_orders)
            self.active_orders.remove(o)
            self.trades[o['symbol']].append(self.to_trade(o))
            self.trades[o['symbol']] = self.trades[o['symbol']][-5:]
        return json.dumps(self.active_orders)

    def order(self, request, context):
        try:
            params = parse_qs(request._request.body)
            response = {
                "id": 0,
                "clientOrderId": ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(32)),
                "symbol": params['symbol'][0],
                "side": params['side'][0],
                "status": "new",
                "type": "limit",
                "timeInForce": "GTC",
                "quantity": params['quantity'][0],
                "price": params['price'][0],
                "cumQuantity": "0.000",
                "createdAt": dt.datetime.utcnow().isoformat(),
                "updatedAt": dt.datetime.utcnow().isoformat()
            }
            self.active_orders.append(response)
            return json.dumps(response)
        except:
            return responses.bid_res

    def balances(self, request, context):
        for b in self.wallet:
            b['available'] += random.uniform(-5, 5)
            if b['available'] < 0:
                b['available'] = 0
        return json.dumps(self.wallet)

    def orderbook(self, request, context):
        try:
            symbol = request._request.url.split('/')[-1]
            self.values[symbol] += random.uniform(-.00005, .00005)

            if self.values[symbol] < .0001:
                self.values[symbol] = random.uniform(.0001, .9)

            response = {"ask": [], "bid": []}
            ask = bid = self.values[symbol]
            for _ in range(10):
                ask += random.uniform(.00001, self.values[symbol]/100)
                bid -= random.uniform(.00001, self.values[symbol]/100)
                response['ask'].append({"price": ask, "size": random.uniform(.001, 100)})
                response['bid'].append({"price": bid, "size": random.uniform(.001, 100)})
            return json.dumps(response)
        except:
            return responses.bid_res

    def ticker(self, request, context):
        symbol = request._request.url.split('/')[-1]
        if symbol != 'ticker' and symbol != '':
            self.values[symbol] += random.uniform(-.00005, .00005)
            response = {
                "ask": self.values[symbol] + random.uniform(.00001, self.values[symbol] / 100),
                "bid": self.values[symbol] - random.uniform(.00001, self.values[symbol] / 100),
                "last": self.values[symbol],
                "open": "0.047800",
                "low": "0.047052",
                "high": "0.051679",
                "volume": "36456.720",
                "volumeQuote": "1782.625000",
                "timestamp": dt.datetime.utcnow().isoformat(),
                "symbol": symbol
            }
            return json.dumps(response)
        else:
            responses = []
            for symbol in Mocker.SYMBOLS:
                self.values[symbol] += random.uniform(-.00005, .00005)
                response = {
                    "ask": self.values[symbol] + random.uniform(.00001, self.values[symbol]/100),
                    "bid": self.values[symbol] - random.uniform(.00001, self.values[symbol]/100),
                    "last": self.values[symbol],
                    "open": "0.047800",
                    "low": "0.047052",
                    "high": "0.051679",
                    "volume": "36456.720",
                    "volumeQuote": "1782.625000",
                    "timestamp": dt.datetime.utcnow().isoformat(),
                    "symbol": symbol
                }
                responses.append(response)
            return json.dumps(responses)

    def trade_history(self, request, context):
        params = parse_qs(request._request.body)
        response = self.trades[params['symbol'][0]]
        return json.dumps(response)

    def to_trade(self, order):
        return {
            "id": 9535486,
            "clientOrderId": order['clientOrderId'],
            "orderId": random.randint(1, 999999),
            "symbol": order['symbol'],
            "side": order['side'],
            "quantity": order['quantity'],
            "price": order['price'],
            "fee": "0.000002775",
            "timestamp": dt.datetime.utcnow().isoformat()
        }

    def cancel(self, request, context):
        params = parse_qs(request._request.body)
        if params:
            self.active_orders = [o for o in self.active_orders if o['symbol'] != params['symbol'][0]]
        else:
            self.active_orders = []
        return "[]"

mock_adapter = requests_mock.Adapter()
mocker = Mocker()

matcher = re.compile('/public/ticker')
mock_adapter.register_uri('GET', matcher, text=mocker.ticker)

matcher = re.compile('/public/trades')
mock_adapter.register_uri('GET', matcher, text=responses.market_trades_res)

matcher = re.compile('/public/orderbook')
mock_adapter.register_uri('GET', matcher, text=mocker.orderbook)

matcher = re.compile('/trading/balance')
mock_adapter.register_uri('GET', matcher, text=mocker.balances)

matcher = re.compile('/history/trades')
mock_adapter.register_uri('GET', matcher, text=mocker.trade_history)

# matcher = re.compile('/trading/balance')
# mock_adapter.register_uri('GET', matcher, text=responses.error_res, status_code=400)

matcher = re.compile('/order/$')
mock_adapter.register_uri('GET', matcher, text=mocker.orders)

matcher = re.compile('/order')
mock_adapter.register_uri('POST', matcher, text=mocker.order)

matcher = re.compile('/order/.{10,}')
mock_adapter.register_uri('DELETE', matcher, text=responses.cancel_one_res)

matcher = re.compile('/order$')
mock_adapter.register_uri('DELETE', matcher, text=mocker.cancel)
