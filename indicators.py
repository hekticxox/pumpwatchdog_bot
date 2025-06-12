import os
import ccxt
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import ta  # pip install ta

load_dotenv()

def get_exchange():
    kucoin_api_key = os.getenv('KUCOIN_API_KEY')
    kucoin_secret = os.getenv('KUCOIN_API_SECRET')
    kucoin_passphrase = os.getenv('KUCOIN_API_PASSPHRASE')
    if kucoin_api_key and kucoin_secret and kucoin_passphrase:
        kucoin = ccxt.kucoin({
            'apiKey': kucoin_api_key,
            'secret': kucoin_secret,
            'password': kucoin_passphrase,
            'enableRateLimit': True
        })
        try:
            kucoin.load_markets()
            return kucoin, 'kucoin'
        except Exception:
            pass
    binance = ccxt.binance({'enableRateLimit': True})
    binance.load_markets()
    return binance, 'binance'

def fetch_ohlcv(exchange, symbol, timeframe, limit):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except Exception:
        if exchange.id == 'binance':
            try:
                return exchange.fetch_ohlcv(symbol.replace('/', ''), timeframe=timeframe, limit=limit)
            except Exception:
                raise
        else:
            raise

def get_percent_change(prices, periods):
    if len(prices) < periods + 1:
        return None
    return round(100 * (prices[-1] - prices[-(periods+1)]) / prices[-(periods+1)], 2)

def calc_confidence_from_orderbook(exchange, symbol, ex_name):
    try:
        if ex_name == 'binance':
            ob = exchange.fetch_order_book(symbol.replace('/', ''))
        else:
            ob = exchange.fetch_order_book(symbol)
        bids = ob.get('bids', [])[:20]
        asks = ob.get('asks', [])[:20]
        buy_vol = sum(price * amount for price, amount in bids)
        sell_vol = sum(price * amount for price, amount in asks)
        total_vol = buy_vol + sell_vol
        if total_vol == 0:
            return 50
        confidence = int(round(100 * buy_vol / total_vol))
        return confidence
    except Exception:
        return 50

