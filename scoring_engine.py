import numpy as np

# Abbreviations for triggers/indicators
TRIGGER_ABBR = {
    "RSI_overbought": "rsi↑",
    "RSI_oversold": "rsi↓",
    "MACD_bullish": "macd+",
    "MACD_bearish": "macd-",
    "Stoch_overbought": "stoch↑",
    "Stoch_oversold": "stoch↓",
    "BB_breakout": "bb↑",
    "BB_squeeze": "bb<>",
    "RVOL_high": "rvol+",
    "VWAP_breakout": "vwap+",
    "EMA_bull_cross": "ema+",
    "EMA_bear_cross": "ema-",
    "SMA_bull_cross": "sma+",
    "SMA_bear_cross": "sma-",
    "ADX_strong": "adx+",
    "CCI_extreme": "cci!",
    "Donchian_breakout": "don+",
    "ATR_rising": "atr+",
    "Pivot_reject": "piv-",
    "Fib_reject": "fib-",
    "CMF_positive": "cmf+",
    "Keltner_breakout": "kc+",
    "WilliamsR_extreme": "wr!",
    "ROC_accel": "roc+",
    "TRIX_cross": "trix+",
    "PSAR_flip": "psar*",
    "Bull_Engulfing": "be",
    "Hammer": "ham",
    "Doji": "doji",
    # Bonus/Combo
    "RSI_MACD_combo": "rsi/macd",
    "VWAP_RVOL_combo": "vwap/rvol",
    "BB_MACD_combo": "bb/macd",
    "Stoch_Engulf_combo": "stoch/be",
}

def classify_status(score):
    if score >= 80:
        return "🔥 HOT"
    elif score >= 60:
        return "🚀 Pump"
    elif score >= 30:
        return "🛌 Neutral"
    else:
        return "❄️ Cold"

def calculate_confidence(score, max_score=100):
    # Confidence as a percent of the max possible score
    return round(100 * score / max_score)

def extract_triggers(indicators, combos):
    """Return list of short trigger codes for all tripped signals."""
    triggers = []
    for key, val in indicators.items():
        # Only abbreviate base triggers for display
        for abbr_key in TRIGGER_ABBR:
            if key.startswith(abbr_key) and val:
                triggers.append(TRIGGER_ABBR[abbr_key])
    for key, val in combos.items():
        if val and key in TRIGGER_ABBR:
            triggers.append(TRIGGER_ABBR[key])
    return triggers

