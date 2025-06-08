import asyncio
import aiohttp
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live

KUCOIN_API = "https://api.kucoin.com"
TIMEFRAME = "15min"
CANDLES = 110  # Lowered for broader compatibility
MAX_CONCURRENCY = 5

console = Console()

BULLISH_INDICATORS = [
    ("high_volume_breakout", 3, "High Volume Breakout"),
    ("golden_cross", 2.5, "Golden Cross (50/200EMA)"),
    ("bullish_macd_cross", 2, "Bullish MACD Crossover"),
    ("rsi_oversold_reversal", 2, "RSI Oversold + Reversal"),
    ("volume_spike_pullback", 1.5, "Volume Spike After Pullback"),
    ("bullish_candle_pattern", 1.5, "Bullish Candlestick"),
    ("breakout_consolidation", 1.5, "Consolidation Breakout"),
    ("stoch_rsi_crossover", 1, "Stoch RSI Crossover"),
    ("decreasing_selling_pressure", 1, "Decreasing Selling Pressure"),
    ("vwap_bounce", 1, "VWAP Bounce"),
]

def high_volume_breakout(df):
    if len(df) < 30: return False
    last_close = df['close'].iloc[-1]
    prev_high = df['high'].iloc[-21:-1].max()
    avg_vol = df['volume'].iloc[-21:-1].mean()
    last_vol = df['volume'].iloc[-1]
    return last_close > prev_high and last_vol > 2 * avg_vol

def golden_cross(df):
    if len(df) < 100: return False  # Lowered requirement for EMA due to CANDLES
    ema50 = EMAIndicator(df['close'], window=50).ema_indicator()
    ema200 = EMAIndicator(df['close'], window=100).ema_indicator()  # Shortened for this script
    cross = (ema50.iloc[-3] < ema200.iloc[-3]) and (ema50.iloc[-1] > ema200.iloc[-1])
    return cross

def bullish_macd_cross(df):
    macd = MACD(df['close'])
    return (macd.macd_diff().iloc[-2] < 0) and (macd.macd_diff().iloc[-1] > 0)

def rsi_oversold_reversal(df):
    rsi = RSIIndicator(df['close']).rsi()
    return (rsi.iloc[-2] < 30) and (rsi.iloc[-1] > rsi.iloc[-2])

def volume_spike_pullback(df):
    if len(df) < 20: return False
    avg_vol = df['volume'].iloc[-20:-1].mean()
    last_vol = df['volume'].iloc[-1]
    low_idx = df['close'].iloc[-6:-1].idxmin()
    return (last_vol > 1.5 * avg_vol) and (low_idx >= len(df) - 7)

def bullish_candle_pattern(df):
    o, h, l, c = df['open'].iloc[-1], df['high'].iloc[-1], df['low'].iloc[-1], df['close'].iloc[-1]
    body = abs(c - o)
    lower_wick = min(c, o) - l
    upper_wick = h - max(c, o)
    hammer = lower_wick > 2 * body and lower_wick > upper_wick
    prev_o, prev_c = df['open'].iloc[-2], df['close'].iloc[-2]
    engulfing = (prev_c < prev_o) and (c > o) and (c > prev_o) and (o < prev_c)
    return hammer or engulfing

def breakout_consolidation(df):
    if len(df) < 30: return False
    last_close = df['close'].iloc[-1]
    prev_max = df['close'].iloc[-30:-15].max()
    return last_close > prev_max

def stoch_rsi_crossover(df):
    stoch = StochasticOscillator(df['high'], df['low'], df['close'])
    return (stoch.stoch_signal().iloc[-2] > stoch.stoch().iloc[-2]) and \
           (stoch.stoch_signal().iloc[-1] < stoch.stoch().iloc[-1]) and \
           (stoch.stoch().iloc[-1] < 20)

def decreasing_selling_pressure(df):
    closes = df['close'].iloc[-15:]
    vols = df['volume'].iloc[-15:]
    lows = closes < closes.shift(1)
    down_vols = vols[lows]
    return len(down_vols) > 2 and all(x > y for x, y in zip(down_vols, down_vols[1:]))

def vwap_bounce(df):
    vwap = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    return (df['close'].iloc[-2] < vwap.iloc[-2]) and (df['close'].iloc[-1] > vwap.iloc[-1])

def estimate_bull_duration(triggered):
    score = sum(triggered.values())
    if triggered.get("golden_cross", 0) and score > 5:
        return "1 day" if score < 8 else "1 week"
    if triggered.get("high_volume_breakout", 0) and score > 3:
        return "1 hour"
    if score >= 8:
        return "1 day"
    if score >= 5:
        return "1 hour"
    if score >= 3:
        return "15 mins"
    return "neutral"

