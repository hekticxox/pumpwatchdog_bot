import os
import logging
import requests

def send_alert(msg: str, parse_mode: str = "Markdown") -> None:
    """
    Send an alert message to Telegram.

    Args:
        msg (str): The message to send.
        parse_mode (str, optional): Parse mode for Telegram (e.g., 'Markdown', 'HTML'). Defaults to "Markdown".

    Environment Variables:
        TELEGRAM_BOT_TOKEN: Telegram bot token.
        TELEGRAM_CHAT_ID: Chat ID to send the message to.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logging.warning("Telegram credentials not set, skipping alert.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": parse_mode}
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code != 200:
            logging.error(f"Telegram alert failed: {resp.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Telegram alert exception: {e}")
