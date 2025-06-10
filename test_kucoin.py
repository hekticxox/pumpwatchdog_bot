import os
import ccxt
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("KUCOIN_API_KEY")
api_secret = os.getenv("KUCOIN_SECRET")
api_password = os.getenv("KUCOIN_PASSWORD")

kucoin = ccxt.kucoin({
    'apiKey': api_key,
    'secret': api_secret,
    'password': api_password,
    'enableRateLimit': True,
})

def test_kucoin():
    try:
        balance = kucoin.fetch_balance()
        usdt_balance = balance['free'].get('USDT', 0)
        print(f"✅ Connected successfully. USDT Balance: {usdt_balance}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_kucoin()