async def get_top_kucoin_usdt_symbols(session, top_n=100):
    url = f"{KUCOIN_API}/api/v1/market/allTickers"
    async with session.get(url) as resp:
        js = await resp.json()
        tickers = js["data"]["ticker"]
        usdt_pairs = [
            t for t in tickers
            if t["symbolName"].endswith("USDT")
            and "-3S" not in t["symbolName"]
            and "-3L" not in t["symbolName"]
            and "UP" not in t["symbolName"]
            and "DOWN" not in t["symbolName"]
        ]
        usdt_pairs.sort(key=lambda x: float(x["volValue"]), reverse=True)
        console.print(f"[bold green]Fetched top {top_n} USDT pairs. Example:[/bold green] {usdt_pairs[:5]}")
        return [t["symbolName"] for t in usdt_pairs[:top_n]]

async def fetch_ohlcv(session, symbol, tf=TIMEFRAME, limit=CANDLES):
    url = f"{KUCOIN_API}/api/v1/market/candles?type={tf}&symbol={symbol}&reverse=false"
    async with session.get(url) as resp:
        js = await resp.json()
        if js.get("code") != "200000":
            console.print(f"[red]Failed OHLCV for {symbol}: {js}[/red]")
            return pd.DataFrame()
        data = js['data'][-limit:]
        cols = ["time", "open", "close", "high", "low", "volume", "turnover"]
        df = pd.DataFrame(data, columns=cols)
        for col in ["open", "close", "high", "low", "volume"]:
            df[col] = df[col].astype(float)
        df["time"] = pd.to_datetime(df["time"], unit='ms')
        console.print(f"[cyan]{symbol} OHLCV shape: {df.shape}[/cyan]")
        return df

async def analyze_symbol(session, symbol):
    try:
        df = await fetch_ohlcv(session, symbol)
        if df.empty or len(df) < 100:
            console.print(f"[yellow]Insufficient data for {symbol}[/yellow]")
            return None
        triggers = {}
        total_score = 0
        for name, pts, _ in BULLISH_INDICATORS:
            fn = globals()[name]
            hit = fn(df)
            triggers[name] = pts if hit else 0
            if hit:
                total_score += pts
        duration = estimate_bull_duration(triggers)
        if total_score > 0:
            console.print(f"[green]{symbol} score: {total_score}, triggers: {[desc for (name, _, desc) in BULLISH_INDICATORS if triggers[name]]}, duration: {duration}[/green]")
        return {
            'symbol': symbol,
            'score': total_score,
            'triggers': [desc for (name, _, desc) in BULLISH_INDICATORS if triggers[name]],
            'duration': duration,
            'price': df['close'].iloc[-1],
            '15m_gain': ((df['close'].iloc[-1] / df['close'].iloc[-4]) - 1) * 100 if len(df) >= 4 else 0,
            '30m_gain': ((df['close'].iloc[-1] / df['close'].iloc[-3]) - 1) * 100 if len(df) >= 3 else 0,
            'volume': df['volume'].iloc[-1]
        }
    except Exception as e:
        console.print(f"[red]Error analyzing {symbol}: {e}[/red]")
        return None

def build_table(results):
    table = Table(title="KuCoin Top 100 Bullish Scanner", show_lines=True)
    table.add_column("Symbol", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Triggers", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Price", justify="right")
    table.add_column("15m Gain %", justify="right")
    table.add_column("30m Gain %", justify="right")
    table.add_column("Volume", justify="right")
    for res in sorted(results, key=lambda x: x['score'], reverse=True):
        table.add_row(
            res['symbol'],
            f"{res['score']:.2f}",
            ", ".join(res['triggers']),
            res['duration'],
            f"{res['price']:.5f}",
            f"{res['15m_gain']:.2f}",
            f"{res['30m_gain']:.2f}",
            f"{res['volume']:.2f}"
        )
    return table

async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                console.print("[bold cyan]Fetching top 100 USDT pairs by volume from KuCoin...[/bold cyan]")
                SYMBOLS = await get_top_kucoin_usdt_symbols(session, top_n=100)
                console.print(f"[bold cyan]Top 10 symbols: {SYMBOLS[:10]}[/bold cyan]")
                tasks = []
                sem = asyncio.Semaphore(MAX_CONCURRENCY)
                async def limited(symbol):
                    async with sem:
                        return await analyze_symbol(session, symbol)
                for symbol in SYMBOLS:
                    tasks.append(limited(symbol))
                results = [r for r in await asyncio.gather(*tasks) if r and r['score'] > 0]
                if not results:
                    console.print("[red]No symbols with valid data or triggers.[/red]")
                else:
                    table = build_table(results)
                    with Live(table, refresh_per_second=0.5, screen=True):
                        await asyncio.sleep(30)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Scanner stopped.")
