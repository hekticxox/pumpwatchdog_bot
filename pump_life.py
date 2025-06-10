import numpy as np

def estimate_pump_duration(df):
    """
    Estimate pump duration in minutes using a more advanced approach:
    - Uses last 15 bars for better trend detection.
    - Incorporates price trend, volume trend, volatility, and RSI.
    - Scales estimated life between 1 and 60 min based on combined score.
    """
    if len(df) < 15:
        return 0

    recent = df.iloc[-15:]
    vol_start = recent['volume'].iloc[0]
    vol_end = recent['volume'].iloc[-1]
    price_start = recent['close'].iloc[0]
    price_end = recent['close'].iloc[-1]

    # Prevent divide-by-zero
    vol_trend = (vol_end - vol_start) / vol_start if abs(vol_start) > 1e-8 else 0
    price_trend = (price_end - price_start) / price_start if abs(price_start) > 1e-8 else 0

    # Calculate volatility (stddev of close price)
    volatility = recent['close'].std() / recent['close'].mean() if recent['close'].mean() > 0 else 0

    # Use RSI if available, else fallback to basic calculation
    if 'rsi' in recent.columns:
        rsi_now = recent['rsi'].iloc[-1]
    else:
        # Basic RSI calculation for last 14 periods
        delta = recent['close'].diff()
        up = delta.clip(lower=0).mean()
        down = -delta.clip(upper=0).mean()
        rs = up / down if down != 0 else 0
        rsi_now = 100 - (100 / (1 + rs)) if rs != 0 else 50

    # Heuristic scoring (each component normalized/clipped)
    score = 0

    # Price trend: strong uptrend is good
    if price_trend > 0.10:
        score += 2
    elif price_trend > 0.05:
        score += 1
    elif price_trend < -0.04:
        score -= 1

    # Volume trend: sustained volume = longer pump
    if vol_trend > 0.5:
        score += 2
    elif vol_trend > 0.2:
        score += 1
    elif vol_trend < -0.1:
        score -= 1

    # Volatility: too high = possible dump soon
    if volatility > 0.05:
        score -= 1
    elif volatility < 0.02:
        score += 1

    # RSI: Overbought (RSI>80) or oversold (RSI<20) signals
    if 60 <= rsi_now <= 80:
        score += 2
    elif 50 <= rsi_now < 60:
        score += 1
    elif rsi_now > 85 or rsi_now < 25:
        score -= 1

    # Clamp score between -2 and 6
    score = max(-2, min(score, 6))

    # Map score to estimated duration
    # -2 → 1m, 0 → 5m, 2 → 15m, 4 → 30m, 6 → 60m
    duration_map = {
        -2: 1,
        -1: 3,
         0: 5,
         1: 10,
         2: 15,
         3: 20,
         4: 30,
         5: 45,
         6: 60
    }
    est_life = duration_map.get(score, 5)

    return est_life
