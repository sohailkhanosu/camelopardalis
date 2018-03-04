from crypto.engine import Strategy
import logging


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
        logging.info("{} best ask: {}".format(market.symbol, best_ask))
        logging.info("{} best bid: {}".format(market.symbol, best_bid))
        logging.info("{} last: {}".format(market.symbol, last))
        market_value = (best_ask + best_bid) / 2
        return market_value

    def trade(self, market):
        self.exchange.cancel(market=market)  # cancel previous orders in this market
        market_value = round(self.analyze_market(market), 8)
        spread = market_value * .1
        ask_quote = round(market_value + (spread / 2), 8)
        bid_quote = round(market_value - (spread / 2), 8)
        min_qty = market.increment

        logging.info("{} market value: {}".format(market.symbol, market_value))
        logging.info("{} ask quote: {}".format(market.symbol, ask_quote))
        logging.info("{} bid quote: {}".format(market.symbol, bid_quote))

        try:
            new_orders = []
            bid = self.exchange.bid(market=market, rate=bid_quote, quantity=min_qty)
            ask = self.exchange.ask(market=market, rate=ask_quote, quantity=min_qty)
            for order in [bid, ask]:
                if order:
                    new_orders.append(order)
                    logging.info("Successfully placed {} order #{} in {}".format(order.side, order.order_id, market.symbol))

            return new_orders
        except Exception as e:
            logging.warning('Order failed: "{}"'.format(e))
            self.exchange.cancel(all=True)
            raise e


