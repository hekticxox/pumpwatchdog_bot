import os
import ccxt
import unittest
from dotenv import load_dotenv

load_dotenv()

class TestKucoinConnection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_key = os.getenv("KUCOIN_API_KEY")
        cls.api_secret = os.getenv("KUCOIN_SECRET")
        cls.api_password = os.getenv("KUCOIN_PASSWORD")
        cls.kucoin = ccxt.kucoin({
            'apiKey': cls.api_key,
            'secret': cls.api_secret,
            'password': cls.api_password,
            'enableRateLimit': True,
        })

    def test_connection(self):
        try:
            balance = self.kucoin.fetch_balance()
            usdt_balance = balance['free'].get('USDT', 0)
            print(f"✅ Connected successfully. USDT Balance: {usdt_balance}")
            self.assertIsInstance(usdt_balance, (float, int))
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.fail(f"KuCoin connection failed: {e}")

    def test_markets(self):
        try:
            markets = self.kucoin.load_markets()
            self.assertTrue(isinstance(markets, dict))
            self.assertIn('BTC/USDT', markets)
        except Exception as e:
            print(f"❌ Could not fetch markets: {e}")
            self.fail(f"KuCoin failed to return markets: {e}")

    def test_fetch_ticker(self):
        try:
            ticker = self.kucoin.fetch_ticker('BTC/USDT')
            self.assertIn('last', ticker)
            self.assertIn('baseVolume', ticker)
        except Exception as e:
            print(f"❌ Could not fetch ticker: {e}")
            self.fail(f"KuCoin failed to return ticker: {e}")

if __name__ == "__main__":
    unittest.main()
