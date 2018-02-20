from crypto import TradingBot
import sys
import logging

def main():
	logging.basicConfig(filename='mockhitbtc.log', level=logging.INFO)
	b = TradingBot('mockhitbtc', config_path='config.ini', mock=True)
	try:
		b.run()
	except (KeyboardInterrupt, SystemExit) as e:
		logging.info("Exiting program")
		b.exchange.cancel(all=True)  # cancel orders one more time just to be sure
		b.push([], 'active_orders')
		sys.exit(0)

if __name__ == "__main__":
    main()