from crypto.engine import Exchange
import requests
from crypto.structs import Order, Trade, Market, Ticker, Balance, OrderBook, Entry, Candle
import dateutil.parser
import logging
import configparser
import json
from crypto.bitmex.auth import APIKeyAuthWithExpires
from crypto.helpers import print_json
import time


class BitMEXExchange(Exchange):
    def __init__(self, base_url, key, secret, symbols, mock=False):
        super().__init__(base_url, key, secret, symbols, mock)
        self.auth = APIKeyAuthWithExpires(key, secret)
        self.symbols = symbols
        self.markets = {}
        self.markets = {s: self.to_market(s) for s in symbols}

    # Interface
    def bid(self, market, rate, quantity):
        try:
            if rate is None:
                ord_type = 'Market'
            else:
                ord_type = None
            status, data = self._order(market.symbol, side="Buy", price=rate, orderQty=quantity, ordType=ord_type)
            if status == 200:
                return self._to_order(data)
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in bid function")

    def ask(self, market, rate, quantity):
        try:
            if rate is None:
                ord_type = 'Market'
            else:
                ord_type = None
            status, data = self._order(market.symbol, side="Sell", price=rate, orderQty=quantity, ordType=ord_type)
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
                orders = list(map(self._to_order, data))
            else:
                raise Exception('Specify order_id, market, or all')
            return orders
        except Exception as e:
            logging.exception("Error in cancel function")

    def balance(self):
        try:
            status, data = self._wallet()
            if status == 200:
                total = [d for d in data if d['transactType'] == 'Total'][-1]
                currency = total['currency'].upper()
                if total['currency'].upper() == 'XBT':
                    currency = 'BTC'
                return {currency: Balance(total['walletBalance'] / 100000000, 0)}
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in balance function")

    def orders(self, market=None):
        try:
            symbol = market.symbol if market else ''
            status, data = self._active_orders(symbol)
            if status == 200:
                orders = list(map(self._to_order, data))
                return orders
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in orders function")

    def order_book(self, market):
        try:
            status, data = self._order_book(market.symbol)
            if status == 200:
                asks = [Entry(d['price'], d['size']) for d in data if d['side'] == 'Sell']
                bids = [Entry(d['price'], d['size']) for d in data if d['side'] == 'Buy']
                orderbook = OrderBook(asks, bids)
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

    def trades(self, market):
        try:
            status, data = self._filled_orders(market.symbol)
            if status == 200:
                trades = [self._to_trade(d, market) for d in data]
                return trades
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in trades function")

    def candles(self, market, start=None, limit=100):
        try:
            status, data = self._trades_bucketed(market.symbol, count=limit, startTime=start)
            if status == 200:
                candles = [self._to_candle(d) for d in data[::-1]]
                return candles
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in candles function")

    def position(self, market):
        try:
            status, data = self._positions(market.symbol)
            if status == 200:
                if len(data) < 1:
                    return 0
                return data[0]['currentQty']
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in position function")

    def close_positions(self):
        try:
            for m in self.markets.values():
                self._close_position(m.symbol)
        except Exception as e:
            logging.exception("Error in close position function")

    # Data conversion
    def to_market(self, symbol):
        m = self.markets.get(symbol, None)
        if not m:
            status, data = self._instrument(symbol)
            if status == 200:
                counter = data[0]['positionCurrency']
                if counter.upper() == 'XBT':
                    counter = 'BTC'
                base = data[0]['underlying']
                if base.upper() == 'XBT':
                    base = 'BTC'
                m = Market(counter=counter, base=base, symbol=symbol,
                           increment=data[0]['lotSize'], make_fee=data[0]['makerFee'], take_fee=data[0]['takerFee'])
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

    def _to_candle(self, data):
        market = self.to_market(data['symbol'])
        time = dateutil.parser.parse(data['timestamp'])
        candle = Candle(market=market, open=data['open'], high=data['high'], low=data['low'],
                       close=data['close'], volume=data['volume'], time=time)
        return candle

    # API Methods
    def _wallet(self):
        r = requests.get(self.base_url + "/user/walletSummary/", auth=self.auth)
        self._control_rate(r)
        return r.status_code, r.json()

    def _instrument(self, symbol=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        r = requests.get(self.base_url + "/instrument/", data=payload, auth=self.auth)
        self._control_rate(r)
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
        self._control_rate(response)
        return response.status_code, response.json()

    def _cancel(self, orderID=None, clOrdID=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        if not len(payload.keys()):
            raise Exception("Order id or client order id required")
        response = requests.delete(self.base_url + '/order', data=payload, auth=self.auth)
        self._control_rate(response)
        return response.status_code, response.json()

    def _cancel_all(self, symbol=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        response = requests.delete(self.base_url + '/order/all', data=payload, auth=self.auth)
        self._control_rate(response)
        return response.status_code, response.json()

    def _order_book(self, symbol=None, depth=10):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        payload['filter'] = json.dumps({"ordStatus": "Filled"})
        r = requests.get(self.base_url + "/orderBook/L2", data=payload, auth=self.auth)
        self._control_rate(r)
        return r.status_code, r.json()

    def _active_orders(self, symbol=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        payload['filter'] = json.dumps({"open": "true"})
        r = requests.get(self.base_url + "/order/", data=payload, auth=self.auth)
        self._control_rate(r)
        return r.status_code, r.json()

    def _filled_orders(self, symbol=None, count=100):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        payload['filter'] = json.dumps({"ordStatus": "Filled"})
        r = requests.get(self.base_url + "/order/", data=payload, auth=self.auth)
        self._control_rate(r)
        return r.status_code, r.json()

    def _trades(self, symbol=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        r = requests.get(self.base_url + "/trade/", data=payload, auth=self.auth)
        self._control_rate(r)
        return r.status_code, r.json()

    def _trades_bucketed(self, symbol=None, binSize='1m', count=None, start=None, reverse=True, partial=False,
                         startTime=None, endTime=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        payload['reverse'] = "true" if payload['reverse'] else "false"
        payload['partial'] = "true" if payload['partial'] else "false"
        if binSize not in ['1m', '5m', '1h', '1d']:
            raise Exception('Invalid binSize')
        r = requests.get(self.base_url + "/trade/bucketed", data=payload)
        self._control_rate(r)
        return r.status_code, r.json()

    def _positions(self, symbol):
        payload = {}
        payload['filter'] = json.dumps({"symbol": symbol})
        r = requests.get(self.base_url + "/position/", data=payload, auth=self.auth)
        self._control_rate(r)
        return r.status_code, r.json()

    def _close_position(self, symbol):
        payload = {"symbol": symbol,
                   "ordType": "Market",
                   "execInst": "Close"}
        r = requests.post(self.base_url + "/order/", data=payload, auth=self.auth)
        self._control_rate(r)
        return r.status_code, r.json()

    def _control_rate(self, res):
        try:
            if int(res.headers['x-ratelimit-remaining']) < 50:
                time.sleep(20)
            else:
                time.sleep(.2)
        except:
            time.sleep(5)


# if __name__ == "__main__":
#     config = configparser.ConfigParser(allow_no_value=True)
#     config.read("../config.ini")
#     b = BitMEXExchange(config["bitmex"]['BaseUrl'], config['bitmex']['Key'], config['bitmex']['Secret'],
#                        config['bitmex']['Symbols'].split(','), False)
#     r = b.position(b.markets['XBTJPY'])
#     print(r)
#     # print(int(r[1]['amount'])/100000000)


