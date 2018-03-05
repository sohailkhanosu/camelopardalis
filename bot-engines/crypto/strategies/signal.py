from crypto.engine import Strategy
import logging
import numpy as np
import concurrent.futures
from talib import abstract
from crypto.helpers import print_json
from collections import namedtuple
import datetime as dt
import abc
import time


class SignalConfig:
    def __init__(self, *args):
        self.long_qty_cap = float(args[0])
        self.short_qty_cap = float(args[1])
        self.lot_qty = float(args[2])
        self.long_score_threshold = float(args[3])
        self.short_score_threshold = float(args[4])


class SignalStrategy(Strategy):
    def __init__(self, exchange, params, indicators):
        super().__init__(exchange, params)
        self.candles = {}
        self.next_update = {}
        self.indicators = indicators
        self.cfg = {market: SignalConfig(*args) for market, args in params.items()}

    def __str__(self):
        return "Signal Strategy"

    def update_candles(self, market):
        if market.symbol not in self.candles.keys():
            self.candles[market.symbol] = self.exchange.candles(market, limit=100)
        else:
            start_time = self.candles[market.symbol][-1].time + dt.timedelta(seconds=5)
            new_candles = self.exchange.candles(market, start=start_time, limit=5)
            if len(new_candles) < 1:
                return False  # no new candles yet
            self.candles[market.symbol].extend(new_candles)
            self.candles[market.symbol] = self.candles[market.symbol][-100:]

        return True

    def get_input(self, market):
        self.update_candles(market)
        inputs = {
            'open': np.array([c.open for c in self.candles[market.symbol]]),
            'high': np.array([c.high for c in self.candles[market.symbol]]),
            'low': np.array([c.low for c in self.candles[market.symbol]]),
            'close': np.array([c.close for c in self.candles[market.symbol]]),
            'volume': np.array([c.volume for c in self.candles[market.symbol]]),
        }
        return inputs

    def signals(self, market):
        inputs = self.get_input(market)
        return {k: v(inputs) for (k, v) in self.indicators.items()}

    def trade(self, market):
        if self.new_candle(market):
            self.candles[market.symbol] = self.exchange.candles(market)
            logging.info("Beginning of new period. Analyzing {} market using {} strategy...".format(market.symbol, self))

            with concurrent.futures.ThreadPoolExecutor() as executor:
                signal_future = executor.submit(self.signals, market)
                position_future = executor.submit(self.exchange.position, market)
                balance_future = executor.submit(self.exchange.balance)
                book_future = executor.submit(self.exchange.order_book, market)

                signal = signal_future.result()
                mean_score = sum(v for v in signal.values()) / len(signal)

                if mean_score >= self.cfg[market.symbol].long_score_threshold:
                    self.open_longs(market=market, position=position_future.result(), balance=balance_future.result(), book=book_future.result())
                elif mean_score > self.cfg[market.symbol].short_score_threshold:
                    self.close_positions(market=market, position=position_future.result())
                else:
                    self.open_shorts(market=market, position=position_future.result(), balance=balance_future.result(), book=book_future.result())

    def new_candle(self, market):
        return (market.symbol not in self.candles) or ((time.time() - self.candles[market.symbol][-1].time.timestamp()) > 60)

    def close_positions(self, market, position):
        if position > 0:
            self.exchange.ask(market=market, rate=None, quantity=position)
        elif position < 0:
            self.exchange.bid(market=market, rate=None, quantity=abs(position))

    def open_longs(self, market, position, balance, book):
        if position < 0:
            self.close_positions(market=market, position=position)
            position = 0

        cap_buffer = self.cfg[market.symbol].long_qty_cap - position
        funds = self.mid_spread(book) * balance[market.base].available * 0.9
        quantity = min(funds, self.cfg[market.symbol].lot_qty, cap_buffer)
        if quantity > market.increment:
            self.exchange.bid(market=market, rate=None, quantity=quantity)

    def open_shorts(self, market, position, balance, book):
        if position > 0:
            self.close_positions(market=market, position=position)
            position = 0

        cap_buffer = self.cfg[market.symbol].short_qty_cap + position
        funds = self.mid_spread(book) * balance[market.base].available * 0.9
        quantity = min(funds, self.cfg[market.symbol].lot_qty, cap_buffer)
        if quantity > market.increment:
            self.exchange.ask(market=market, rate=None, quantity=quantity)

    @staticmethod
    def mid_spread(book):
        return book.bids[0].rate + ((book.asks[0].rate - book.bids[0].rate) / 2)


def MACD(inputs):
    Result = namedtuple('Result', 'close, sma, macd, signal, macd_last')

    calculate_sma = abstract.Function("SMA")
    sma = calculate_sma(inputs)

    calculate_macd = abstract.Function("MACD")
    macd, macdsignal, macdhist = calculate_macd(inputs)

    r = Result(
        close=inputs['close'][-1],
        sma=sma[-1],
        macd=macd[-1],
        signal=macdsignal[-1],
        macd_last=macd[-2]
    )
    indicator = 0
    if r.close > r.sma and (0 > r.macd > r.signal > r.macd_last):
        indicator = 1
    elif r.close < r.sma and (0 < r.macd < r.signal < r.macd_last):
        indicator = -1
    return indicator


def RSI(inputs):
    Result = namedtuple('Result', 'close, sma, rsi')
    calculate_sma = abstract.Function("SMA")
    sma = calculate_sma(inputs)

    calculate_rsi = abstract.Function("RSI")
    rsi = calculate_rsi(inputs)

    r = Result(
        close=inputs['close'][-1],
        sma=sma[-1],
        rsi=rsi[-1]
    )
    indicator = 0
    if r.close > r.sma and r.rsi <= 30:
        indicator = 1
    elif r.close < r.sma and r.rsi >= 70:
        indicator = -1
    return indicator


def STOCHRSI(inputs):
    Result = namedtuple('Result', 'close, sma_10, sma_60, stoch_rsi')
    calculate_sma = abstract.Function("SMA")
    sma_10 = calculate_sma(inputs, timeperiod=10)
    sma_60 = calculate_sma(inputs, timeperiod=60)

    calculate_rsi = abstract.Function("STOCHRSI")
    fastk, fastd = calculate_rsi(inputs)
    r = Result(
        close=inputs['close'][-1],
        sma_10=sma_10[-1],
        sma_60=sma_60[-1],
        stoch_rsi=fastd[-1]
    )

    indicator = 0
    if r.close > r.sma_60 and r.stoch_rsi <= 20 and r.close < r.sma_10:
        indicator = 1
    elif r.close < r.sma_60 and r.stoch_rsi > 80 and r.close > r.sma_10:
        indicator = -1
    return indicator