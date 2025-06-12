from signal_engine import SignalEngine
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

def send_telegram_alert(msg: str):
    """
    Send an alert message to Telegram. Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[alerts] Telegram credentials not set, skipping alert.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code != 200:
            print(f"[alerts] Telegram alert failed: {resp.text}")
    except Exception as e:
        print(f"[alerts] Telegram alert exception: {e}")

def send_alert(msg: str, channel: str = "telegram"):
    """
    Dispatch alert to the chosen channel. Defaults to Telegram.
    """
    if channel == "telegram":
        send_telegram_alert(msg)
    # Add more channels here (email, Discord, etc.)
    else:
        print(f"[alerts] Unknown alert channel: {channel}")

if __name__ == "__main__":
    engine = SignalEngine()
    result = engine.analyze("BTC/USDT")
    if result and result["momentum_likely_to_continue"]:
        msg = f"🚨 *Pump Alert* — {result['symbol']} is showing strong momentum!\n\nScore: {result['score']}\nConfidence: {result['confidence']}%\nTriggers: {', '.join(result['trigger_list'])}"
        send_alert(msg, channel="telegram")
