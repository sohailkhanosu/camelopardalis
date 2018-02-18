from crypto import TradingBot
import sys
import logging


def main():
    b = TradingBot('hitbtc', config_path='config.ini', mock=True)
    try:
        b.run()
    except (KeyboardInterrupt, SystemExit) as e:
        logging.info("Exiting program")
        b.exchange.cancel(all=True)  # cancel orders one more time just to be sure
    sys.exit(0)

if __name__ == "__main__":
    main()