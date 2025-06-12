import os
import ccxt
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from ta import trend, momentum, volatility, volume

load_dotenv()

DEFAULT_WEIGHTS = {
    "EMA_CROSS": 3,
    "SMA_CROSS": 2,
    "MACD_BULL": 4,
    "RSI_HOLD": 2,
    "RSI_OVERBOUGHT": 2,
    "STOCH_BULL": 2,
    "ADX_BULL": 2,
    "BB_MID": 1,
    "ATR_SPIKE": 2,
    "DONCHIAN_BREAK": 2,
    "VWAP_HOLD": 1,
    "OBV_UP": 2,
    "CMF_FLOW": 1,
    "ADL_UP": 1,
    "CCI_BULL": 1,
    "WILLR_BULL": 1,
    "ROC_POS": 1,
    "TRIX_POS": 1,
    "MOM_POS": 1,
    "ZSCORE_SPIKE": 1,
    "FDI_TREND": 1,
    "VOLUME_SPIKE": 2,
    "CANDLE_ENGULF": 2,
    "BREAKOUT_20": 2,
    "COMBO_BONUS": 3,
}

class SignalEngine:
    def __init__(self, weights=None):
        self.weights = weights or DEFAULT_WEIGHTS
        self.exchange, self.ex_name = self._get_exchange()

    def _get_exchange(self):
        key = os.getenv("KUCOIN_API_KEY")
        secret = os.getenv("KUCOIN_SECRET")
        pw = os.getenv("KUCOIN_PASSWORD")
        if key and secret and pw:
            try:
                ku = ccxt.kucoin({'apiKey': key, 'secret': secret, 'password': pw, 'enableRateLimit': True})
                ku.load_markets()
                return ku, 'kucoin'
            except Exception:
                pass
        b = ccxt.binance({'enableRateLimit': True})
        b.load_markets()
        return b, 'binance'

    def fetch_ohlcv(self, symbol, tf="1h", limit=120):
        try:
            sym = symbol.replace("/", "") if self.ex_name == 'binance' else symbol
            return self.exchange.fetch_ohlcv(sym, timeframe=tf, limit=limit)
        except:
            return None

    def calc_confidence(self, symbol):
        try:
            sym = symbol.replace("/", "") if self.ex_name == 'binance' else symbol
            ob = self.exchange.fetch_order_book(sym)
            bids = ob.get('bids', [])[:20]
            asks = ob.get('asks', [])[:20]
            buy_vol = sum(p * a for p, a in bids)
            sell_vol = sum(p * a for p, a in asks)
            return int(round(100 * buy_vol / (buy_vol + sell_vol))) if buy_vol + sell_vol > 0 else 50
        except:
            return 50

    def _percent_change(self, prices, periods):
        return round(100 * (prices[-1] - prices[-(periods + 1)]) / prices[-(periods + 1)], 2)

    def score_signals(self, df):
        score = 0
        triggers = []

        def add(cond, name):
            nonlocal score
            if cond:
                score += self.weights.get(name, 0)
                triggers.append(name)

        # Add indicators
        add(df['ema9'].iloc[-1] > df['ema21'].iloc[-1], "EMA_CROSS")
        add(df['sma10'].iloc[-1] > df['sma20'].iloc[-1], "SMA_CROSS")
        add(df['macd'].iloc[-2] < df['macdsignal'].iloc[-2] and df['macd'].iloc[-1] > df['macdsignal'].iloc[-1], "MACD_BULL")
        add(df['rsi'].iloc[-1] >= 60, "RSI_HOLD")
        add(df['rsi'].iloc[-1] > 70, "RSI_OVERBOUGHT")
        add(df['stoch_k'].iloc[-1] > df['stoch_d'].iloc[-1] and df['stoch_k'].iloc[-1] > 20, "STOCH_BULL")
        add(df['adx'].iloc[-1] > 25 and df['plus_di'].iloc[-1] > df['minus_di'].iloc[-1], "ADX_BULL")
        add(df['close'].iloc[-1] > df['bb_middle'].iloc[-1], "BB_MID")
        add(df['atr'].iloc[-1] > np.percentile(df['atr'].dropna(), 90), "ATR_SPIKE")
        add(df['close'].iloc[-1] > df['donchian_high'].iloc[-2], "DONCHIAN_BREAK")
        add(df['close'].iloc[-1] > df['vwap'].iloc[-1], "VWAP_HOLD")
        add(df['obv'].iloc[-1] > df['obv'].iloc[-2] > df['obv'].iloc[-3], "OBV_UP")
        add(df['cmf'].iloc[-1] > 0, "CMF_FLOW")
        add(df['ad'].iloc[-1] > df['ad'].iloc[-2], "ADL_UP")
        add(df['cci'].iloc[-1] > 100, "CCI_BULL")
        add(df['williamsr'].iloc[-1] > -50, "WILLR_BULL")
        add(df['roc'].iloc[-1] > 0, "ROC_POS")
        add(df['trix'].iloc[-1] > 0, "TRIX_POS")
        try:
            df['mom'] = momentum.awesome_oscillator(df['high'], df['low'])
        except AttributeError:
            df['mom'] = pd.Series(np.nan, index=df.index)
        add(df['mom'].iloc[-1] > 0, "MOM_POS")
        df['zscore'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).std()
        add(df['zscore'].iloc[-1] > 1, "ZSCORE_SPIKE")
        try:
            df['fdi'] = trend.fractal_dimension_index(df['close'], window=10)
        except Exception:
            df['fdi'] = pd.Series(np.nan, index=df.index)
        add(df['fdi'].iloc[-1] > 1.5, "FDI_TREND")
        add(df['volume'].iloc[-1] > np.percentile(df['volume'].dropna(), 80), "VOLUME_SPIKE")
        add(
            df['close'].iloc[-2] < df['open'].iloc[-2] and
            df['close'].iloc[-1] > df['open'].iloc[-1] and
            df['close'].iloc[-1] > df['open'].iloc[-2] and
            df['open'].iloc[-1] < df['close'].iloc[-2],
            "CANDLE_ENGULF"
        )
        add(df['close'].iloc[-1] > df['close'].iloc[-21:-1].max(), "BREAKOUT_20")

        # Confluence bonus
        if {"MACD_BULL", "RSI_HOLD", "EMA_CROSS"}.issubset(set(triggers)):
            score += self.weights.get("COMBO_BONUS", 0)
            triggers.append("COMBO_BONUS")

        return score, triggers

    def analyze(self, symbol):
        ohlcv = self.fetch_ohlcv(symbol)
        if not ohlcv or len(ohlcv) < 30:
            return None

        df = pd.DataFrame(ohlcv, columns=['ts','open','high','low','close','volume'])
        for col in ['open','high','low','close','volume']:
            df[col] = df[col].astype(float)

        # Add TA indicators
        df['ema9'] = trend.ema_indicator(df['close'], window=9)
        df['ema21'] = trend.ema_indicator(df['close'], window=21)
        df['sma10'] = trend.sma_indicator(df['close'], window=10)
        df['sma20'] = trend.sma_indicator(df['close'], window=20)
        df['macd'] = trend.macd(df['close'])
        df['macdsignal'] = trend.macd_signal(df['close'])
        df['rsi'] = momentum.rsi(df['close'])
        df['stoch_k'] = momentum.stoch(df['high'], df['low'], df['close'])
        df['stoch_d'] = momentum.stoch_signal(df['high'], df['low'], df['close'])
        df['adx'] = trend.adx(df['high'], df['low'], df['close'])
        df['plus_di'] = trend.positive_di(df['high'], df['low'], df['close'])
        df['minus_di'] = trend.minus_di(df['high'], df['low'], df['close'])
        bb = volatility.BollingerBands(df['close'])
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['atr'] = volatility.average_true_range(df['high'], df['low'], df['close'])
        df['donchian_high'] = df['high'].rolling(20).max()
        df['vwap'] = volume.volume_weighted_average_price(df['high'], df['low'], df['close'], df['volume'])
        df['obv'] = volume.on_balance_volume(df['close'], df['volume'])
        df['cmf'] = volume.chaikin_money_flow(df['high'], df['low'], df['close'], df['volume'])
        df['ad'] = volume.acc_dist_index(df['high'], df['low'], df['close'], df['volume'])
        df['cci'] = trend.cci(df['high'], df['low'], df['close'])
        df['williamsr'] = momentum.williams_r(df['high'], df['low'], df['close'])
        df['roc'] = momentum.roc(df['close'])
        df['trix'] = trend.trix(df['close'])

        score, triggers = self.score_signals(df)
        confidence = self.calc_confidence(symbol)

        return {
            "symbol": symbol,
            "score": score,
            "confidence": confidence,
            "trigger_list": triggers,
            "change_15m": self._percent_change(df['close'].tolist(), 15),
            "change_30m": self._percent_change(df['close'].tolist(), 30),
            "momentum_likely_to_continue": score >= 10 and confidence >= 60,
        }
