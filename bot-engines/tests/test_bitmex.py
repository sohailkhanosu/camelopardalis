import unittest
from crypto import TradingBot, print_json, Market
import configparser
import datetime as dt
import requests_mock
import crypto.hitbtc.sample_responses as responses
from crypto.hitbtc.mock import mock_adapter
from crypto.structs import *


def set_up():
    b = TradingBot('bitmex', config_path='config.ini', mock=False)
    exchange = b.exchange
    return exchange


class TestBid(unittest.TestCase):
    def setUp(self):
        self.e = set_up()
        self.sample = responses.bid_res

    def test_bid(self):
        mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
        order = self.e.bid(mk, rate=100, quantity=1)
        # print(vars(order))
        self.assertTrue(isinstance(order, Order))
        self.e._cancel_all()


class TestAsk(unittest.TestCase):
    def setUp(self):
        self.e = set_up()
        self.sample = responses.ask_res

    def test_ask(self):
        mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
        order = self.e.ask(mk, rate=1000000, quantity=1)
        # print(vars(order))
        self.assertTrue(isinstance(order, Order))
        self.e._cancel_all()


class TestCancel(unittest.TestCase):
    def setUp(self):
        self.e = set_up()
        self.sample = responses.cancel_mul_res

    def test_cancel_by_id(self):
        try:
            mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
            order = self.e.bid(mk, rate=100, quantity=1)
            # print(vars(order))
            cancelled = self.e.cancel(order_id=order.order_id)
            self.assertTrue(isinstance(cancelled, list))
            self.assertTrue(isinstance(cancelled[0], Order))
            # print(cancelled)
        finally:
            self.e.cancel(all=True)

    def test_cancel_by_market(self):
        mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
        self.e.bid(mk, rate=100, quantity=1)
        cancelled = self.e.cancel(market=mk)
        self.assertTrue(isinstance(cancelled, list))
        self.assertTrue(isinstance(cancelled[0], Order))
        # print(cancelled)

    def test_cancel_all(self):
        mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
        self.e.bid(mk, rate=100, quantity=1)
        cancelled = self.e.cancel(all=True)
        self.assertTrue(isinstance(cancelled[0], Order))
        # print(cancelled)


class TestOrders(unittest.TestCase):
    def setUp(self):
        self.e = set_up()

    def test_orders(self):
        mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
        self.e.bid(mk, rate=100, quantity=1)
        orders = self.e.orders()
        self.assertTrue(isinstance(orders, list))
        self.assertTrue(isinstance(orders[0], Order))
        # print(cancelled)


class TestBalance(unittest.TestCase):
    def setUp(self):
        self.e = set_up()
        self.sample = responses.balance_res

    def test_balance(self):
        balances = self.e.balance()
        # print(balances)
        self.assertIn("BTC", balances.keys())
        self.assertTrue(isinstance(balances['BTC'], Balance))


class TestOrderBook(unittest.TestCase):
    def setUp(self):
        self.e = set_up()
        self.sample = responses.orderbook_res

    def test_balance(self):
        mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
        orderbook = self.e.order_book(mk)
        # print(vars(orderbook.asks[0]))
        self.assertTrue(isinstance(orderbook, OrderBook))


class TestTicker(unittest.TestCase):
    def setUp(self):
        self.e = set_up()

    def test_ticker(self):
        mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
        ticker = self.e.ticker(mk)
        self.assertTrue(isinstance(ticker, Ticker))


class TestCandles(unittest.TestCase):
    def setUp(self):
        self.e = set_up()

    def test_candles(self):
        mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
        candles = self.e.candles(mk)
        # print(candles)
        self.assertTrue(isinstance(candles, list))
        self.assertTrue(isinstance(candles[0], Candle))


class TestPosition(unittest.TestCase):
    def setUp(self):
        self.e = set_up()

    def test_position(self):
        mk = Market('USD', 'BTC', 'XBTUSD', 1, 0, 0)
        position = self.e.position(mk)
        # print(position)
        self.assertTrue(isinstance(position, int))
