import unittest
from crypto import HitBTCExchange, print_json, Market
import configparser
import datetime as dt
import requests_mock
import crypto.hitbtc.sample_responses as responses
from crypto.hitbtc.mock import mock_adapter


def set_up(mock=True):
    config = configparser.ConfigParser(allow_no_value=True)
    config.read('../crypto/config.ini')
    c = config['hitbtc']
    exchange = HitBTCExchange(c['BaseUrl'], c['Key'], c['Secret'], c['Symbols'].split(','), mock)
    return exchange


def check_params(ut, data):
    for param in data.keys():
        ut.assertIn(param, ut.expected_params)
    for param in ut.expected_params:
        ut.assertIn(param, data.keys())


class TestAPICurrencies(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.expected_params = ["id", "fullName", "crypto", "payinEnabled", "payinPaymentId", "payinConfirmations",
                                "payoutEnabled", "payoutIsPaymentId", "transferEnabled"]

    def test_currencies_all(self):
        status, data = self.e._currencies()
        # print_json(data)
        check_params(self, data[0])

    def test_currencies_one(self):
        status, data = self.e._currencies('BTC')
        print_json(data)
        self.assertEqual(status, 200)

    def tearDown(self):
        self.e.session.close()


class TestAPISymbols(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.expected_params = ["id", "baseCurrency", "quoteCurrency", "quantityIncrement", "tickSize",
                                "takeLiquidityRate", "provideLiquidityRate", "feeCurrency"]

    def test_symbols_all(self):
        status, data = self.e._symbols()
        # print_json(data)
        check_params(self, data[0])

    def test_symbols_one_by_one(self):
        for s in self.e.symbols:
            status, data = self.e._symbols(s)
            # print_json(data)
            self.assertEqual(status, 200)

    def tearDown(self):
        self.e.session.close()


class TestAPITickers(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.expected_params = ["ask", "bid", "last", "open", "low", "high", "volume", "volumeQuote", "timestamp",
                                "symbol"]

    def test_symbols_all(self):
        status, data = self.e._tickers()
        # print_json(data)
        check_params(self, data[0])

    def test_symbols_one_by_one(self):
        for s in self.e.symbols:
            status, data = self.e._tickers(s)
            self.assertEqual(status, 200)

    def tearDown(self):
        self.e.session.close()


class TestAPITrades(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.expected_params = ["id", "price", "quantity", "side", "timestamp"]

    def test_trades_no_params(self):
        status, data = self.e._trades(self.e.symbols[0])
        # print_json(data)
        check_params(self, data[0])

    def test_trades_with_params(self):
        time1 = (dt.datetime.now() - dt.timedelta(seconds=3)).isoformat()
        status, data = self.e._trades(self.e.symbols[0], _from=time1, limit=2)
        # print_json(data)
        self.assertEqual(len(data), 2)

    def tearDown(self):
        self.e.session.close()


class TestAPIOrderbook(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.expected_params = ["price", "size"]

    def test_orderbook(self):
        status, data = self.e._orderbook(self.e.symbols[0])
        self.assertSetEqual(set(data.keys()), {"ask", "bid"})
        # print_json(data)
        check_params(self, data["ask"][0])

    def tearDown(self):
        self.e.session.close()


class TestAPICandles(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.expected_params = ["timestamp", "open", "close", "min", "max", "volume", "volumeQuote"]

    def test_candles_no_params(self):
        status, data = self.e._candles(self.e.symbols[0])
        # print_json(data)
        check_params(self, data[0])

    def test_trades_with_params(self):
        status, data = self.e._candles(self.e.symbols[0], limit=7, period='D1')
        # print_json(data)
        self.assertEqual(len(data), 7)
        check_params(self, data[0])

    def tearDown(self):
        self.e.session.close()


class TestAPIBalances(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.expected_params = ["currency", "available", "reserved"]

    def test_balances(self):
        status, data = self.e._trading_balance()
        # print_json(list([d for d in data if d['available'] != "0"]))
        check_params(self, data[0])

    def tearDown(self):
        self.e.session.close()


class TestAPIOrder(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.expected_params = ["id", "clientOrderId", "symbol", "side", "status", "type", "timeInForce",
                                "quantity", "price", "cumQuantity", "createdAt", "updatedAt"]

    def test_blank_order(self):
        status, data = self.e._order_create(symbol="ETHBTC", side="buy", quantity=0, price=0)
        print_json(data)
        # check_params(self, data[0])

    def test_order_fok(self):
        # order
        status, data = self.e._order_create(symbol="ETHBTC", side="buy", quantity=1, price=.0001, timeInForce='FOK')
        check_params(self, data)
        print_json(data)
        # check for orders
        status, data = self.e._orders_active()
        print_json(data)
        self.assertEqual(len(data), 0)

    @unittest.skip('')
    def test_order_sell_fok(self):
        # order
        status, data = self.e._order_create(symbol="ETHBTC", side="sell", quantity=.01, price=.5)
        print_json(data)
        check_params(self, data)
        # check for orders
        status, data = self.e._orders_active()
        print_json(data)
        self.assertEqual(len(data), 0)

    def test_order_gtc_and_cancel_all(self):
        # order
        status, data = self.e._order_create(symbol="ETHBTC", side="buy", quantity=1, price=.0001)
        check_params(self, data)
        print_json(data)
        # check for orders
        status, data = self.e._orders_active()
        print_json(data)
        self.assertEqual(len(data), 1)
        # cancel orders
        status, data = self.e._orders_cancel()
        print_json(data)
        self.assertEqual(status, 200)
        # make sure it was canceled
        status, data = self.e._orders_active()
        print_json(data)
        self.assertEqual(len(data), 0)

    def test_order_gtc_and_cancel_by_id(self):
        # order
        status, data = self.e._order_create(symbol="ETHBTC", side="buy", quantity=1, price=.0001)
        check_params(self, data)
        clientOrderId = data['clientOrderId']
        print_json(data)
        # check for order
        status, data = self.e._order_active(clientOrderId)
        self.assertEqual(status, 200)
        # cancel order
        status, data = self.e._order_cancel(clientOrderId)
        print_json(data)
        self.assertEqual(status, 200)
        # make sure it was canceled
        status, data = self.e._orders_active()
        print_json(data)
        self.assertEqual(len(data), 0)

    def test_cancel_orders_all(self):
        status, data = self.e._orders_cancel()
        print_json(data)
        # check_params(self, data[0])

    def test_history(self):
        status, data = self.e._history_orders("ETHBTC", )
        print_json(data)
        # check_params(self, data[0])

    def test_history_with_params(self):
        time1 = (dt.datetime.now() - dt.timedelta(days=60)).isoformat()
        status, data = self.e._history_orders("LTCBTC", _from=time1)
        print_json(data)

    def tearDown(self):
        self.e.session.close()


class TestTicker(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)

    def test_ticker(self):
        tickers = self.e.ticker()
        print(tickers)


class TestMarketTrades(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)

    def test_market_trades(self):
        mk = Market('ETH', 'BTC', 'ETHBTC')
        trades = self.e.market_trades(mk)
        print(trades)


class TestOrders(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)

    def test_orders(self):
        orders = self.e.orders()
        print(orders)


class TestBid(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.sample = responses.bid_res

    def test_bid(self):
        mk = Market('ETH', 'BTC', 'ETHBTC')
        order = self.e.bid(mk, rate=.0001, quantity=.001)
        print(order)
        self.e._orders_cancel('ETHBTC')


@unittest.skip('')
class TestAsk(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=True)
        self.sample = responses.ask_res

    def test_ask(self):
        mk = Market('ETH', 'BTC', 'ETHBTC')
        order = self.e.ask(mk, rate=0, quantity=0)
        print(order)


class TestCancel(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.sample = responses.cancel_mul_res

    def test_cancel_by_id(self):
        try:
            mk = Market('ETH', 'BTC', 'ETHBTC')
            order = self.e.bid(mk, rate=.0001, quantity=.001)
            print(order)
            cancelled = self.e.cancel(order_id=order.order_id)
            print(cancelled)
        finally:
            self.e.cancel(all=True)

    def test_cancel_by_market(self):
        mk = Market('ETH', 'BTC', 'ETHBTC')
        cancelled = self.e.cancel(market=mk)
        print(cancelled)

    def test_cancel_all(self):
        cancelled = self.e.cancel(all=True)
        print(cancelled)


class TestBalance(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.sample = responses.balance_res

    def test_balance(self):
        balances = self.e.balance()
        print(vars(balances['BTC']))


class TestOrderBook(unittest.TestCase):
    def setUp(self):
        self.e = set_up(mock=False)
        self.sample = responses.orderbook_res

    def test_balance(self):
        mk = Market('ETH', 'BTC', 'ETHBTC')
        orderbook = self.e.order_book(mk)
        print(vars(orderbook.asks[0]))

# #
# if __name__ == '__main__':
#     unittest.main()
#
