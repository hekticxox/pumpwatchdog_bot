import ccxt
import pandas as pd

def get_all_symbols():
    """
    Returns a list of all symbols to scan (e.g., ['BTC/USDT', 'ETH/USDT', ...])
    """
    exchange = ccxt.kucoin()
    markets = exchange.load_markets()
    # Only spot, active, quote=USDT
    symbols = [s for s in markets if
               '/USDT' in s and markets[s]['active'] and markets[s]['spot']]
    return symbols

def fetch_ohlcv_for_symbol(symbol, limit=250):
    """
    Fetches OHLCV data for a given symbol using ccxt. Returns pandas DataFrame.
    """
    exchange = ccxt.kucoin()
    try:
        # 1m or 5m candles; adjust timeframe as needed
        bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None
