import ccxt
import pandas as pd

def get_all_symbols():
    """
    Get all USDT trading pairs from KuCoin.
    """
    exchange = ccxt.kucoin()
    markets = exchange.load_markets()
    return [symbol for symbol in markets if symbol.endswith('/USDT')]

def fetch_ohlcv_for_symbol(symbol, timeframe="15m", limit=500):
    """
    Fetch OHLCV data for a symbol from KuCoin.
    Returns a pandas DataFrame.
    """
    exchange = ccxt.kucoin()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    # Convert timestamp from ms to readable datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df