def bullish_triggers(df):
    score = 0
    triggers = []

    # 1. Moving Average crossovers (EMA 9 > EMA 21, SMA 10 > SMA 20)
    if df['ema9'].iloc[-1] > df['ema21'].iloc[-1]:
        score += 1
        triggers.append('EMA9>EMA21 Bullish')
    if df['sma10'].iloc[-1] > df['sma20'].iloc[-1]:
        score += 1
        triggers.append('SMA10>SMA20 Bullish')

    # 2. MACD Bullish Cross (MACD line crosses above Signal)
    if df['macd'].iloc[-2] < df['macdsignal'].iloc[-2] and df['macd'].iloc[-1] > df['macdsignal'].iloc[-1]:
        score += 2
        triggers.append('MACD Bullish Cross')

    # 3. RSI
    if df['rsi'].iloc[-1] >= 60:
        score += 1
        triggers.append(f'RSI={df["rsi"].iloc[-1]:.1f} Bullish')
    if df['rsi'].iloc[-1] > 70:
        score += 1
        triggers.append(f'RSI={df["rsi"].iloc[-1]:.1f} Overbought, but bullish')

    # 4. Stochastic oscillator
    if df['stoch_k'].iloc[-1] > 20 and df['stoch_k'].iloc[-1] > df['stoch_d'].iloc[-1]:
        score += 1
        triggers.append(f'StochK>{df["stoch_k"].iloc[-1]:.1f} Bullish')

    # 5. ADX trend (plus_di, minus_di from ta.trend, not ta.momentum, and always check existence!)
    if 'plus_di' in df.columns and 'minus_di' in df.columns and 'adx' in df.columns:
        if pd.notnull(df['adx'].iloc[-1]) and pd.notnull(df['plus_di'].iloc[-1]) and pd.notnull(df['minus_di'].iloc[-1]):
            if df['adx'].iloc[-1] > 25 and df['plus_di'].iloc[-1] > df['minus_di'].iloc[-1]:
                score += 1
                triggers.append('ADX Trend Up')

    # 6. Bollinger Bands: price closes above mid band, not over upper
    if df['close'].iloc[-1] > df['bb_middle'].iloc[-1] and df['close'].iloc[-1] < df['bb_upper'].iloc[-1]:
        score += 1
        triggers.append('Price > BB Middle')

    # 7. ATR Volatility Spike (current ATR > 90th percentile of ATR)
    if df['atr'].iloc[-1] > np.percentile(df['atr'].dropna(), 90):
        score += 1
        triggers.append('ATR Volatility Spike')

    # 8. Donchian Channel breakout
    if df['close'].iloc[-1] > df['donchian_high'].iloc[-2]:
        score += 1
        triggers.append('Donchian Channel Breakout')

    # 9. VWAP: price above VWAP intraday
    if not np.isnan(df['vwap'].iloc[-1]) and df['close'].iloc[-1] > df['vwap'].iloc[-1]:
        score += 1
        triggers.append('Price > VWAP')

    # 10. OBV Uptrend (last 2 OBV positive slope)
    if df['obv'].iloc[-1] > df['obv'].iloc[-2] > df['obv'].iloc[-3]:
        score += 1
        triggers.append('OBV Uptrend')

    # 11. Chaikin Money Flow positive
    if df['cmf'].iloc[-1] > 0:
        score += 1
        triggers.append('CMF Positive Flow')

    # 12. Accum/Dist Line Up
    if df['ad'].iloc[-1] > df['ad'].iloc[-2]:
        score += 1
        triggers.append('Accum/Dist Up')

    # 13. CCI bullish
    if df['cci'].iloc[-1] > 100:
        score += 1
        triggers.append('CCI Bullish')

    # 14. Williams %R bullish (>-50)
    if df['williamsr'].iloc[-1] > -50:
        score += 1
        triggers.append('Williams %R Bullish')

    # 15. ROC (Rate of Change) positive
    if df['roc'].iloc[-1] > 0:
        score += 1
        triggers.append('ROC Positive')

    # 16. TRIX positive
    if df['trix'].iloc[-1] > 0:
        score += 1
        triggers.append('TRIX Bullish')

    # 17. Momentum positive
    if 'mom' in df.columns and pd.notnull(df['mom'].iloc[-1]) and df['mom'].iloc[-1] > 0:
        score += 1
        triggers.append('Momentum Positive')

    # 18. Z-Score Price > 1 (strong move)
    if df['zscore'].iloc[-1] > 1:
        score += 1
        triggers.append('Z-Score Price Spike')

    # 19. Fractal Dimension Index > 1.5 (trending)
    if 'fdi' in df.columns and pd.notnull(df['fdi'].iloc[-1]) and df['fdi'].iloc[-1] > 1.5:
        score += 1
        triggers.append('Fractal Trending')

    # 20. High Volume (current volume > 80th percentile)
    if df['volume'].iloc[-1] > np.percentile(df['volume'].dropna(), 80):
        score += 1
        triggers.append('High Volume Spike')

    # 21. Candlestick: Bullish Engulfing (simple)
    if (df['close'].iloc[-2] < df['open'].iloc[-2] and
        df['close'].iloc[-1] > df['open'].iloc[-1] and
        df['close'].iloc[-1] > df['open'].iloc[-2] and
        df['open'].iloc[-1] < df['close'].iloc[-2]):
        score += 2
        triggers.append('Bullish Engulfing Candle')

    # 22. Price breakout above last 20 closes
    if df['close'].iloc[-1] > df['close'].iloc[-21:-1].max():
        score += 2
        triggers.append('20-bar Price Breakout')

    # 23. Bonus: Combo triggers
    if ('MACD Bullish Cross' in triggers and
        'RSI=' in ' '.join(triggers) and
        df['rsi'].iloc[-1] > 60):
        score += 3
        triggers.append('MACD+RSI Bullish Combo')
    if ('EMA9>EMA21 Bullish' in triggers and
        'High Volume Spike' in triggers):
        score += 2
        triggers.append('EMA+Volume Combo')
    if ('Price > VWAP' in triggers and
        'High Volume Spike' in triggers):
        score += 2
        triggers.append('VWAP+Volume Combo')
    if ('OBV Uptrend' in triggers and
        'Accum/Dist Up' in triggers):
        score += 2
        triggers.append('OBV+AD Combo')

    return score, triggers

