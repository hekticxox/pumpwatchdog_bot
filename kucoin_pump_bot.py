import warnings
warnings.filterwarnings("ignore")

import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands
from collections import defaultdict

# === CONFIG ===
TELEGRAM_BOT_TOKEN = '7072447263:AAFZ6wYCgMhOQCj_iuAYccMP6LjnqPnh_l0'
TELEGRAM_CHAT_ID = '5703735580'
PUMP_THRESHOLD = 0.10
SPREAD_THRESHOLD = 0.015
TELEGRAM_ALERT_INTERVAL = 600

console = Console()

last_alert_time = 0
alerted_symbols = set()
symbol_history = defaultdict(list)

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        console.log(f"[red]Telegram Error: {e}[/red]")

def fetch_ohlcv(symbol):
    url = f"https://api.kucoin.com/api/v1/market/candles?type=1min&symbol={symbol}"
    try:
        r = requests.get(url, timeout=10)
        candles = r.json()['data']
        df = pd.DataFrame(candles, columns=["time", "open", "close", "high", "low", "volume", "turnover"])
        df = df.iloc[::-1].astype(float).reset_index(drop=True)
        return df
    except Exception as e:
        return pd.DataFrame()

def compute_indicators(df):
    df["rsi"] = RSIIndicator(df["close"]).rsi()
    df["ema20"] = EMAIndicator(df["close"], window=20).ema_indicator()
    df["macd"] = MACD(df["close"]).macd_diff()
    bb = BollingerBands(df["close"])
    df["bb_width"] = bb.bollinger_hband() - bb.bollinger_lband()
    df["stoch_rsi"] = StochasticOscillator(df["high"], df["low"], df["close"]).stoch()
    df["vwap"] = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()
    return df

def indicator_score(row):
    score = 0
    if row['rsi'] > 70: score += 1
    if row['close'] > row['ema20']: score += 1
    if row['macd'] > 0: score += 1
    if row['bb_width'] > 0: score += 1
    if row['stoch_rsi'] > 80: score += 1
    if row['close'] > row['vwap']: score += 1
    return score

def fetch_all_tickers():
    url = "https://api.kucoin.com/api/v1/market/allTickers"
    try:
        r = requests.get(url, timeout=10)
        return r.json()['data']['ticker']
    except:
        return []

def analyze_tickers(tickers):
    candidates = []
    for t in tickers:
        try:
            symbol = t["symbol"]
            if not symbol.endswith("USDT"):
                continue
            change = float(t["changeRate"])
            price = float(t["last"])
            bid = float(t.get("buy") or 0)
            ask = float(t.get("sell") or 0)
            spread = abs(ask - bid) / price if price else 1
            if spread > SPREAD_THRESHOLD: continue

            df = fetch_ohlcv(symbol)
            if df.empty or len(df) < 30: continue
            df = compute_indicators(df)
            row = df.iloc[-1]
            score = indicator_score(row)
            combined_score = change * 100 + score * 2  # % change + indicator boost
            candidates.append((symbol, change, price, combined_score, score))

        except Exception:
            continue

    candidates.sort(key=lambda x: x[3], reverse=True)
    return candidates[:10]

def build_dashboard(top_tokens):
    time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    table = Table(title="📊 Top 10 Crypto Pumps (w/ Indicators)", header_style="bold magenta")
    table.add_column("Symbol", style="cyan", justify="left")
    table.add_column("15m Change", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Score", justify="center")

    for s, c, p, total, ind_score in top_tokens:
        color = "bright_blue" if ind_score >= 4 else ("yellow" if ind_score >= 2 else "dim")
        table.add_row(f"{s}", f"[green]{c*100:.2f}%[/green]", f"{p:.6f}", f"[{color}]{ind_score}/6[/{color}]")

    return Panel(table, title=f"[bold blue]Updated: {time_str}[/bold blue]", border_style="green")

def main():
    global last_alert_time
    console.print("[cyan]📡 KuCoin Pump Bot w/ TA Starting...[/cyan]")
    with Live(console=console, screen=False, refresh_per_second=0.5) as live:
        while True:
            tickers = fetch_all_tickers()
            top_tokens = analyze_tickers(tickers)
            panel = build_dashboard(top_tokens)
            live.update(panel)

            # Alert best pick
            if top_tokens and time.time() - last_alert_time >= TELEGRAM_ALERT_INTERVAL:
                sym, change, price, _, score = top_tokens[0]
                msg = f"""🚀 *Top Pump Alert*
Symbol: `{sym}`
Change: `{change*100:.2f}%`
Price: `{price}`
Indicators: `{score}/6`"""
                send_telegram_alert(msg)
                last_alert_time = time.time()

            time.sleep(60)

if __name__ == "__main__":
    main()

