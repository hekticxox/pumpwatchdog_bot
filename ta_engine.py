import pandas as pd
import numpy as np
from ta.momentum import (
    RSIIndicator, StochasticOscillator, ROCIndicator, WilliamsRIndicator, KAMAIndicator
)
from ta.trend import (
    MACD, EMAIndicator, ADXIndicator, CCIIndicator, TRIXIndicator
)
from ta.volatility import (
    BollingerBands, AverageTrueRange, DonchianChannel, KeltnerChannel
)
from ta.volume import (
    OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator, VolumeWeightedAveragePrice
)

class TAEngine:
    def __init__(self):
        # Indicator weights (sum to 100 or less, combos can add more)
        self.weights = {
            # Core
            "rsi_bull": 5,
            "rsi_oversold": 3,
            "stoch_rsi": 5,
            "macd_cross": 7,
            "ema_fast_slow": 7,
            "boll_break": 4,
            "boll_squeeze": 3,
            "adx_strong": 5,
            "cci_bull": 3,
            "williams_r": 3,
            "cmf": 3,
            "obv": 3,
            "atr_vol": 2,
            "roc": 3,
            # "mfi": 3,  # Money Flow Index removed due to missing import
            "donchian_break": 2,
            "keltner_break": 2,
            "trix": 2,
            "kama_trend": 2,
            "vwap_pos": 2,
            # Combo
            "combo_bonus": 14,  # For strong multi-signal confluence
        }

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Core
        df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
        stoch = StochasticOscillator(df['high'], df['low'], df['close'])
        df['stoch_rsi'] = stoch.stoch()
        macd = MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        df['ema_fast'] = EMAIndicator(df['close'], window=8).ema_indicator()
        df['ema_slow'] = EMAIndicator(df['close'], window=21).ema_indicator()
        # Bollinger Bands
        boll = BollingerBands(df['close'], window=20, window_dev=2)
        df['boll_upper'] = boll.bollinger_hband()
        df['boll_lower'] = boll.bollinger_lband()
        df['boll_width'] = df['boll_upper'] - df['boll_lower']
        df['boll_break'] = (df['close'] > df['boll_upper']).astype(int)
        df['boll_squeeze'] = (df['boll_width'] < df['boll_width'].rolling(100).quantile(0.15)).astype(int)
        # ADX
        adx = ADXIndicator(df['high'], df['low'], df['close'], window=14)
        df['adx'] = adx.adx()
        # CCI
        df['cci'] = CCIIndicator(df['high'], df['low'], df['close'], window=20).cci()
        # Williams %R
        df['williams_r'] = WilliamsRIndicator(df['high'], df['low'], df['close'], lbp=14).williams_r()
        # Chaikin Money Flow
        df['cmf'] = ChaikinMoneyFlowIndicator(df['high'], df['low'], df['close'], df['volume'], window=20).chaikin_money_flow()
        # OBV
        df['obv'] = OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
        # ATR
        df['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        # ROC
        df['roc'] = ROCIndicator(df['close'], window=12).roc()
        # Donchian Channels (now includes 'close')
        donchian = DonchianChannel(df['high'], df['low'], df['close'], window=20)
        df['donchian_high'] = donchian.donchian_channel_hband()
        df['donchian_low'] = donchian.donchian_channel_lband()
        df['donchian_break'] = (df['close'] > df['donchian_high']).astype(int)
        # Keltner Channels
        kelt = KeltnerChannel(df['high'], df['low'], df['close'], window=20)
        df['keltner_high'] = kelt.keltner_channel_hband()
        df['keltner_low'] = kelt.keltner_channel_lband()
        df['keltner_break'] = (df['close'] > df['keltner_high']).astype(int)
        # TRIX
        trix = TRIXIndicator(df['close'], window=15)
        df['trix'] = trix.trix()
        # KAMA (Kaufman Adaptive Moving Average)
        kama = KAMAIndicator(df['close'], window=10, pow1=2, pow2=30)
        df['kama'] = kama.kama()
        df['kama_trend'] = (df['close'] > df['kama']).astype(int)
        # VWAP (Volume Weighted Average Price)
        vwap = VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'])
        df['vwap'] = vwap.volume_weighted_average_price()
        df['vwap_pos'] = (df['close'] > df['vwap']).astype(int)
        return df.dropna().reset_index(drop=True)

    def calculate_heat_score(self, df: pd.DataFrame) -> int:
        if df is None or len(df) < 30:
            return 0
        row = df.iloc[-1]
        score = 0
        # 1. Individual indicator scoring
        if 60 < row['rsi'] < 80:
            score += self.weights['rsi_bull']
        if row['rsi'] < 35:
            score += self.weights['rsi_oversold']
        if row['stoch_rsi'] > 80:
            score += self.weights['stoch_rsi']
        if row['macd'] > row['macd_signal'] and row['macd_diff'] > 0:
            score += self.weights['macd_cross']
        if row['ema_fast'] > row['ema_slow']:
            score += self.weights['ema_fast_slow']
        if row['boll_break']:
            score += self.weights['boll_break']
        if row['boll_squeeze']:
            score += self.weights['boll_squeeze']
        if row['adx'] > 25:
            score += self.weights['adx_strong']
        if row['cci'] > 100:
            score += self.weights['cci_bull']
        if row['williams_r'] > -20:
            score += self.weights['williams_r']
        if row['cmf'] > 0.1:
            score += self.weights['cmf']
        if row['obv'] > df['obv'].iloc[-2]:
            score += self.weights['obv']
        if row['atr'] > df['atr'].mean():
            score += self.weights['atr_vol']
        if row['roc'] > 4:
            score += self.weights['roc']
        # if row['mfi'] > 80:  # Money Flow Index removed
        #     score += self.weights['mfi']
        if row['donchian_break']:
            score += self.weights['donchian_break']
        if row['keltner_break']:
            score += self.weights['keltner_break']
        if row['trix'] > 0:
            score += self.weights['trix']
        if row['kama_trend']:
            score += self.weights['kama_trend']
        if row['vwap_pos']:
            score += self.weights['vwap_pos']

        # 2. Combo logic: award bonus if strong confluence
        strong_signals = sum([
            (60 < row['rsi'] < 80),
            row['stoch_rsi'] > 80,
            (row['macd'] > row['macd_signal'] and row['macd_diff'] > 0),
            row['ema_fast'] > row['ema_slow'],
            row['boll_break'],
            row['adx'] > 25,
            row['donchian_break'],
            row['keltner_break'],
            row['cmf'] > 0.1,
            row['obv'] > df['obv'].iloc[-2],
            row['roc'] > 4,
            # row['mfi'] > 80,  # Money Flow Index removed
        ])
        if strong_signals >= 5:
            score += self.weights['combo_bonus']

        # Clamp score to [0, 100]
        return min(100, score)
