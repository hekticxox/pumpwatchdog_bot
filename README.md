# PumpWatchdog Multi-Timeframe Scanner

PumpWatchdog is an automated crypto market scanner that continuously monitors the **top 100 USDT trading pairs by volume on KuCoin**. It calculates multiple technical indicators and ranks coins based on their pump potential, displaying the results in a live-updating terminal table. The tool is ideal for active traders seeking early momentum opportunities or tracking market activity across a wide range of assets.

---

## Features

- **Live Automated Scanning:** Monitors the top 100 USDT pairs on KuCoin, updating every 60 seconds.
- **Technical Indicators:** Computes technical signals like ADX, CCI, Williams %R, ROC, RSI, and more (customizable via `indicators.py`).
- **Pump Scoring:** Assigns each coin a score and status (HOT, Pump, Watch, Weak) based on live indicator triggers.
- **Age Tracking:** Shows how many times each symbol has appeared on the chart since the script started.
- **Ranked Output:** Prints a ranked, readable table in the terminal and logs all results to CSV.
- **Easy Extensibility:** Modular design—add or adjust indicators via the `indicators.py` file.
- **KuCoin Native:** All data and symbols are pulled live from KuCoin, ensuring compatibility and up-to-date listings.

---

## Installation

### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/pumpwatchdog_bot.git
cd pumpwatchdog_bot
```

### 2. (Recommended) Create & Activate a Virtual Environment

```sh
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, you need at least:

- `ccxt`
- `numpy`
- `pandas`

Install with:

```sh
pip install ccxt numpy pandas
```

---

## Usage

Start the scanner with:

```sh
python main.py
```

The script will:

- Fetch the top 100 USDT pairs by volume from KuCoin every 60 seconds.
- Calculate technical indicators for each symbol.
- Print a ranked table showing:
  - Rank
  - Symbol
  - Pump Score
  - Status (HOT, Pump, Watch, Weak)
  - Confidence %
  - PumpTime
  - Age (number of times the coin has appeared on the chart since script start)
  - Number of triggers and trigger details
- Log all results to `pumpwatchdog_log.csv` for later analysis.

---

## Customization

- **Indicators & Scoring:**  
  Edit `indicators.py` to adjust which indicators are used or how scores are calculated.
- **Number of Pairs:**  
  To scan more or fewer pairs, change the `n=100` value in `get_top_usdt_pairs()` in `main.py`.
- **Exchange:**  
  By default, the script scans KuCoin. To use another exchange supported by [ccxt](https://github.com/ccxt/ccxt), change the `exchange_name` argument in `main.py`.

---

## Output Example

```
Rank | Symbol           | Score | Status    | Conf% | PumpTime | Age | # Trig | Triggers
--------------------------------------------------------------------------------------------------------------
   1 | PEPE/USDT      |    12 | 🔥 HOT     |    96% | 15m      |  19 |      12 | ADX_5m=34.3 CCI_5m=-105.9 ...
   2 | UNI/USDT       |     8 | 🚀 Pump    |    64% | 15m      |  19 |       8 | ADX_15m=28.8 RSI_1h=82.5 ...
   3 | ETH/USDT       |     6 | Watch     |    48% | 15m      |  19 |       6 | CCI_5m=-153.2 WilliamsR_5m=-85.8 ...
--------------------------------------------------------------------------------------------------------------
Press Ctrl+C to exit. Refreshing in 60 seconds...
```

---

## Troubleshooting

- If you see errors about missing modules, run `pip install` as above.
- If the script cannot fetch dynamic pairs (for example, if KuCoin is down), it falls back to a small static list.
- If your terminal or editor shows warnings about style schemes, you can ignore them—they don't affect scanning.

---

## Contributing

Pull requests, bug reports, and suggestions are welcome! Please open an issue or PR on GitHub.

---

## License

MIT License

---

## Disclaimer

This tool is for educational and informational purposes only. It does **not** constitute financial advice. Crypto trading is risky—use your own judgment.