def score_indicators(all_tf_indicators, combo_signals):
    """
    all_tf_indicators: dict of indicators across all timeframes, e.g.
        {
            "RSI_5m": 72, "RSI_15m": 68, ...,
            "MACD_5m_bullish": True, ...
        }
    combo_signals: dict of boolean combo signals, e.g. {"RSI_MACD_combo": True}
    """
    score = 0
    triggers = {}

    # --------- RSI ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        rsi = all_tf_indicators.get(f"RSI_{tf}")
        if rsi is not None:
            if rsi > 70:
                score += 3
                triggers[f"RSI_overbought_{tf}"] = True
            elif rsi < 30:
                score += 5
                triggers[f"RSI_oversold_{tf}"] = True

    # --------- MACD ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"MACD_bullish_{tf}"):
            score += 4
            triggers[f"MACD_bullish_{tf}"] = True
        if all_tf_indicators.get(f"MACD_bearish_{tf}"):
            score -= 3
            triggers[f"MACD_bearish_{tf}"] = True

    # --------- Stochastic Oscillator ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        stoch = all_tf_indicators.get(f"Stoch_{tf}")
        if stoch is not None:
            if stoch > 80:
                score -= 2
                triggers[f"Stoch_overbought_{tf}"] = True
            elif stoch < 20:
                score += 2
                triggers[f"Stoch_oversold_{tf}"] = True

    # --------- Bollinger Bands ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"BB_breakout_{tf}"):
            score += 6
            triggers[f"BB_breakout_{tf}"] = True
        if all_tf_indicators.get(f"BB_squeeze_{tf}"):
            score += 2
            triggers[f"BB_squeeze_{tf}"] = True

    # --------- Volume ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"RVOL_high_{tf}"):
            score += 5
            triggers[f"RVOL_high_{tf}"] = True

    # --------- VWAP ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"VWAP_breakout_{tf}"):
            score += 6
            triggers[f"VWAP_breakout_{tf}"] = True

    # --------- EMA/SMA Crosses ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"EMA_bull_cross_{tf}"):
            score += 4
            triggers[f"EMA_bull_cross_{tf}"] = True
        if all_tf_indicators.get(f"EMA_bear_cross_{tf}"):
            score -= 2
            triggers[f"EMA_bear_cross_{tf}"] = True
        if all_tf_indicators.get(f"SMA_bull_cross_{tf}"):
            score += 3
            triggers[f"SMA_bull_cross_{tf}"] = True
        if all_tf_indicators.get(f"SMA_bear_cross_{tf}"):
            score -= 2
            triggers[f"SMA_bear_cross_{tf}"] = True

    # --------- ADX ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        adx = all_tf_indicators.get(f"ADX_{tf}")
        if adx is not None and adx > 25:
            score += 3
            triggers[f"ADX_strong_{tf}"] = True

    # --------- CCI ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        cci = all_tf_indicators.get(f"CCI_{tf}")
        if cci is not None and abs(cci) > 200:
            score += 2
            triggers[f"CCI_extreme_{tf}"] = True

    # --------- Donchian ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"Donchian_breakout_{tf}"):
            score += 4
            triggers[f"Donchian_breakout_{tf}"] = True

    # --------- ATR ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"ATR_rising_{tf}"):
            score += 2
            triggers[f"ATR_rising_{tf}"] = True

    # --------- Pivot/Fib ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"Pivot_reject_{tf}"):
            score -= 2
            triggers[f"Pivot_reject_{tf}"] = True
        if all_tf_indicators.get(f"Fib_reject_{tf}"):
            score -= 2
            triggers[f"Fib_reject_{tf}"] = True

    # --------- CMF ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"CMF_positive_{tf}"):
            score += 3
            triggers[f"CMF_positive_{tf}"] = True

    # --------- Keltner ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"Keltner_breakout_{tf}"):
            score += 3
            triggers[f"Keltner_breakout_{tf}"] = True

    # --------- Williams %R ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        wr = all_tf_indicators.get(f"WilliamsR_{tf}")
        if wr is not None and (wr > -10 or wr < -90):
            score += 2
            triggers[f"WilliamsR_extreme_{tf}"] = True

    # --------- ROC ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        roc = all_tf_indicators.get(f"ROC_{tf}")
        if roc is not None and abs(roc) > 3:
            score += 2
            triggers[f"ROC_accel_{tf}"] = True

    # --------- TRIX ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"TRIX_cross_{tf}"):
            score += 3
            triggers[f"TRIX_cross_{tf}"] = True

    # --------- PSAR ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"PSAR_flip_{tf}"):
            score += 2
            triggers[f"PSAR_flip_{tf}"] = True

    # --------- Candlestick Patterns ---------
    for tf in ["5m", "15m", "1h", "4h"]:
        if all_tf_indicators.get(f"Bull_Engulfing_{tf}"):
            score += 2
            triggers[f"Bull_Engulfing_{tf}"] = True
        if all_tf_indicators.get(f"Hammer_{tf}"):
            score += 2
            triggers[f"Hammer_{tf}"] = True
        if all_tf_indicators.get(f"Doji_{tf}"):
            score += 1
            triggers[f"Doji_{tf}"] = True

    # --------- Bonus Combos ---------
    for key, active in combo_signals.items():
        if active:
            # Each combo can boost score strongly
            if key == "RSI_MACD_combo":
                score += 10
            elif key == "VWAP_RVOL_combo":
                score += 8
            elif key == "BB_MACD_combo":
                score += 7
            elif key == "Stoch_Engulf_combo":
                score += 6

    return score, triggers

def estimate_pump_time(score, high_rvol=False):
    # Simple rule: higher score and RVOL = shorter/faster pump
    if score > 80 and high_rvol:
        return "5m"
    elif score > 60:
        return "15m"
    elif score > 40:
        return "30m"
    else:
        return "60m"

def scoring_engine(all_tf_indicators, combo_signals, age, ml_pred=None):
    score, triggers = score_indicators(all_tf_indicators, combo_signals)
    status = classify_status(score)
    confidence = calculate_confidence(score)
    high_rvol = any(all_tf_indicators.get(f"RVOL_high_{tf}") for tf in ["5m", "15m", "1h", "4h"])
    pump_time = estimate_pump_time(score, high_rvol)
    # Add ML prediction as confidence boost
    if ml_pred is not None:
        confidence = int(0.7 * confidence + 0.3 * (ml_pred * 100))
    return {
        "score": score,
        "status": status,
        "confidence": confidence,
        "pump_time": pump_time,
        "age": age,
        "triggers": extract_triggers(triggers, combo_signals),
    }