def get_real_indicators(symbol, fallback=False, return_exchange=False):
    tf = '1h'
    limit = 120

    exchange, ex_name = get_exchange()
    symbol_binance = symbol.replace('/', '')

    try:
        try:
            if ex_name == 'binance':
                ohlcv = fetch_ohlcv(exchange, symbol_binance, tf, limit)
            else:
                ohlcv = fetch_ohlcv(exchange, symbol, tf, limit)
        except Exception as e:
            return (None, ex_name) if return_exchange else None
        if not ohlcv or len(ohlcv) < 30:
            return (None, ex_name) if return_exchange else None

        df = pd.DataFrame(ohlcv, columns=['ts','open','high','low','close','volume'])
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        df['sma10'] = ta.trend.sma_indicator(df['close'], window=10)
        df['sma20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['ema9'] = ta.trend.ema_indicator(df['close'], window=9)
        df['ema21'] = ta.trend.ema_indicator(df['close'], window=21)
        macd = ta.trend.macd(df['close'])
        macdsignal = ta.trend.macd_signal(df['close'])
        df['macd'] = macd
        df['macdsignal'] = macdsignal
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        stoch = ta.momentum.stoch(df['high'], df['low'], df['close'], window=14, smooth_window=3)
        stoch_signal = ta.momentum.stoch_signal(df['high'], df['low'], df['close'], window=14, smooth_window=3)
        df['stoch_k'] = stoch
        df['stoch_d'] = stoch_signal
        adx = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
        try:
            plus_di = ta.trend.plus_di(df['high'], df['low'], df['close'], window=14)
            minus_di = ta.trend.minus_di(df['high'], df['low'], df['close'], window=14)
        except Exception:
            plus_di = pd.Series(np.nan, index=df.index)
            minus_di = pd.Series(np.nan, index=df.index)
        df['adx'] = adx
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        df['donchian_high'] = df['high'].rolling(window=20).max()
        df['donchian_low'] = df['low'].rolling(window=20).min()
        df['keltner_high'] = ta.volatility.keltner_channel_hband(df['high'], df['low'], df['close'], window=20)
        df['keltner_low'] = ta.volatility.keltner_channel_lband(df['high'], df['low'], df['close'], window=20)
        df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])
        df['vwap'] = ta.volume.volume_weighted_average_price(df['high'], df['low'], df['close'], df['volume'], window=20)
        df['cmf'] = ta.volume.chaikin_money_flow(df['high'], df['low'], df['close'], df['volume'], window=20)
        df['ad'] = ta.volume.acc_dist_index(df['high'], df['low'], df['close'], df['volume'])
        df['cci'] = ta.trend.cci(df['high'], df['low'], df['close'], window=20)
        df['williamsr'] = ta.momentum.williams_r(df['high'], df['low'], df['close'], lbp=14)
        df['roc'] = ta.momentum.roc(df['close'], window=12)
        df['trix'] = ta.trend.trix(df['close'], window=15)
        # AO (Awesome Oscillator) not available in all ta versions; skip if not present
        try:
            df['mom'] = ta.momentum.awesome_oscillator(df['high'], df['low'])
        except AttributeError:
            df['mom'] = pd.Series(np.nan, index=df.index)
        df['zscore'] = (df['close'] - df['close'].rolling(window=20).mean()) / df['close'].rolling(window=20).std()
        try:
            df['fdi'] = ta.trend.fractal_dimension_index(df['close'], window=10)
        except Exception:
            df['fdi'] = np.nan

        change_15h = get_percent_change(df['close'].tolist(), 15)
        change_30h = get_percent_change(df['close'].tolist(), 30)

        score, triggers = bullish_triggers(df)

    except Exception as e:
        if fallback:
            score, triggers = 0, []
            change_15h = "N/A"
            change_30h = "N/A"
            confidence = 50
        else:
            raise e

    confidence = calc_confidence_from_orderbook(exchange, symbol, ex_name)
    pumptime = "N/A"

    result = {
        'score': score,
        'confidence': confidence,
        'trigger_list': triggers,
        'pumptime': pumptime,
        'change_15m': change_15h if change_15h is not None else "N/A",
        'change_30m': change_30h if change_30h is not None else "N/A",
    }
    if return_exchange:
        return result, ex_name
    return result
