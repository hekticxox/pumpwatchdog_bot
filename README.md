# PumpWatchdog Bot

PumpWatchdog is an advanced crypto market scanner and alerting system designed to detect potential "pump" signals on KuCoin spot markets using a sophisticated technical analysis (TA) scoring engine. It features real-time scoring based on 25+ indicators, bonus logic for indicator synergy, Telegram alerts, a CLI dashboard, and a secure FastAPI REST API for signal distribution.

---

## Features

- **Comprehensive TA Scoring:** Uses 25+ classic and modern indicators (trend, momentum, volatility, volume, price action).
- **Synergy Bonus Points:** Extra scoring for patterns like price+volume surges, MACD/RSI agreement, golden cross, etc.
- **Multi-Coin Scanning:** Scans all active KuCoin/USDT spot pairs.
- **Alerts:** Sends top signals to Telegram (or other channels) with breakdowns.
- **FastAPI REST API:** Secure endpoint for distributing signals with token authentication.
- **Extensible:** Modular pipeline for adding new indicators, scoring rules, or alerting targets.
- **Dashboard:** CLI dashboard for live signal monitoring.
- **Easy Config:** Uses `.env` for sensitive info and settings.
- **Test Mode:** Simulate runs without live alerts/trades.

---

## Installation & Setup

### 1. Clone & Install Requirements

```sh
git clone https://github.com/yourusername/pumpwatchdog_bot.git
cd pumpwatchdog_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables

Copy `.env.example` to `.env` (or create `.env` manually):

```env
KUCOIN_API_KEY=your_kucoin_api_key
KUCOIN_SECRET=your_kucoin_secret
KUCOIN_PASSWORD=your_kucoin_password
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Set these variables as needed for your setup.

---

## Usage

### Run Main Signal Scanner

```sh
python main.py
```

- Scans all eligible coins, computes scores, prints and (optionally) sends alerts for top results.
- Results are also written to `signals.json` for API/dashboard use.

### Run API Server

```sh
cd pump_signals_api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- API (e.g., `/signal/latest`) requires a valid token, managed in the SQLite user DB.

### Run CLI Dashboard

```sh
python dashboard.py
```

- Live, terminal-based interface for monitoring top signals.

### Send Test Alert

```sh
python alerts.py
```

- (Edit this file or run from code to test Telegram alerts.)

---

## File Overview

```
.
├── main.py               # Main scanning/alert loop (entry point)
├── ta_engine.py          # All TA indicator calculations
├── scoring_engine.py     # Scoring logic (points, bonuses)
├── scanner.py            # CCXT data fetching utilities
├── alerts.py             # Telegram (or other) alert sender
├── dashboard.py          # CLI dashboard (Rich)
├── pump_signals_api/     # FastAPI app and user/token DB
│   ├── main.py
│   ├── db.py
│   └── test_db.py
├── requirements.txt      # Python dependencies
├── .env                  # Your environment variables (not versioned)
├── signals.json          # Latest results (for API/dashboard)
└── README.md
```

---

## Technical Details

### Scoring Engine

- **Indicators:** SMA, EMA, MACD, RSI, Stochastic, ADX, Bollinger Bands, ATR, Donchian, Keltner, OBV, VWAP, CMF, AccDist, Pivot/Fibo, CCI, Williams %R, ROC, TRIX, candlestick patterns, and more.
- **Bonus Triggers:** Price+volume surge, MACD+RSI agreement, multi-trend agreement, golden cross, bullish engulfing confirming price move, etc.
- **Ranking:** Coins are ranked by total points; you set how many top results to alert or output.

### Alerts

- **Telegram:** Out-of-the-box support. Add other channels easily via `alerts.py`.

### API

- **FastAPI:** Secure endpoints with token authentication.
- **Token/User Management:** Managed via `pump_signals_api/db.py` (SQLite, simple CLI).
- **Example Query:**  
  ```sh
  curl -H "Authorization: Bearer <token>" http://localhost:8000/signal/latest
  ```

---

## Customization

- **Add new indicators or scoring logic:** Edit `ta_engine.py` and/or `scoring_engine.py`.
- **Change alert logic or targets:** Edit `alerts.py` and `main.py`.
- **Refine dashboard view:** Edit `dashboard.py`.
- **Adjust API endpoints or logic:** Edit `pump_signals_api/main.py`.

---

## Troubleshooting

- **Indicator Mismatch:** Ensure all indicator names in `ta_engine.py` match those used in `scoring_engine.py`.
- **Telegram issues:** Check your bot token and chat ID in `.env`.
- **KuCoin errors:** Check API keys and ensure your IP is whitelisted (if needed).
- **Missing packages:** Run `pip install -r requirements.txt` inside your virtualenv.
- **API auth errors:** Use the right token; manage with scripts in `pump_signals_api/db.py`.

---

## Contribution

Pull requests and feature suggestions are very welcome!
- Please submit bugs or feature requests via GitHub Issues.
- Follow PEP8 and document new code.
- Major changes: open an issue first to discuss.

---

## License

MIT License. See `LICENCE.md`.

---

## Credits

- [ccxt](https://github.com/ccxt/ccxt)
- [ta](https://github.com/bukosabino/ta)
- [rich](https://github.com/Textualize/rich)
- [FastAPI](https://fastapi.tiangolo.com/)
