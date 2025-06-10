import pandas as pd
from typing import Optional

def estimate_pump_duration(df: Optional[pd.DataFrame]) -> int:
    """
    Estimates how long a bullish move ("pump") may last based on price and volume dynamics.

    Args:
        df (Optional[pd.DataFrame]): DataFrame with OHLCV and (optionally) TA indicator columns.

    Returns:
        int: Estimated duration in minutes (rounded to nearest 5).
    """
    if df is None or len(df) < 20:
        return 0

    # Example heuristic: duration increases with higher recent volume spikes and price momentum
    try:
        price_change = df["close"].iloc[-1] - df["close"].iloc[-10]
        perc_change = 100 * price_change / df["close"].iloc[-10]
        recent_vol = df["volume"].iloc[-10:].mean()
        all_vol = df["volume"].mean()
        vol_ratio = recent_vol / all_vol if all_vol > 0 else 0

        # Simple scoring logic (tweak as needed)
        duration = 0
        if perc_change > 5 and vol_ratio > 1.5:
            duration = 60
        elif perc_change > 3 and vol_ratio > 1.2:
            duration = 30
        elif perc_change > 2 and vol_ratio > 1.0:
            duration = 15
        elif perc_change > 1 and vol_ratio > 0.8:
            duration = 5

        # Clamp to nearest 5, 1 <= duration <= 120
        duration = max(0, min(int(round(duration / 5) * 5), 120))
        return duration
    except Exception as e:
        print(f"[pump_life] Error estimating duration: {e}")
        return 0

if __name__ == "__main__":
    # Example usage
    import numpy as np
    data = {
        "close": np.linspace(1, 1.5, 30),
        "volume": np.random.normal(1000, 200, 30)
    }
    df = pd.DataFrame(data)
    print("Estimated pump duration (min):", estimate_pump_duration(df))
