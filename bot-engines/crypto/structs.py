class Currency:
    pass


class Market(object):
    def __init__(self, counter, base, symbol):
        self.counter = counter
        self.base = base
        self.symbol = symbol


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