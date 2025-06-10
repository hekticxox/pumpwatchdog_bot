import ccxt
import pandas as pd
import os
import time
import sys

# Verbose flag for detailed logging
VERBOSE = '--verbose' in sys.argv

KUCOIN_API_KEY = os.getenv("KUCOIN_API_KEY")
KUCOIN_SECRET = os.getenv("KUCOIN_SECRET")
KUCOIN_PASSWORD = os.getenv("KUCOIN_PASSWORD")

def get_kucoin():
    params = {}
    if KUCOIN_API_KEY and KUCOIN_SECRET and KUCOIN_PASSWORD:
        params = {
            'apiKey': KUCOIN_API_KEY,
            'secret': KUCOIN_SECRET,
            'password': KUCOIN_PASSWORD,
        }
    return ccxt.kucoin(params) if params else ccxt.kucoin()

exchange = get_kucoin()

def get_all_symbols(quote='USDT', top_n=100, timeframe='15m', limit=30):
    """
    Return the top N symbols ending in /USDT by recent volume.
    Volume is calculated as the sum of the last 30 candles on the specified timeframe.
    """
    markets = exchange.load_markets()
    symbols = [
        s for s in markets
        if s.endswith('/' + quote)
        and markets[s]['active']
        and markets[s]['spot']
    ]

    volumes = []
    for sym in symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(sym, timeframe=timeframe, limit=limit)
            if not ohlcv or len(ohlcv) == 0:
                continue
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            total_vol = df['volume'].sum()
            volumes.append((sym, total_vol))
        except Exception as e:
            if VERBOSE:
                print(f"[scanner] Volume fetch error for {sym}: {e}")
            continue

    # Sort descending by volume
    volumes.sort(key=lambda tup: tup[1], reverse=True)

    # Return only symbol names, sorted
    top_symbols = [s[0] for s in volumes[:top_n]]
    if VERBOSE:
        print(f"[scanner] Top {top_n} by volume: {top_symbols}")
    return top_symbols

def fetch_ohlcv_for_symbol(symbol, timeframe='15m', limit=100, max_retries=3, pause=1.0):
    """
    Fetch OHLCV for a single symbol as a pandas DataFrame.
    Returns None on failure.
    """
    for attempt in range(max_retries):
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            if not ohlcv:
                return None
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            # Convert ms to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except ccxt.NetworkError as e:
            if VERBOSE:
                print(f"[scanner] NetworkError on {symbol} (attempt {attempt+1}): {e}")
            time.sleep(pause)
        except ccxt.BaseError as e:
            if VERBOSE:
                print(f"[scanner] CCXT error on {symbol} (attempt {attempt+1}): {e}")
            return None
        except Exception as e:
            if VERBOSE:
                print(f"[scanner] Unknown error on {symbol}: {e}")
            return None
    return None

def fetch_ohlcv_for_symbol_multi_timeframes(symbol, timeframes=['15m','1h'], limit=100):
    """
    Fetch OHLCV for a symbol in multiple timeframes.
    Returns a dict: { timeframe: DataFrame }
    """
    dfs = {}
    for tf in timeframes:
        df = fetch_ohlcv_for_symbol(symbol, timeframe=tf, limit=limit)
        dfs[tf] = df
    return dfs
