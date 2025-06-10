import ccxt
import logging
from datetime import datetime

class KuCoinTrader:
    def __init__(self, api_key, api_secret, password, test_mode=True):
        self.test_mode = test_mode
        self.exchange = ccxt.kucoin({
            'apiKey': api_key,
            'secret': api_secret,
            'password': password,
            'enableRateLimit': True,
        })

    def get_balance(self, asset="USDT"):
        try:
            balance = self.exchange.fetch_balance()
            return balance['free'].get(asset, 0)
        except Exception as e:
            logging.error(f"[BALANCE ERROR] {e}")
            return 0

    def trade(self, symbol, usdt_amount, reason="signal"):
        try:
            if self.test_mode:
                print(f"[PAPER TRADE] Buy ${usdt_amount} of {symbol} - Reason: {reason}")
                return {"status": "paper", "symbol": symbol, "usdt_amount": usdt_amount}

            # Fetch ticker to estimate price
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            quantity = round(usdt_amount / price, 5)

            # Place market buy
            order = self.exchange.create_market_buy_order(symbol, quantity)
            logging.info(f"[TRADE] Executed BUY on {symbol}: {quantity} @ {price} - Reason: {reason}")
            return order
        except Exception as e:
            logging.error(f"[TRADE ERROR] {symbol}: {e}")
            return None
