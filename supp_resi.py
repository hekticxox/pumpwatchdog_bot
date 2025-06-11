import ccxt
import pandas as pd

def fetch_ohlcv(symbol, timeframe='1h', limit=200, exchange_name='kucoin'):
    exchange = getattr(ccxt, exchange_name)()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    return df

def find_supports(df, count=3):
    current_price = df['close'].iloc[-1]
    lows = df['low'].tolist()
    swing_lows = [lows[i] for i in range(1, len(lows)-1) if lows[i] < lows[i-1] and lows[i] < lows[i+1]]
    supports_below = sorted([lvl for lvl in swing_lows if lvl < current_price], reverse=True)
    return supports_below[:count]

def find_resistances(df, count=3):
    current_price = df['close'].iloc[-1]
    highs = df['high'].tolist()
    swing_highs = [highs[i] for i in range(1, len(highs)-1) if highs[i] > highs[i-1] and highs[i] > highs[i+1]]
    resistances_above = sorted([lvl for lvl in swing_highs if lvl > current_price])

    if resistances_above:
        return resistances_above[:count]
    else:
        # Fallback: Use Fibonacci extension
        lows = df['low'].tolist()
        recent_low = min(lows[-20:])
        recent_high = max(highs[-20:])
        diff = recent_high - recent_low
        fib_extensions = [1.272, 1.618, 2.0]
        predicted_resistances = [recent_high + (diff * ext) for ext in fib_extensions]
        return predicted_resistances[:count]

if __name__ == "__main__":
    print("Enter the coin symbol (e.g., ANIME):")
    user_coin = input().strip().upper()
    symbol = f"{user_coin}/USDT"

    df = fetch_ohlcv(symbol, timeframe='1h', limit=200, exchange_name='kucoin')
    if df is None or df.empty:
        print("No data available for this coin.")
    else:
        supports = find_supports(df)
        resistances = find_resistances(df)
        current_price = df['close'].iloc[-1]

        if supports:
            print(f"\n🔻 Top 3 Support Levels for {symbol}:")
            for i, lvl in enumerate(supports, 1):
                pct = ((current_price - lvl) / current_price) * 100
                print(f"  {i}. {lvl:.6f} USDT  ({pct:.2f}% below)")
        else:
            print("No valid support levels found.")

        if resistances:
            print(f"\n🔺 Top 3 Resistance Levels for {symbol}:")
            for i, lvl in enumerate(resistances, 1):
                pct = ((lvl - current_price) / current_price) * 100
                print(f"  {i}. {lvl:.6f} USDT  ({pct:.2f}% above)")
        else:
            print("No valid resistance levels found.")

