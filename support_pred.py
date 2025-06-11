import ccxt
import pandas as pd

def fetch_ohlcv(symbol, timeframe='1h', limit=200, exchange_name='kucoin'):
    """
    Fetches OHLCV data for the given symbol and timeframe from the specified exchange.
    """
    exchange = getattr(ccxt, exchange_name)()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    return df

def predict_next_support(symbol, timeframe='1h', lookback=100, exchange_name='kucoin'):
    """
    Predicts the next likely support level for the symbol on the given timeframe.
    Returns the nearest historical support below the current price, or the all-time low if none.
    """
    df = fetch_ohlcv(symbol, timeframe, limit=lookback+10, exchange_name=exchange_name)
    if df is None or df.empty:
        print("No data available.")
        return None

    current_price = df['close'].iloc[-1]
    lows = df['low'].tolist()
    swing_lows = []
    for i in range(1, len(lows) - 1):
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            swing_lows.append(lows[i])
    supports_below = [lvl for lvl in swing_lows if lvl < current_price]
    if supports_below:
        next_support = max(supports_below)
    else:
        next_support = min(lows)
    return next_support

if __name__ == "__main__":
    print("Enter the coin symbol (e.g., ANIME):")
    user_coin = input().strip().upper()
    symbol = f"{user_coin}/USDT"
    support = predict_next_support(symbol, timeframe='1h')
    if support:
        print(f"Predicted next support for {symbol}: {support:.6f} USDT")
    else:
        print("Could not determine support level.")
