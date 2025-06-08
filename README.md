# KuCoin Top 100 Bullish Scanner

This is an **async Python scanner** for KuCoin's top 100 USDT trading pairs by volume.  
It analyzes each coin using a point-based system of technical indicators and displays a real-time dashboard of the most bullish setups.

## Features

- **Automatically fetches the top 100 USDT pairs by 24h volume** on KuCoin.
- For each symbol, calculates:
  - Bullish score based on a ranked set of technical indicators (volume breakout, golden cross, MACD, RSI, candlestick patterns, etc).
  - Triggered indicator names.
  - Estimated bullish duration (e.g. 15m, 1h, 1d, 1w, neutral).
  - Current price.
  - 15-minute and 30-minute percent gain.
  - Last candle's trading volume.
- **Fully async** for fast batch analysis.
- **Rich TUI dashboard** (auto-refreshes every 30 seconds).
- Verbose logging for symbol fetching, OHLCV data, and indicator triggers.

## Setup

1. **Clone this repo and install requirements**  
   ```sh
   pip install aiohttp pandas ta numpy rich
   ```

2. **Run the scanner**  
   ```sh
   python kucoin_bullish_scanner.py
   ```

3. **(Optional) Customize**  
   - Change `TIMEFRAME` (default: "15min")
   - Change `CANDLES` for more or less history (default: 110)
   - Change `MAX_CONCURRENCY` for more/fewer simultaneous API calls

## How It Works

- Fetches the top 100 USDT pairs by 24h volume from KuCoin.
- For each symbol:
  - Downloads ~110 candles of OHLCV data.
  - Computes bullish indicators and scores the setup.
  - Prints which indicators triggered and how long the move might last.
- Only setups with a nonzero bullish score are shown in the dashboard.

## Output Example

```
┌─────────────── KuCoin Top 100 Bullish Scanner ──────────────┐
│ Symbol  │ Score │ Triggers           │ Duration │ ...       │
│ ADA-USDT│ 4.50  │ Volume Spike ...   │ 15 mins  │ ...       │
│ LINK-USDT│ 4.50 │ Volume Spike ...   │ 15 mins  │ ...       │
│ ...      │ ...  │ ...                │ ...      │ ...       │
└─────────────────────────────────────────────────────────────┘
```

- **Triggers**: Which indicators fired (see below)
- **Duration**: How long the bullish move may last (estimate)
- **15m/30m Gain %**: Price gain over last 15/30 minutes

## Indicators Used

- High Volume Breakout
- Golden Cross (50/200 EMA)
- Bullish MACD Crossover
- RSI Oversold + Reversal
- Volume Spike After Pullback
- Bullish Candlestick Pattern
- Breakout from Consolidation
- Stochastic RSI Crossover
- Decreasing Selling Pressure (volume divergence)
- VWAP Bounce

## Windows Users

1. **Install Python**  
   Download and install Python 3.9 or newer from [python.org](https://www.python.org/downloads/windows/).  
   During installation, **check "Add Python to PATH"**.

2. **Install dependencies**  
   Open **Command Prompt** (Win+R, type `cmd`, press Enter):
   ```bat
   pip install -r requirements.txt
   ```

3. **Run the scanner**  
   In the same Command Prompt, start the script:
   ```bat
   python kucoin_bullish_scanner.py
   ```

4. **Troubleshooting**  
   - If you get errors about `pip` not found, try `python -m pip install -r requirements.txt`.
   - If you see encoding issues in the terminal UI, try using [Windows Terminal](https://aka.ms/terminal) or set your Command Prompt font to a TrueType font (like Consolas).

## Troubleshooting

- If you see "Insufficient data for ..." in the logs, some newly listed coins may not have enough candles.
- If KuCoin rate-limits you, reduce `MAX_CONCURRENCY`.
- If you want to add more timeframes or intervals, edit the script as needed.

## License

MIT

## Credits

- Uses [ta](https://github.com/bukosabino/ta) for technical analysis.
- Uses [rich](https://github.com/Textualize/rich) for the terminal UI.

---

**Not financial advice. Use at your own risk.**
