import os
import requests

def send_alert(msg: str):
    """
    Send an alert message to Telegram. Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram credentials not set, skipping alert.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code != 200:
            print(f"Telegram alert failed: {resp.text}")
    except Exception as e:
        print(f"Telegram alert exception: {e}")
