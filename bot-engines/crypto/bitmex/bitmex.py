from crypto.engine import Exchange
import requests
from crypto.structs import Order, Trade, Market, Ticker, Balance, OrderBook, Entry
import dateutil.parser
import logging
import configparser
import json
from crypto.bitmex.auth import APIKeyAuthWithExpires
from crypto.helpers import print_json


class BitMEXExchange(Exchange):
    def __init__(self, base_url, key, secret, symbols, mock=False):
        super().__init__(base_url, key, secret, symbols, mock)
        self.auth = APIKeyAuthWithExpires(key, secret)
        self.symbols = symbols
        self.markets = {}
        for s in self.symbols:
            self.markets[s] = self.to_market(s)

    # Interface
    def bid(self, market, rate, quantity):
        try:
            status, data = self._order(market.symbol, side="Buy", price=rate, orderQty=quantity)
            if status == 200:
                return self._to_order(data)
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in bid function")

    def ask(self, market, rate, quantity):
        try:
            status, data = self._order(market.symbol, side="Sell", price=rate, orderQty=quantity)
            if status == 200:
                return self._to_order(data)
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in ask function")

    def cancel(self, order_id=None, market=None, all=False):
        try:
            if all:
                status, data = self._cancel_all()
                orders = list(map(self._to_order, data))
            elif market:
                status, data = self._cancel_all(market.symbol)
                orders = list(map(self._to_order, data))
            elif order_id:
                status, data = self._cancel(order_id)
                orders = [self._to_order(data)]
            else:
                raise Exception('Specify order_id, market, or all')
            return orders
        except Exception as e:
            logging.exception("Error in cancel function")

    def balance(self):
        try:
            status, data = self._wallet()
            if status == 200:
                return {data['currency'].upper(): Balance(data['amount'], 0)}
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in balance function")

    def orders(self, market=None):
        try:
            symbol = market.symbol if market else ''
            status, data = self._active_orders(symbol)
            orders = list(map(self._to_order, data))
            if status == 200:
                return orders
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in orders function")

    def order_book(self, market):
        try:
            status, data = self._order_book(market.symbol)
            asks = [Entry(d['price'], d['size']) for d in data if d['side'] == 'Sell']
            bids = [Entry(d['price'], d['size']) for d in data if d['side'] == 'Buy']
            orderbook = OrderBook(asks, bids)
            if status == 200:
                return orderbook
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in order_book function")

    def ticker(self, market=None):
        try:
            status, data = self._instrument(market.symbol)
            if status == 200:
                if market:
                    return self._to_ticker(data[0], market)
                else:
                    tickers = [self._to_ticker(d) for d in data]
                    return tickers
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in ticker function")

    def market_trades(self, market):
        pass

    def trades(self, market):
        try:
            status, data = self._filled_orders(market.symbol)
            trades = [self._to_trade(d, market) for d in data]
            if status == 200:
                return trades
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in trades function")

    # Data conversion
    def to_market(self, symbol):
        m = self.markets.get(symbol, None)
        if not m:
            status, data = self._instrument(symbol)
            if status == 200:
                m = Market(counter=data[0]['rootSymbol'], base='XBT', symbol=symbol, increment=data[0]['lotSize'],
                           make_fee=data[0]['makerFee'], take_fee=data[0]['takerFee'])
            else:
                raise Exception(data['error']['message'])

        return m

    def _to_order(self, data):
        market = self.markets.get(data['symbol'], None)
        if not market:
            market = self.to_market(data['symbol'])
        created = dateutil.parser.parse(data['timestamp'])
        order = Order(order_id=data['orderID'], market=market, side=data['side'].lower(),
                      rate=data['price'], quantity=data['orderQty'], time=created)
        return order

    def _to_trade(self, data, market=None):
        market = self.markets.get(data['symbol'], None)
        if not market:
            market = self.to_market(data['symbol'])
        time = dateutil.parser.parse(data['timestamp'])
        trade = Trade(trade_id=data['orderID'], order_id=data['orderID'], market=market,
                      side=data['side'], rate=data['price'], quantity=data['orderQty'], time=time)
        return trade

    def _to_ticker(self, data, market=None):
        if not market:
            market = self.to_market(data['symbol'])
        time = data['timestamp']
        ticker = Ticker(market=market, ask=data['askPrice'], bid=data['bidPrice'], low=data['lowPrice'], high=data['highPrice'],
                        last=data['lastPrice'], base_volume=0, quote_volume=data['turnover'], time=time)
        return ticker

    # API Methods
    def _wallet(self):
        r = requests.get(self.base_url + "/user/wallet/", auth=self.auth)
        return r.status_code, r.json()

    def _instrument(self, symbol=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        r = requests.get(self.base_url + "/instrument/", data=payload, auth=self.auth)
        return r.status_code, r.json()

    def _order(self, symbol, side, orderQty, price, timeInForce=None, ordType=None, stopPx=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        if side not in ["Buy", "Sell"]:
            raise Exception("Invalid side")
        if timeInForce and timeInForce not in ['Day', 'GoodTillCancel', 'ImmediateOrCancel', 'FillOrKill']:
            raise Exception("Invalid timeInForce")
        if ordType and ordType not in ['Market', 'Limit', 'Stop', 'StopLimit', 'MarketIfTouched', 'LimitIfTouched',
                                       'MarketWithLeftOverAsLimit', 'Pegged']:
            raise Exception('Invalid type')
        if not stopPx and payload.get('type', '').startswith('Stop'):
            raise Exception("Stop price required for stop types")
        response = requests.post(self.base_url + '/order', data=payload, auth=self.auth)
        return response.status_code, response.json()

    def _cancel(self, orderID=None, clOrdID=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        if not len(payload.keys()):
            raise Exception("Order id or client order id required")
        response = requests.delete(self.base_url + '/order', data=payload, auth=self.auth)
        return response.status_code, response.json()

    def _cancel_all(self, symbol=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        response = requests.delete(self.base_url + '/order/all', data=payload, auth=self.auth)
        return response.status_code, response.json()

    def _order_book(self, symbol=None, depth=10):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        payload['filter'] = json.dumps({"ordStatus": "Filled"})
        r = requests.get(self.base_url + "/orderBook/L2", data=payload, auth=self.auth)
        return r.status_code, r.json()

    def _active_orders(self, symbol=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        payload['filter'] = json.dumps({"open": "true"})
        r = requests.get(self.base_url + "/order/", data=payload, auth=self.auth)
        return r.status_code, r.json()

    def _filled_orders(self, symbol=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        payload['filter'] = json.dumps({"ordStatus": "Filled"})
        r = requests.get(self.base_url + "/order/", data=payload, auth=self.auth)
        return r.status_code, r.json()

    def _trades(self, symbol=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        r = requests.get(self.base_url + "/trade/", data=payload, auth=self.auth)
        return r.status_code, r.json()


if __name__ == "__main__":
    config = configparser.ConfigParser(allow_no_value=True)
    config.read("../config.ini")
    b = BitMEXExchange(config["bitmex"]['BaseUrl'], config['bitmex']['Key'], config['bitmex']['Secret'],
                       config['bitmex']['Symbols'].split(','), False)
    r = b._instrument("XRPH18")
    print_json(r[1])