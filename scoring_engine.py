import pandas as pd
import numpy as np

class ForwardPumpScorer:
    """
    Scoring engine for forward price movement with bonus logic for combined signals.
    Pass in a pandas DataFrame (OHLCV & indicator columns) for one coin,
    returns a score and detailed breakdown.
    """

    def __init__(self, indicator_weights=None, bonus_weights=None):
        self.indicator_weights = indicator_weights or {
            "sma_bullish": 2,
            "ema_bullish": 2,
            "macd_bullish": 3,
            "rsi_bullish": 2,
            "stoch_bullish": 1,
            "adx_strong": 2,
            "boll_breakout": 1,
            "atr_rising": 1,
            "donchian_breakout": 1,
            "keltner_breakout": 1,
            "obv_rising": 1,
            "vwap_above": 1,
            "cmf_positive": 1,
            "accdist_up": 1,
            "pivot_break": 1,
            "fibo_support": 1,
            "candlestick_bull": 2,
            "cci_bullish": 1,
            "williams_bullish": 1,
            "roc_rising": 1,
            "trix_bullish": 1,
            "golden_cross": 5,
        }
        self.bonus_weights = bonus_weights or {
            "price_volume_surge": 4,
            "macd_rsi_agree": 3,
            "multi_trend_agree": 2,
            "bullish_engulf_and_rising": 3,
            "boll_and_vwap_agree": 2,
        }

    def score_coin(self, data: pd.DataFrame) -> dict:
        last = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else last

        breakdown = {}
        score = 0

        breakdown['sma_bullish'] = int(last['SMA_20'] > last['SMA_50'])
        breakdown['ema_bullish'] = int(last['EMA_12'] > last['EMA_26'])
        breakdown['macd_bullish'] = int(last['MACD'] > last['MACD_signal'])
        breakdown['rsi_bullish'] = int(last['RSI'] > 55 and last['RSI'] < 75)
        breakdown['stoch_bullish'] = int(last['Stoch_K'] > last['Stoch_D'])
        breakdown['adx_strong'] = int(last['ADX'] > 25 and last['+DI'] > last['-DI'])
        breakdown['boll_breakout'] = int(last['close'] > last['Bollinger_upper'])
        breakdown['atr_rising'] = int(last['ATR'] > prev['ATR'])
        breakdown['donchian_breakout'] = int(last['close'] > last['Donchian_upper'])
        breakdown['keltner_breakout'] = int(last['close'] > last['Keltner_upper'])
        breakdown['obv_rising'] = int(last['OBV'] > prev['OBV'])
        breakdown['vwap_above'] = int(last['close'] > last['VWAP'])
        breakdown['cmf_positive'] = int(last['CMF'] > 0.05)
        breakdown['accdist_up'] = int(last['AccDist'] > prev['AccDist'])
        breakdown['pivot_break'] = int(last['close'] > last['pivot_point'])
        breakdown['fibo_support'] = int(abs(last['close'] - last['fibo_support']) < 0.01 * last['close'])
        breakdown['candlestick_bull'] = int(last['candle_pattern'] in ['Bullish Engulfing', 'Hammer'])
        breakdown['cci_bullish'] = int(last['CCI'] > 100)
        breakdown['williams_bullish'] = int(last['Williams_%R'] > -20)
        breakdown['roc_rising'] = int(last['ROC'] > 0)
        breakdown['trix_bullish'] = int(last['TRIX'] > 0)

        breakdown['golden_cross'] = int(prev['SMA_50'] < prev['SMA_200'] and last['SMA_50'] >= last['SMA_200'])

        for ind, present in breakdown.items():
            score += present * self.indicator_weights.get(ind, 0)

        bonus = {}
        bonus['price_volume_surge'] = int(
            (last['close'] > prev['close'] * 1.02) and (last['volume'] > prev['volume'] * 1.5)
        )
        bonus['macd_rsi_agree'] = int(breakdown['macd_bullish'] and breakdown['rsi_bullish'])
        n_trend = sum([breakdown['sma_bullish'], breakdown['ema_bullish'], breakdown['adx_strong']])
        bonus['multi_trend_agree'] = int(n_trend >= 2)
        bonus['bullish_engulf_and_rising'] = int(
            last['candle_pattern'] == "Bullish Engulfing" and last['close'] > prev['close']
        )
        bonus['boll_and_vwap_agree'] = int(breakdown['boll_breakout'] and breakdown['vwap_above'])

        for b, present in bonus.items():
            score += present * self.bonus_weights.get(b, 0)

        return {
            "score": score,
            "indicator_breakdown": breakdown,
            "bonus_breakdown": bonus,
        }
