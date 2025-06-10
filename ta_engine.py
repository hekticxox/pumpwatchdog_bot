import numpy as np
import pandas as pd
import ta

def calculate_all_indicators(df, df_1h=None):
    indicators = {}

    # --- Classic TA ---
    indicators['RSI'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    indicators['MACD'] = ta.trend.MACD(df['close']).macd_diff().iloc[-1]
    indicators['STOCH'] = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close']).stoch().iloc[-1]
    indicators['VWAP'] = vwap(df)
    indicators['EMA21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator().iloc[-1]
    indicators['EMA50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator().iloc[-1]
    indicators['BULL'] = df['close'].iloc[-1] > df['open'].iloc[-1]
    indicators['PB'] = price_breakout(df)
    indicators['VOL'] = df['volume'].iloc[-1]

    # --- Relative Volume (RVOL) ---
    if len(df) >= 21:
        indicators['RVOL'] = df['volume'].iloc[-1] / df['volume'].iloc[-21:-1].mean()
    else:
        indicators['RVOL'] = 1

    # --- Multi-Timeframe Confluence (if 1h data passed) ---
    if df_1h is not None:
        bullish_1h = df_1h['close'].iloc[-1] > df_1h['open'].iloc[-1]
        indicators['MTF_BULL'] = bullish_1h

    # --- Divergence ---
    indicators['RSI_DIVERGENCE'] = detect_rsi_bull_divergence(df)
    indicators['MACD_DIVERGENCE'] = detect_macd_bull_divergence(df)

    # --- Candle Patterns ---
    indicators['HAMMER'] = is_hammer(df.iloc[-1])
    indicators['ENGULFING'] = is_bullish_engulfing(df)

    # --- Breakout & Retest ---
    indicators['RETEST'] = breakout_retest(df)

    # --- Simple Pattern (Triangle/Flag) ---
    indicators['TRIANGLE'] = detect_triangle(df)

    # --- Pre-pump: volume or volatility surge without price move ---
    price_chg = (df['close'].iloc[-1] - df['close'].iloc[-4]) / df['close'].iloc[-4] if len(df) >= 4 else 0
    indicators['PREPUMP'] = (
        indicators['RVOL'] > 2.0 and abs(price_chg) < 0.01
    )

    # --- Signal triggers (for dashboard clarity) ---
    # Each indicator returns True if the bullish condition is met:
    signal_triggers = {
        'RSI_DIVERGENCE': indicators['RSI_DIVERGENCE'],
        'MACD_DIVERGENCE': indicators['MACD_DIVERGENCE'],
        'RVOL': indicators['RVOL'] > 2.0,
        'MTF_BULL': indicators.get('MTF_BULL', False),
        'HAMMER': indicators['HAMMER'],
        'ENGULFING': indicators['ENGULFING'],
        'RETEST': indicators['RETEST'],
        'PB': indicators['PB'],
        'BULL': indicators['BULL'],
        'TRIANGLE': indicators['TRIANGLE'],
        'PREPUMP': indicators['PREPUMP'],
        'MACD': indicators['MACD'] > 0,
        'STOCH': indicators['STOCH'] > 80,
        'VWAP': df['close'].iloc[-1] > indicators['VWAP'],
    }
    indicators['signal_triggers'] = signal_triggers
    return signal_triggers

# --- Helper Functions Below ---

def vwap(df):
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    return (typical_price * df['volume']).cumsum().iloc[-1] / df['volume'].cumsum().iloc[-1]

def price_breakout(df, window=20):
    if len(df) < window + 1:
        return False
    recent_high = df['high'].iloc[-window:-1].max()
    return df['close'].iloc[-1] > recent_high

def detect_rsi_bull_divergence(df, lookback=15):
    closes = df['close'].iloc[-lookback:]
    rsis = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-lookback:]
    if len(closes) < 5 or rsis.isnull().any():
        return False
    price_ll = closes.idxmin()
    rsi_ll = rsis.idxmin()
    # Bullish divergence: price lower low, RSI higher low
    return price_ll != rsi_ll and closes[price_ll] < closes.iloc[0] and rsis[price_ll] > rsis.iloc[0]

def detect_macd_bull_divergence(df, lookback=15):
    closes = df['close'].iloc[-lookback:]
    macd_vals = ta.trend.MACD(df['close']).macd_diff().iloc[-lookback:]
    if len(closes) < 5 or macd_vals.isnull().any():
        return False
    price_ll = closes.idxmin()
    macd_ll = macd_vals.idxmin()
    return price_ll != macd_ll and closes[price_ll] < closes.iloc[0] and macd_vals[price_ll] > macd_vals.iloc[0]

def is_hammer(row):
    body = abs(row['close'] - row['open'])
    lower_shadow = min(row['close'], row['open']) - row['low']
    upper_shadow = row['high'] - max(row['close'], row['open'])
    return lower_shadow > 2 * body and body > 0 and upper_shadow < body

def is_bullish_engulfing(df):
    if len(df) < 2:
        return False
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    prev_bear = prev['close'] < prev['open']
    curr_bull = curr['close'] > curr['open']
    engulf = curr['close'] > prev['open'] and curr['open'] < prev['close']
    return prev_bear and curr_bull and engulf

def breakout_retest(df, window=20):
    if len(df) < window + 2:
        return False
    recent_high = df['high'].iloc[-window:-2].max()
    breakout = df['close'].iloc[-2] > recent_high
    retest = abs(df['low'].iloc[-1] - recent_high) / recent_high < 0.01
    return breakout and retest

def detect_triangle(df, window=15):
    # Simple: higher lows and lower highs over last window
    closes = df['close'].iloc[-window:]
    lows = df['low'].iloc[-window:]
    highs = df['high'].iloc[-window:]
    # Check strictly increasing lows and strictly decreasing highs
    lows_increasing = all(x < y for x, y in zip(lows, lows[1:]))
    highs_decreasing = all(x > y for x, y in zip(highs, highs[1:]))
    return lows_increasing and highs_decreasing
