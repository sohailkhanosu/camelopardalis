from crypto.engine import Exchange
import requests
from crypto.structs import Order, Trade, Market, Ticker, Balance, OrderBook, Entry, Candle
import dateutil.parser
from crypto.hitbtc.mock import mock_adapter
import logging
import configparser
from crypto.helpers import print_json
import datetime


class HitBTCExchange(Exchange):
    def __init__(self, base_url, key, secret, symbols, mock=True):
        super().__init__(base_url, key, secret, symbols, mock)
        self.session = requests.session()
        if mock:
            self.session.mount('mock', mock_adapter)
        self.session.auth = (self.key, self.secret)
        self.symbols = symbols if not mock else ['ETHBTC', 'LTCBTC', 'ETCBTC']
        self.markets = {}
        self.markets = {s: self.to_market(s) for s in symbols}

    # Interface
    def bid(self, market, rate, quantity):
        try:
            status, data = self._order_create(market.symbol, side="buy", price=rate, quantity=quantity)
            if status == 200:
                return self._to_order(data)
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in bid function")

    def ask(self, market, rate, quantity):
        try:
            status, data = self._order_create(market.symbol, side="sell", price=rate, quantity=quantity)
            if status == 200:
                return self._to_order(data)
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in ask function")

    def cancel(self, order_id=None, market=None, all=False):
        try:
            if all:
                status, data = self._orders_cancel()
                orders = list(map(self._to_order, data))
            elif market:
                status, data = self._orders_cancel(market.symbol)
                orders = list(map(self._to_order, data))
            elif order_id:
                status, data = self._order_cancel(order_id)
                orders = [self._to_order(data)]
            else:
                raise Exception('Specify order_id, market, or all')
            return orders
        except Exception as e:
            logging.exception("Error in cancel function")

    def balance(self):
        try:
            status, data = self._trading_balance()
            if status == 200:
                return {d['currency']: Balance(d['available'], d['reserved']) for d in data}
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in balance function")

    def orders(self, market=None):
        try:
            symbol = market.symbol if market else ''
            status, data = self._orders_active(symbol)
            if status == 200:
                orders = list(map(self._to_order, data))
                return orders
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in orders function")

    def order_book(self, market):
        try:
            status, data = self._orderbook(market.symbol)
            if status == 200:
                asks = [Entry(d['price'], d['size']) for d in data['ask'][:10]]
                bids = [Entry(d['price'], d['size']) for d in data['bid'][:10]]
                orderbook = OrderBook(asks, bids)
                return orderbook
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in order_book function")

    def ticker(self, market=None):
        try:
            symbol = market.symbol if market else ''
            status, data = self._tickers(symbol)
            if status == 200:
                if market:
                    return self._to_ticker(data, market)
                else:
                    tickers = [self._to_ticker(d) for d in data]
                    return tickers
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in ticker function")

    def market_trades(self, market):
        try:
            status, data = self._trades(market.symbol)
            if status == 200:
                trades = [self._to_trade(d, market) for d in data]
                return trades
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in market_trades function")

    def trades(self, market):
        try:
            status, data = self._history_trades(market.symbol)
            if status == 200:
                trades = [self._to_trade(d, market) for d in data]
                return trades
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in trades function")

    def candles(self, market, start=None, limit=100):
        try:
            status, data = self._candles(market.symbol, limit=limit, period='M1')
            if status == 200:
                candles = [self._to_candle(d, market) for d in data]
                # filter out candles from before start param
                candles = [c for c in candles if start is None or c.time.replace(tzinfo=None) > start.replace(tzinfo=None)]
                return candles
            else:
                raise Exception(data['error']['message'])
        except Exception as e:
            logging.exception("Error in candles function")

    # Data conversion
    def to_market(self, symbol):
        m = self.markets.get(symbol, None)
        if not m:
            status, data = self._symbols(symbol)
            if status == 200:
                m = Market(counter=data['baseCurrency'], base=data['quoteCurrency'], symbol=symbol, increment=data['quantityIncrement'],
                           make_fee=data['provideLiquidityRate'], take_fee=data['takeLiquidityRate'])
            else:
                raise Exception(data['error']['message'])
        return m

    def _split_symbol(self, symbol):
        return symbol[:len(symbol)//2], symbol[len(symbol)//2:]

    def _to_order(self, data):
        market = self.markets.get(data['symbol'], None)
        if not market:
            market = self.to_market(data['symbol'])
        created = dateutil.parser.parse(data['createdAt'])
        order = Order(order_id=data['clientOrderId'], market=market, side=data['side'],
                      rate=data['price'], quantity=data['cumQuantity'], time=created)
        return order

    def _to_trade(self, data, market=None):
        if not market:
            market = self.to_market(data['symbol'])
        time = dateutil.parser.parse(data['timestamp'])
        order_id = data.get('clientOrderId', None)
        trade = Trade(trade_id=data['id'], order_id=order_id, market=market,
                      side=data['side'], rate=data['price'], quantity=data['quantity'], time=time)
        return trade

    def _to_ticker(self, data, market=None):
        if not market:
            market = self.to_market(data['symbol'])
        time = data['timestamp']
        ticker = Ticker(market=market, ask=data['ask'], bid=data['bid'], low=data['low'], high=data['high'],
                        last=data['last'], base_volume=data['volume'], quote_volume=data['volumeQuote'], time=time)
        return ticker

    def _to_candle(self, data, market=None):
        if not market:
            market = self.to_market(data['symbol'])
        time = dateutil.parser.parse(data['timestamp'])
        candle = Candle(market=market, open=data['open'], high=data['min'], low=data['max'],
                        close=data['close'], volume=data['volume'], time=time)
        return candle

    # API Methods
    # Market
    def _currencies(self, currency=''):
        response = self.session.get(self.base_url + '/public/currency/' + currency)
        return response.status_code, response.json()

    def _symbols(self, symbol=''):
        response = self.session.get(self.base_url + '/public/symbol/' + symbol)
        return response.status_code, response.json()

    def _tickers(self, symbol=''):
        response = self.session.get(self.base_url + '/public/ticker/' + symbol)
        return response.status_code, response.json()

    def _trades(self, symbol, sort=None, by=None, _from=None, till=None, limit=None, offset=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self and v != symbol}
        response = self.session.get(self.base_url + '/public/trades/' + symbol, params=payload)
        return response.status_code, response.json()

    def _orderbook(self, symbol):
        response = self.session.get(self.base_url + '/public/orderbook/' + symbol)
        return response.status_code, response.json()

    def _candles(self, symbol, limit=None, period=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        if period and period not in ['M1', 'M3', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'D7', '1M']:
            raise Exception('Invalid period')
        response = self.session.get(self.base_url + '/public/candles/' + symbol, params=payload)
        return response.status_code, response.json()

    # Trading
    def _trading_balance(self):
        response = self.session.get(self.base_url + '/trading/balance')
        return response.status_code, response.json()

    def _trading_fee(self, symbol):
        response = self.session.get(self.base_url + '/trading/fee/' + symbol)
        return response.status_code, response.json()

    def _orders_active(self, symbol=''):
        payload = {'symbol': symbol}
        response = self.session.get(self.base_url + '/order/', data=payload)
        return response.status_code, response.json()

    def _order_active(self, order_id, wait=''):
        if wait:
            payload = {'wait': wait}
        else:
            payload = None
        response = self.session.get(self.base_url + '/order/' + order_id, params=payload)
        return response.status_code, response.json()

    def _order_create(self, symbol, side, quantity, price, timeInForce=None,
                      type=None, stopPrice=None, expireTime=None, strictValidate=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        if side not in ["buy", "sell"]:
            raise Exception("Invalid side")
        if timeInForce and timeInForce not in ['GTC', 'IOC', 'FOK', 'Day', 'GTD']:
            raise Exception("Invalid timeInForce")
        if type and type not in ['limit', 'market', 'stopLimit', 'stopMarket']:
            raise Exception('Invalid type')
        if not stopPrice and payload.get('type', '').startswith('stop'):
            raise Exception("Stop price required for stop types")
        if not expireTime and payload.get('timeInForce', '') == 'GTD':
            raise Exception("expireTime required for GTD timeInForce")
        response = self.session.post(self.base_url + '/order', data=payload)

        return response.status_code, response.json()

    def _orders_cancel(self, symbol=None):
        if symbol:
            payload = {'symbol': symbol}
        else:
            payload = None
        response = self.session.delete(self.base_url + '/order', data=payload)
        return response.status_code, response.json()

    def _order_cancel(self, clientOrderId):
        response = self.session.delete(self.base_url + '/order/' + clientOrderId)
        return response.status_code, response.json()

    # History
    def _history_orders(self, symbol=None, clientOrderId=None, _from=None, till=None, limit=None, offset=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        if clientOrderId:
            payload = {'clientOrderId': clientOrderId}
        else:
            if _from:
                payload['from'] = payload['_from']
                del payload['_from']
        response = self.session.get(self.base_url + '/history/order', data=payload)
        return response.status_code, response.json()

    def _history_trades(self, symbol=None, sort=None, by=None, _from=None, till=None, limit=None, offset=None):
        payload = {k: v for (k, v) in locals().items() if v is not None and v != self}
        if _from:
            payload['from'] = payload['_from']
            del payload['_from']
        response = self.session.get(self.base_url + '/history/trades', data=payload)
        return response.status_code, response.json()

    def _history_trade(self, orderId):
        response = self.session.get(self.base_url + '/history/order/' + orderId + '/trades')
        return response.status_code, response.json()


if __name__ == "__main__":
    config = configparser.ConfigParser(allow_no_value=True)
    config.read("../config.ini")
    b = HitBTCExchange(config["hitbtc"]['BaseUrl'], config['hitbtc']['Key'], config['hitbtc']['Secret'],
                       config['hitbtc']['Symbols'].split(','), False)
    # r = b._candles('LTCBTC', period='M1')
    # print_json(r[-1])
    print(b.markets)