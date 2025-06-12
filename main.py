import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.")

import time
import csv
import os
import ccxt
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from alerts import send_alert
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from ta import trend, momentum, volatility, volume

load_dotenv()

LOG_FILE = "pumpwatchdog_log.csv"
DISPLAY_LIMIT = 20  # Show more coins
THREAD_WORKERS = 12

DEFAULT_WEIGHTS = {
    # ...existing code from signal_engine.py...
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
        add(df['mom'].iloc[-1] > 0, "MOM_POS")
        add(df['zscore'].iloc[-1] > 1, "ZSCORE_SPIKE")
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
        try:
            df['mom'] = momentum.awesome_oscillator(df['high'], df['low'])
        except AttributeError:
            df['mom'] = pd.Series(np.nan, index=df.index)
        df['zscore'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).std()
        try:
            df['fdi'] = trend.fractal_dimension_index(df['close'], window=10)
        except Exception:
            df['fdi'] = pd.Series(np.nan, index=df.index)

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

def get_top_usdt_pairs(n=100, exchange_name='kucoin', verbose=False):
    """
    Fetches the top USDT trading pairs based on quote volume.
    """
    try:
        exchange = getattr(ccxt, exchange_name)()
        tickers = exchange.fetch_tickers()
        usdt_pairs = [
            symbol for symbol in tickers
            if symbol.endswith('/USDT')
            and not symbol.startswith('BULL/')
            and not symbol.startswith('BEAR/')
            and not symbol.startswith('UP/')
            and not symbol.startswith('DOWN/')
        ]
        usdt_pairs.sort(key=lambda s: tickers[s].get('quoteVolume', 0), reverse=True)
        if verbose:
            print(f"[DEBUG] Found {len(usdt_pairs)} USDT pairs, selecting top {n}.")
        return usdt_pairs[:n]
    except Exception as e:
        print(f"Error fetching dynamic pairs: {e}")
        return [
            "UNI/USDT", "ETH/USDT", "BTC/USDT", "AVAX/USDT",
            "DOGE/USDT", "PEPE/USDT", "LAUNCHCOIN/USDT"
        ]

def log_scan(rows, filename=LOG_FILE):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = [
            "rank", "symbol", "score", "status", "conf%", "pumptime",
            "age", "num_triggers", "change_15m", "change_30m", "triggers"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

def get_status(num_triggers, score):
    if num_triggers >= 20:
        return "🟣 PARABOLIC"
    if num_triggers >= 15:
        return "🟢 STRONGUPTREND"
    if score >= 10:
        return "🔥 HOT"
    elif score >= 7:
        return "🚀 Pump"
    elif score >= 4:
        return "Watch"
    elif score > 0:
        return "Weak"
    else:
        return "N/A"

def get_status_color(status):
    if status == "🟣 PARABOLIC":
        return "bold magenta"
    if status == "🟢 STRONGUPTREND":
        return "bold green"
    if status == "🔥 HOT":
        return "bold red"
    if status == "🚀 Pump":
        return "bold yellow"
    if status == "Watch":
        return "cyan"
    if status == "Weak":
        return "grey50"
    return "white"

def fetch_symbol_indicators(symbol, verbose=False):
    def _get_real_indicators(symbol, fallback=False, return_exchange=False):
        """
        Placeholder implementation for fetching real indicators.
        indicators, used_exchange = self._get_real_indicators(symbol, fallback=False, return_exchange=True)
        """
        return {
            "score": 10,
            "confidence": 85,
            "trigger_list": ["trigger1", "trigger2"],
            "change_15m": 5.0,
            "change_30m": 10.0,
            "pumptime": "2023-10-01 12:00:00"
        }, "kucoin"
    if verbose:
        print(f"[VERBOSE] Starting scan for {symbol}")
    try:
        indicators, used_exchange = _get_real_indicators(symbol, fallback=False, return_exchange=True)
    except TypeError:
        try:
            indicators, _ = _get_real_indicators(symbol, fallback=False)
            used_exchange = None
        except Exception as e:
            if verbose:
                print(f"[DEBUG] Error in get_real_indicators for {symbol}: {e}")
            indicators = None
            used_exchange = None
    except Exception as e:
        if verbose:
            print(f"[DEBUG] Unexpected error in get_real_indicators for {symbol}: {e}")
        indicators = None
        used_exchange = None

    if indicators is None:
        if verbose:
            print(f"[DEBUG] No indicator data for {symbol}")
        return (symbol, None, None)
    if len(indicators.get("trigger_list", [])) == 0:
        if verbose:
            print(f"[DEBUG] No triggers fired for {symbol}")
    else:
        if verbose:
            print(f"[DEBUG] {symbol}: {len(indicators.get('trigger_list', []))} triggers fired")
    if verbose:
        print(f"[VERBOSE] Finished scan for {symbol}")
    return (symbol, indicators, used_exchange)

def build_table(symbol_rows, symbol_age, display_limit=DISPLAY_LIMIT):
    table = Table(title="Top Bullish Coins", highlight=True, border_style="bright_magenta")
    table.add_column("Rank", justify="right", style="bold", no_wrap=True)
    table.add_column("Symbol", style="bold")
    table.add_column("Score", justify="center")
    table.add_column("Status", style="bold")
    table.add_column("Conf%", justify="center")
    table.add_column("PumpTime", justify="center")
    table.add_column("Age", justify="center")
    table.add_column("#Trig", justify="center")
    table.add_column("%Δ15m", justify="right")
    table.add_column("%Δ30m", justify="right")
    # Triggers column removed from table

    display_idx = 1
    for symbol, indicators, used_exchange in symbol_rows[:display_limit]:
        if indicators is None:
            continue
        score = indicators.get("score", 0)
        conf = indicators.get("confidence", 0)
        pumptime = indicators.get("pumptime", "N/A")
        age = symbol_age.get(symbol, 1)
        triggers = indicators.get("trigger_list", [])
        num_triggers = len(triggers)
        status = get_status(num_triggers, score)
        status_color = get_status_color(status)
        notable = status in ["🟣 PARABOLIC", "🔥 HOT", "🚀 Pump", "🟢 STRONGUPTREND"]
        star = "★" if notable else ""
        change_15m = indicators.get("change_15m", "N/A")
        change_30m = indicators.get("change_30m", "N/A")
        def fmt_pct(val):
            try:
                v = float(val)
                return f"{v:+.2f}%"
            except:
                return str(val)
        table.add_row(
            f"{display_idx}{star}",
            f"[white]{symbol}[/white]" if not notable else f"[bold magenta]{symbol}[/bold magenta]",
            f"[bold]{score}[/bold]",
            f"[{status_color}]{status}[/{status_color}]",
            f"{conf}%",
            f"{pumptime}",
            f"{age}",
            f"{num_triggers}",
            fmt_pct(change_15m),
            fmt_pct(change_30m),
        )
        display_idx += 1
    return table

def update_symbol_ages(symbol_age, top_symbols):
    new_symbol_age = {}
    for symbol in top_symbols:
        if symbol in symbol_age:
            new_symbol_age[symbol] = symbol_age[symbol] + 1
        else:
            new_symbol_age[symbol] = 1
    return new_symbol_age

def main():
    engine = SignalEngine()
    symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]  # Replace with dynamic symbol fetching logic
    for symbol in symbols:
        result = engine.analyze(symbol)
        if result and result["momentum_likely_to_continue"]:
            msg = f"🚨 *Pump Alert* — {result['symbol']} is showing strong momentum!\n\nScore: {result['score']}\nConfidence: {result['confidence']}%\nTriggers: {', '.join(result['trigger_list'])}"
            send_alert(msg, channel="telegram")

if __name__ == "__main__":
    main()
