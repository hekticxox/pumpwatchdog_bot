import os
import logging
import requests

def send_alert(msg: str, parse_mode: str = "Markdown") -> None:
    """
    Send an alert message to a Telegram chat using a bot.

    Args:
        msg (str): The message to send.
        parse_mode (str, optional): The parse mode for formatting ('Markdown', 'HTML', etc.). Defaults to "Markdown".

    Required Environment Variables:
        TELEGRAM_BOT_TOKEN (str): Your Telegram bot token.
        TELEGRAM_CHAT_ID (str): The chat ID to send the message to.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logging.warning("Telegram credentials not set (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID), skipping alert.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": parse_mode
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            logging.error(f"Telegram alert failed: {response.text}")
    except requests.exceptions.RequestException as error:
        logging.error(f"Telegram alert exception: {error}")
