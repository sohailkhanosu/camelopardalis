class Currency:
    pass


class Market(object):
    def __init__(self, counter, base, symbol, increment, make_fee, take_fee):
        self.counter = counter
        self.base = base
        self.symbol = symbol
        self.increment = increment
        self.make_fee = make_fee
        self.take_fee = take_fee


class Order(object):
    def __init__(self, order_id, market, side, rate, quantity, time):
        self.order_id = str(order_id)
        self.market = market
        self.side = str(side)
        self.rate = float(rate)
        self.quantity = float(quantity)
        self.time = time


class Trade(object):
    def __init__(self, trade_id, order_id, market, side, rate, quantity, time):
        self.trade_id = str(trade_id)
        self.order_id = str(order_id)
        self.market = market
        self.side = str(side)
        self.rate = float(rate)
        self.quantity = float(quantity)
        self.time = time


class Ticker(object):
    def __init__(self, market, ask, bid,  low, high, last, base_volume, quote_volume, time):
        self.market = market
        self.ask = float(ask)
        self.bid = float(bid) if bid else None
        self.low = float(low)
        self.high = float(high)
        self.last = float(last)
        self.base_volume = float(base_volume)
        self.quote_volume = float(quote_volume)
        self.time = time


class Balance(object):
    def __init__(self, available, reserved):
        self.available = float(available)
        self.reserved = float(reserved)


class OrderBook(object):
    def __init__(self, asks, bids):
        self.asks = asks
        self.bids = bids


class Entry(object):
    def __init__(self, rate, quantity):
        self.rate = float(rate)
        self.quantity = float(quantity)


class Candle(object):
    def __init__(self, market, open, high, low, close, volume, time):
        self.market = market
        self.open = float(open) if open else None
        self.high = float(high) if high else None
        self.low = float(low) if low else None
        self.close = float(close) if close else None
        self.volume = float(volume) if volume else 0
        self.time = time

