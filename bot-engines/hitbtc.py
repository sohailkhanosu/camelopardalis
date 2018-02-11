from crypto import TradingBot


b = TradingBot('hitbtc', config_path='config.ini', mock=True)
b.run()
