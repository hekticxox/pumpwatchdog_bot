import requests

def send_telegram_alert(symbol, score, price, change, est_life, token, chat_id):
    message = (
        f"🚨 *Pump Alert*\n"
        f"🪙 *{symbol}* | Score: {score}/100\n"
        f"💰 Price: {price:.6f}\n"
        f"📈 15m Change: {change:.2f}%\n"
        f"⏳ Est. Lifespan: {est_life}m"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Telegram alert error: {e}")
