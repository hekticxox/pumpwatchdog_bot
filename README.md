# KuCoin Pump Bot

A Python bot that scans KuCoin tickers for rapid price increases ("pumps") and sends alerts to Telegram.  
It displays a live dashboard with TA indicators for the top 10 pumping coins.

## Features

- Live terminal dashboard with rich TA indicators
- Sends Telegram alerts for top pumps
- Customizable thresholds and intervals
- Modular, easy to extend

## Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/hekticxox/pumpwatchdog_bot.git
   cd pumpwatchdog_bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your Telegram bot token and chat ID.

     ```
     cp .env.example .env
     ```

     Then edit `.env`:
     ```
     TELEGRAM_BOT_TOKEN=your_bot_token
     TELEGRAM_CHAT_ID=your_chat_id
     ```

4. **Run the bot:**
   ```bash
   python kucoin_pump_bot.py
   ```

## Notes

- **Never commit your real `.env` file!**
- Requires a Telegram bot. [Get your token here.](https://core.telegram.org/bots#6-botfather)
- You may need to install system dependencies for `ta` or `rich` if not present.

## License

MIT
