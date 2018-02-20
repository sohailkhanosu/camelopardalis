from crypto import TradingBot
import sys
import logging

def main():
	logging.basicConfig(filename='hitbtc.log', level=logging.INFO)
	b = TradingBot('hitbtc', config_path='config.ini', mock=False)
	try:
		b.run()
	except (KeyboardInterrupt, SystemExit) as e:
		logging.info("Exiting program")
		b.exchange.cancel(all=True)  # cancel orders one more time just to be sure
		b.push([], 'active_orders')
		sys.exit(0)

if __name__ == "__main__":
    main()