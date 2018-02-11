import configparser
import abc
from .helpers import str_to_class, serialize_obj
import json
import random
from queue import Queue
import time
import threading
import os


class TradingBot(object):
    def __init__(self, name, exchange=None, strategy=None, config_path=None, mock=True):
        if config_path:
            config = configparser.ConfigParser(allow_no_value=True)
            fname = os.path.join(os.path.dirname(__file__), 'config.ini')
            config.read(fname)
            wrapper_class = str_to_class(config[name]['Wrapper'])
            strategy_class = str_to_class(config[name]['Strategy'])
            exchange = wrapper_class(config[name]['BaseUrl'], config[name]['Key'], config[name]['Secret'],
                                     config[name]['Symbols'].split(','), mock)
            strategy = strategy_class(exchange)
        self.name = name
        self.exchange = exchange
        self.strategy = strategy
        self.markets = {m.counter + '_' + m.base: m for m in list(map(self.exchange.to_market, self.exchange.symbols))}
        self.markets_on = {m: True for m in self.markets.keys()}
        self.msg_queue = Queue(maxsize=10)

    def run(self):
        bot_thread = threading.Thread(target=self.work)
        bot_thread.daemon = True
        bot_thread.start()

        while True:
            self.pull()

    def work(self):
        while True:
            try:
                if not self.msg_queue.empty():
                    msg = self.msg_queue.get()
                    for k,v in msg.items():
                        self.markets_on[k] = (v == 'on')
                new_orders = self.execute_strategy()
                self.report()
                time.sleep(5)
            except Exception as e:
                self.push(e, 'error')
                time.sleep(5)
                # send error msg to backend, cancel orders if necessary
                pass

    def execute_strategy(self):
        new_orders = []
        for m in [market for market, is_on in self.markets_on.items() if is_on]:
            res = self.strategy.trade(self.markets[m])
            if res:
                new_orders.append(res)
        return new_orders

    def report(self):
        # send data to backend via stdout
        balance = self.exchange.balance()
        self.push(balance, 'balance')
        active_orders = self.exchange.orders()
        self.push(active_orders, 'active_orders')
        status = {
            'strategy': str(self.strategy),
            'markets': self.markets_on
        }
        self.push(status, 'status')

    def pull(self):
        # pull commands from backend via stdin e.g. {"ETH_BTC": "off"}
        stream = input()
        try:
            msg = json.loads(stream)
            self.msg_queue.put(msg)
        except json.JSONDecodeError as e:
            self.push(e, "error")

    def push(self, data, type):
        payload = {
            'exchange': self.name,
            'type': type,
            'data': data,
            'nonce': ''.join([str(random.randint(0, 9)) for _ in range(10)])
        }
        print(json.dumps(payload, default=serialize_obj), flush=True)


class Exchange(abc.ABC):
    @abc.abstractmethod
    def __init__(self, base_url, key, secret, symbols, mock=True):
        self.base_url = base_url
        if mock:
            self.base_url = self.base_url.replace("https://", "mock://")
        self.key = key
        self.secret = secret
        self.symbols = symbols

    @abc.abstractmethod
    def bid(self, market, rate, quantity):
        pass

    @abc.abstractmethod
    def ask(self, market, rate, quantity):
        pass

    @abc.abstractmethod
    def cancel(self, order_id=None, market=None, all=False):
        pass

    @abc.abstractmethod
    def orders(self, market=None):
        pass

    @abc.abstractmethod
    def balance(self):
        pass

    @abc.abstractmethod
    def order_book(self, market):
        pass

    @abc.abstractmethod
    def ticker(self):
        pass

    @abc.abstractmethod
    def market_trades(self, market):
        pass


class Strategy(object):
    def __init__(self, exchange):
        self.exchange = exchange

    @abc.abstractmethod
    def trade(self, market):
        pass


class BasicStrategy(Strategy):
    def __init__(self, exchange):
        super().__init__(exchange)

    def __str__(self):
        return "Basic"

    def analyze_market(self, market):
        data = self.exchange.order_book(market)
        # do math
        return None

    def trade(self, market):
        math = self.analyze_market(market)
        # make a decision/quote based on math
        # res = self.exchange.bid(market=market, rate=0, quantity=0)
        res = None
        return res
