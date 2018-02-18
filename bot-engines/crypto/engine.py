import configparser
import abc
from .helpers import str_to_class, serialize_obj, print_json
import json
import random
from queue import Queue
import time
import threading
import os
import logging
import signal


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
        self.on = True
        self.work_thread = None
        signal.signal(signal.SIGINT, self.sig_handler)

    def run(self):
        self.work_thread = threading.Thread(target=self.work)
        self.work_thread.daemon = True
        self.work_thread.start()

        while True:
            self.pull()

    def work(self):
        while True:
            if not self.on:
                logging.info("Cancelling trades")
                self.exchange.cancel(all=True)
                return
            try:
                if not self.msg_queue.empty():
                    msg = self.msg_queue.get()
                    self.process_msg(msg)
                new_orders = self.execute_strategy()
                self.push(new_orders, "new_orders")
                self.report()
            except Exception as e:
                self.push(e, 'error')
                logging.info("Cancelling orders")
                self.exchange.cancel(all=True)
                raise e
            finally:
                time.sleep(2)

    def process_msg(self, msg):
        if msg['type'] == 'markets':
            for k, v in msg.items():
                self.markets_on[k] = (v == 'on')
        elif msg['type'] == 'pause':
            for k, v in msg.items():
                self.markets_on[k] = False

    def execute_strategy(self):
        new_orders = []
        for m in [market for market, is_on in self.markets_on.items() if is_on]:
            res = self.strategy.trade(self.markets[m])
            if res:
                new_orders.extend(res)
        return new_orders

    def report(self):
        # send market data to backend via stdout
        balance = self.exchange.balance()
        self.push(balance, 'balance')
        active_orders = self.exchange.orders()
        self.push(active_orders, 'active_orders')
        status = {
            'strategy': str(self.strategy),
            'markets': self.markets_on
        }
        self.push(status, 'status')
        orderbooks = {k: self.exchange.order_book(v) for k,v in self.markets.items()}
        self.push(orderbooks, 'orderbooks')
        trades = {k: self.exchange.trades(v) for k,v in self.markets.items()}
        self.push(trades, 'trades')

    def pull(self):
        # pull commands from backend via stdin e.g. {"type": "markets", "data": {"ETH_BTC": "off"}}
        stream = self.input_with_timeout(10)
        try:
            msg = json.loads(stream)
            if msg['type'] == 'ping':  # if heartbeat, immediately reply
                msg['type'] = 'pong'
                print(json.dumps(msg), flush=True)
            else:
                self.msg_queue.put(msg)
        except json.JSONDecodeError as e:
            self.push(e, "error")

    def push(self, data, type='Test'):
        payload = {
            'exchange': self.name,
            'type': type,
            'data': data,
            'nonce': ''.join([str(random.randint(0, 9)) for _ in range(10)])
        }
        print(json.dumps(payload, default=serialize_obj), flush=True)

    def input_with_timeout(self, timeout):
        # set signal handler
        signal.signal(signal.SIGALRM, self.sig_handler)
        signal.alarm(timeout)  # produce SIGALRM in `timeout` seconds
        try:
            return input()
        finally:
            signal.alarm(0)  # cancel alarm

    def sig_handler(self, signum, frame):
        if signum == signal.SIGALRM:
            logging.info("Input timed out, turning off bot")
        else:
            logging.info("Received SIGINT, turning off bot")
        self.on = False
        self.work_thread.join()
        raise SystemExit


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
    def ticker(self, market=None):
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
        ticker = self.exchange.ticker(market)
        best_ask = ticker.ask
        best_bid = ticker.bid
        last = ticker.last
        logging.info("best ask: {}".format(best_ask))
        logging.info("best bid: {}".format(best_bid))
        logging.info("last: {}".format(last))
        market_value = (best_ask + best_bid) / 2
        return market_value

    def trade(self, market):
        self.exchange.cancel(all=True)  # cancel previous orders
        spread = .004
        market_value = self.analyze_market(market)
        ask_quote = market_value + (spread / 2)
        bid_quote = market_value - (spread / 2)

        logging.info("market value: {}".format(market_value))
        logging.info("ask quote: {}".format(ask_quote))
        logging.info("bid quote: {}".format(bid_quote))

        try:
            new_orders = []
            bid = self.exchange.bid(market=market, rate=bid_quote, quantity=.001)
            ask = self.exchange.ask(market=market, rate=ask_quote, quantity=.001)
            for order in [bid, ask]:
                if order:
                    new_orders.append(order)
                    logging.info("Successfully placed {} order #{}".format(order.side, order.order_id))

            return new_orders
        except Exception as e:
            logging.warning('Order failed: "{}"'.format(e))
            self.exchange.cancel(all=True)
            raise e


