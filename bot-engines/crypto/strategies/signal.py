from crypto.engine import Strategy
import logging
import numpy as np
from talib import abstract
from crypto.helpers import print_json
import datetime as dt
import abc


class SignalStrategy(Strategy):
    def __init__(self, exchange, params):
        super().__init__(exchange, params)
        self.candles = {}
        self.next_update = {}
        self.long_thresh = params['long']
        self.short_thresh = params['short']
        self.quantity = params['quantity']

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

        self.next_update[market.symbol] = self.candles[market.symbol][-1].time + dt.timedelta(minutes=1)
        self.next_update[market.symbol] = self.next_update[market.symbol].replace(tzinfo=None)
        return True

    @abc.abstractmethod
    def analyze_market(self, market):
        pass

    @abc.abstractmethod
    def bearish(self, **kwargs):
        pass

    @abc.abstractmethod
    def bullish(self, **kwargs):
        pass

    def trade(self, market):
        if market.symbol not in self.next_update.keys() or dt.datetime.utcnow() >= self.next_update[market.symbol]:
            new_period = self.update_candles(market)
            if new_period:  # pass until a new period begins
                logging.info("Beginning of new period. Analyzing {} market using {} strategy...".format(market.symbol, self))
                stats = self.analyze_market(market)
                # logging.info(stats)
                if self.bullish(**stats):
                    logging.info("Bullish!")
                    order = self.exchange.bid(market=market, quantity=market.increment, rate=None)
                    logging.info("Successfully placed {} order #{} in {}".format(order.side, order.order_id, market.symbol))
                elif self.bearish(**stats):
                    logging.info("Bearish!")
                    order = self.exchange.sell(market=market, quantity=market.increment, rate=None)
                    logging.info("Successfully placed {} order #{} in {}".format(order.side, order.order_id, market.symbol))
        # return signal
        return


class MACDStrategy(SignalStrategy):
    def __init__(self, exchange, params):
        super().__init__(exchange, params)
        # self.low = params['Low']
        # self.high = params['High']

    def __str__(self):
        return "MACD"

    def analyze_market(self, market):
        inputs = {
            'open': np.array([c.open for c in self.candles[market.symbol]]),
            'high': np.array([c.high for c in self.candles[market.symbol]]),
            'low': np.array([c.low for c in self.candles[market.symbol]]),
            'close': np.array([c.close for c in self.candles[market.symbol]]),
            'volume': np.array([c.volume for c in self.candles[market.symbol]]),
        }

        calculate_sma = abstract.Function("SMA")
        sma = calculate_sma(inputs)

        calculate_macd = abstract.Function("MACD")
        macd, macdsignal, macdhist = calculate_macd(inputs)

        # logging.info("MACD: {0} Signal: {1}, Hist: {2}".format(macd[-1], macdsignal[-1], macdhist[-1]))
        stats = {
            'close': inputs['close'][-1],
            'sma': sma[-1],
            'macd': macd[-1],
            'signal': macdsignal[-1],
            'macd_last': macd[-2]
        }
        return stats

    def bullish(self, **kwargs):
        return kwargs['close'] > kwargs['sma'] and kwargs['macd_last'] < kwargs['signal'] \
               and kwargs['macd'] > kwargs['signal'] and kwargs['macd'] < 0

    def bearish(self, **kwargs):
        return kwargs['close'] < kwargs['sma'] and kwargs['macd_last'] > kwargs['signal'] \
               and kwargs['macd'] < kwargs['signal'] and kwargs['macd'] > 0


class RSIStrategy(SignalStrategy):
    def __init__(self, exchange, params):
        super().__init__(exchange, params)
        self.low = int(params['Low'])
        self.high = int(params['High'])

    def __str__(self):
        return "RSI"

    def analyze_market(self, market):
        inputs = {
            'open': np.array([c.open for c in self.candles[market.symbol]]),
            'high': np.array([c.high for c in self.candles[market.symbol]]),
            'low': np.array([c.low for c in self.candles[market.symbol]]),
            'close': np.array([c.close for c in self.candles[market.symbol]]),
            'volume': np.array([c.volume for c in self.candles[market.symbol]]),
        }

        calculate_sma = abstract.Function("SMA")
        sma = calculate_sma(inputs)

        calculate_rsi = abstract.Function("RSI")
        rsi = calculate_rsi(inputs)

        stats = {
            'close': inputs['close'][-1],
            'sma': sma[-1],
            'rsi': rsi[-1]
        }
        return stats

    def bullish(self, **kwargs):
        return kwargs['close'] > kwargs['sma'] and kwargs['rsi'] <= self.low

    def bearish(self, **kwargs):
        return kwargs['close'] < kwargs['sma'] and kwargs['rsi'] >= self.high


class StochRSIStrategy(SignalStrategy):
    def __init__(self, exchange, params):
        super().__init__(exchange, params)
        # self.low = int(params['Low'])
        # self.high = int(params['High'])

    def __str__(self):
        return "StochRSI"

    def analyze_market(self, market):
        inputs = {
            'open': np.array([c.open for c in self.candles[market.symbol]]),
            'high': np.array([c.high for c in self.candles[market.symbol]]),
            'low': np.array([c.low for c in self.candles[market.symbol]]),
            'close': np.array([c.close for c in self.candles[market.symbol]]),
            'volume': np.array([c.volume for c in self.candles[market.symbol]]),
        }

        calculate_sma = abstract.Function("SMA")
        sma_10 = calculate_sma(inputs, timeperiod=10)
        sma_60 = calculate_sma(inputs, timeperiod=60)

        calculate_rsi = abstract.Function("STOCHRSI")
        fastk, fastd = calculate_rsi(inputs)
        stats = {
            'close': inputs['close'][-1],
            'sma_10': sma_10[-1],
            'sma_60': sma_60[-1],
            'stoch_rsi': fastd[-1]
        }
        return stats

    def bullish(self, **kwargs):
        return kwargs['close'] > kwargs['sma_60'] and kwargs['stoch_rsi'] <= 20 and kwargs['close'] < kwargs['sma_10']

    def bearish(self, **kwargs):
        return kwargs['close'] < kwargs['sma_60'] and kwargs['stoch_rsi'] > 80 and kwargs['close'] > kwargs['sma_10']


