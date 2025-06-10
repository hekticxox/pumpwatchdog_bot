def calculate_score(indicators: dict, df) -> tuple:
    """
    Accepts a dictionary of indicators (from ta_engine.calculate_all_indicators)
    and the raw DataFrame, and returns a (score, meta) tuple.
    The score is a float, meta is a summary string for the dashboard/alerts.
    """
    score = 0
    meta = []

    # Assign points for each indicator (customize as needed)
    if indicators.get("volume_breakout"):
        score += 20
        meta.append("VOL")

    if indicators.get("golden_cross"):
        score += 15
        meta.append("GC")

    if indicators.get("macd_bull"):
        score += 10
        meta.append("MACD")

    if indicators.get("rsi_oversold"):
        score += 8
        meta.append("RSI")

    if indicators.get("pullback_volume_spike"):
        score += 5
        meta.append("PB")

    if indicators.get("bullish_candle"):
        score += 4
        meta.append("BULL")

    if indicators.get("breakout_consolidation"):
        score += 10
        meta.append("BRK")

    if indicators.get("stoch_rsi_cross"):
        score += 6
        meta.append("STOCH")

    if indicators.get("selling_pressure_div"):
        score -= 5
        meta.append("BEAR DIV")

    if indicators.get("vwap_bounce"):
        score += 7
        meta.append("VWAP")

    # Example: add a bonus for fast price move (last 15m)
    try:
        pct_change = ((df["close"].iloc[-1] - df["close"].iloc[-4]) / df["close"].iloc[-4]) * 100
        if pct_change > 3:
            score += 5
            meta.append("3%/15m")
    except Exception:
        pass

    # Compose meta string, e.g.: "VOL,MACD,BULL"
    meta_str = ",".join(meta)

    return score, meta_str

# If you want a CLI test:
if __name__ == "__main__":
    # Fake example (for testing)
    indicators = {
        "volume_breakout": True,
        "golden_cross": False,
        "macd_bull": True,
        "rsi_oversold": False,
        "pullback_volume_spike": True,
        "bullish_candle": True,
        "breakout_consolidation": False,
        "stoch_rsi_cross": False,
        "selling_pressure_div": False,
        "vwap_bounce": True
    }
    # You'd pass a real pandas DataFrame in real use
    import pandas as pd
    import numpy as np
    # Fake DataFrame for test
    df = pd.DataFrame({
        "close": np.linspace(100, 120, 20)
    })
    score, meta = calculate_score(indicators, df)
    print(f"Score: {score}, Meta: {meta}")
