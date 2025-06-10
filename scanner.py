import ccxt
import asyncio
import pandas as pd
from datetime import datetime, timezone

class KuCoinScanner:
    def __init__(self, timeframe="1m", max_ohlcv=500, top_n=100, min_volume=100000):
        self.exchange = ccxt.kucoin()
        self.timeframe = timeframe
        self.max_ohlcv = max_ohlcv
        self.top_n = top_n
        self.min_volume = min_volume
        self.symbols = []
        self.ohlcv_data = {}  # {symbol: DataFrame}

    async def fetch_symbols(self):
        markets = self.exchange.load_markets()
        tickers = self.exchange.fetch_tickers()
        filtered = []
        for s in markets:
            if not s.endswith('/USDT'):
                continue
            try:
                tick = tickers[s]
                vol = tick['quoteVolume'] or 0
                if vol < self.min_volume:
                    continue
                pct = abs((tick['percentage'] or 0))
                filtered.append((s, vol, pct))
            except Exception:
                continue
        # Sort by % change (descending), then by volume
        filtered.sort(key=lambda x: (x[2], x[1]), reverse=True)
        self.symbols = [s for s, _, _ in filtered[:self.top_n]]

    async def fetch_ohlcv(self, symbol):
        try:
            raw = self.exchange.fetch_ohlcv(symbol, timeframe=self.timeframe, limit=self.max_ohlcv)
            df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            return df
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    async def update_all_ohlcv(self):
        tasks = [self.fetch_ohlcv(sym) for sym in self.symbols]
        results = await asyncio.gather(*tasks)
        for sym, df in zip(self.symbols, results):
            if df is not None:
                self.ohlcv_data[sym] = df

    async def run(self, poll_interval=15):
        await self.fetch_symbols()
        print(f"Tracking {len(self.symbols)} KuCoin pairs (filtered).")
        while True:
            await self.update_all_ohlcv()
            print(f"[{datetime.now(timezone.utc).isoformat()}] Updated OHLCV for all symbols.")
            await asyncio.sleep(poll_interval)

if __name__ == "__main__":
    scanner = KuCoinScanner()
    asyncio.run(scanner.run())
