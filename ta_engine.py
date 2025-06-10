import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator, CCIIndicator, TRIXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange, DonchianChannel, KeltnerChannel
from ta.volume import OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator, AccDistIndexIndicator
from ta.volume import VolumeWeightedAveragePrice

def calculate_pivot_levels(df):
    # Classic Pivot Point
    high = df['high'].iloc[-2]
    low = df['low'].iloc[-2]
    close = df['close'].iloc[-2]
    pivot = (high + low + close) / 3
    support = pivot - (high - low)
    resistance = pivot + (high - low)
    return pivot, support, resistance

def detect_candle_pattern(df):
    # Simple example: Bullish engulfing and Hammer
    if len(df) < 2:
        return "None"
    last = df.iloc[-1]
    prev = df.iloc[-2]
    pattern = "None"
    # Bullish Engulfing: current bullish, body engulfs previous candle
    if last['close'] > last['open'] and prev['close'] < prev['open']:
        if last['close'] > prev['open'] and last['open'] < prev['close']:
            pattern = "Bullish Engulfing"
    # Hammer
    body = abs(last['close'] - last['open'])
    lower_shadow = last['open'] - last['low'] if last['open'] > last['close'] else last['close'] - last['low']
    upper_shadow = last['high'] - last['close'] if last['close'] > last['open'] else last['high'] - last['open']
    if body < lower_shadow and lower_shadow > 2*body and upper_shadow < body:
        pattern = "Hammer"
    return pattern

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all indicators needed for scoring_engine.py.
    Expects df with columns: open, high, low, close, volume
    Returns df with extra columns.
    """
    df = df.copy()

    # --- Trend Indicators
    df['SMA_20'] = SMAIndicator(df['close'], window=20, fillna=True).sma_indicator()
    df['SMA_50'] = SMAIndicator(df['close'], window=50, fillna=True).sma_indicator()
    df['SMA_200'] = SMAIndicator(df['close'], window=200, fillna=True).sma_indicator()
    df['EMA_12'] = EMAIndicator(df['close'], window=12, fillna=True).ema_indicator()
    df['EMA_26'] = EMAIndicator(df['close'], window=26, fillna=True).ema_indicator()

    macd = MACD(df['close'], window_slow=26, window_fast=12, window_sign=9, fillna=True)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()

    df['RSI'] = RSIIndicator(df['close'], window=14, fillna=True).rsi()
    stoch = StochasticOscillator(df['high'], df['low'], df['close'], window=14, smooth_window=3, fillna=True)
    df['Stoch_K'] = stoch.stoch()
    df['Stoch_D'] = stoch.stoch_signal()

    adx = ADXIndicator(df['high'], df['low'], df['close'], window=14, fillna=True)
    df['ADX'] = adx.adx()
    df['+DI'] = adx.adx_pos()
    df['-DI'] = adx.adx_neg()

    df['CCI'] = CCIIndicator(df['high'], df['low'], df['close'], window=20, fillna=True).cci()
    df['TRIX'] = TRIXIndicator(df['close'], window=15, fillna=True).trix()

    # --- Volatility/Bands
    boll = BollingerBands(df['close'], window=20, window_dev=2, fillna=True)
    df['Bollinger_upper'] = boll.bollinger_hband()

    df['ATR'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14, fillna=True).average_true_range()

    # FIX: DonchianChannel requires high, low, **close**
    donch = DonchianChannel(high=df['high'], low=df['low'], close=df['close'], window=20, fillna=True)
    df['Donchian_upper'] = donch.donchian_channel_hband()

    kelt = KeltnerChannel(high=df['high'], low=df['low'], close=df['close'], window=20, fillna=True)
    df['Keltner_upper'] = kelt.keltner_channel_hband()

    # --- Volume & Order Flow
    df['OBV'] = OnBalanceVolumeIndicator(df['close'], df['volume'], fillna=True).on_balance_volume()
    df['VWAP'] = VolumeWeightedAveragePrice(
        high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=14, fillna=True
    ).volume_weighted_average_price()
    df['CMF'] = ChaikinMoneyFlowIndicator(
        high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=20, fillna=True
    ).chaikin_money_flow()
    df['AccDist'] = AccDistIndexIndicator(df['high'], df['low'], df['close'], df['volume'], fillna=True).acc_dist_index()

    # --- Price Action & Oscillators
    df['Williams_%R'] = WilliamsRIndicator(df['high'], df['low'], df['close'], lbp=14, fillna=True).williams_r()
    df['ROC'] = ROCIndicator(df['close'], window=10, fillna=True).roc()

    # --- Candle Pattern (very simple)
    df['candle_pattern'] = "None"
    if len(df) > 2:
        df.iloc[-1, df.columns.get_loc('candle_pattern')] = detect_candle_pattern(df)

    # --- Pivot/Fibonacci
    pivot, fibo_support, _ = calculate_pivot_levels(df)
    df['pivot_point'] = pivot
    df['fibo_support'] = fibo_support

    return df
