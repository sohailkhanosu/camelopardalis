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
import sys
import csv
import requests



class TradingBot(object):
    def __init__(self, name, exchange=None, strategy=None, config_path=None, mock=None):
        if config_path:
            try:
                config = configparser.ConfigParser(allow_no_value=True)
                fname = os.path.join(os.path.dirname(__file__), 'config.ini')
                config.read(fname)
                if mock is None:
                    mock = config[name].getboolean('Mock', fallback=True)
                wrapper_class = str_to_class(config[name]['Wrapper'])
                strategy_class = str_to_class(config[name]['Strategy'])
                self.minutes_to_timeout = int(config[name]['MinutesToTimeout'])
                symbols = config[name]['Symbols'].split(',')
                exchange = wrapper_class(config[name]['BaseUrl'], config[name]['Key'], config[name]['Secret'],
                                         symbols, mock)
                market_configs = {s: config[name][s].split(',') for s in symbols}
                if config[name]['Strategy'] == 'SignalStrategy':
                    indicators = {ind: str_to_class(ind) for ind in config[name]['indicators'].split(',')}
                    strategy = strategy_class(exchange, market_configs, indicators)
                else:
                    strategy = strategy_class(exchange, market_configs)
            except Exception as e:
                logging.exception("Error reading config file")
                sys.exit(0)
        self.name = name
        self.exchange = exchange
        self.strategy = strategy

        self.markets = {m.counter + '_' + m.base: m for m in list(map(self.exchange.to_market, self.exchange.symbols))}
        self.markets_on = {m: True for m in self.markets.keys()}

        self.msg_queue = Queue(maxsize=10)
        self.turn_off = threading.Event()
        self.work_thread = None
        self.end_time = time.time() + (60 * self.minutes_to_timeout)
        signal.signal(signal.SIGINT, self.sig_handler)

    def run(self):
        logging.info('Turning on')
        self.work_thread = threading.Thread(target=self.work)
        self.work_thread.daemon = True
        self.work_thread.start()

        while time.time() < self.end_time:
            self.pull()
        self.turn_off.set()
        logging.info("Timeout")
        self.work_thread.join()
        raise SystemExit

    def work(self):
        while True:
            if self.turn_off.is_set():
                logging.info("Cancelling trades")
                self.exchange.cancel(all=True)
                if hasattr(self.exchange, 'close_positions'):
                    self.exchange.close_positions()
                self.push([], 'active_orders')
                return
            try:
                if not self.msg_queue.empty():
                    msg = self.msg_queue.get()
                    self.process_msg(msg)
                self.execute_strategy()
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
            for k, v in msg['data'].items():
                if self.markets_on[k] and v == 'off':  # cancel trades if turning off market
                    logging.info("Turning off market {}, cancelling trades".format(k))
                    self.exchange.cancel(market=self.markets[k])
                self.markets_on[k] = (v == 'on')
        elif msg['type'] == 'pause':
            for m in self.markets_on.keys():
                self.markets_on[m] = False
            logging.info("Pausing all markets. Cancelling all active trades")
            self.exchange.cancel(all=True)

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
        if hasattr(self.exchange, 'position'):
            positions = {k: self.exchange.position(v) for k,v in self.markets.items()}
            self.push(positions, 'positions')
        if hasattr(self.strategy, 'signals'):
            signals = {k: self.strategy.signals(v) for k,v in self.markets.items()}
            self.push(signals, 'signals')

    def pull(self):
        # pull commands from backend via stdin e.g. {"type": "markets", "data": {"ETH_BTC": "off"}}
        stream = self.input_with_timeout(10)
        # stream = input()
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
        msg = json.dumps(payload, default=serialize_obj)
        requests.post('http://localhost:{}/update'.format(os.environ['PORT']), data=msg)

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
        self.turn_off.set()
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
    def candles(self, market):
        pass


class Strategy(object):
    def __init__(self, exchange, params):
        self.exchange = exchange

    @abc.abstractmethod
    def trade(self, market):
        pass


