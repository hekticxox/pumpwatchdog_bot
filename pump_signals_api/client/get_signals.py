import os
import requests
import json

CONFIG_PATH = os.path.expanduser("~/.config_signal")
API_URL = "https://your-render-url.onrender.com/signal/latest"  # update this

def load_token():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return f.read().strip()
    token = input("Enter your API token: ").strip()
    with open(CONFIG_PATH, "w") as f:
        f.write(token)
    return token

def get_signal():
    token = load_token()
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(API_URL, headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(f"\n🔔 {data['pair']} SIGNAL")
        print(f"  Entry     : {data['entry']}")
        print(f"  Current   : {data['current']}")
        print(f"  Exit      : {data['exit_target']}")
        print(f"  Confidence: {data['confidence']}")
        print(f"  Time      : {data['timestamp']}")
        print(f"\n💰 Trade Now: {data['kucoin_referral']}")
    else:
        print(f"\n❌ Error {r.status_code}: {r.text}")

if __name__ == "__main__":
    get_signal()

