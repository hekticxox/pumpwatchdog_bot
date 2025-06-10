import requests

TOKEN = "7072447263:AAFZ6wYCgMhOQCj_iuAYccMP6LjnqPnh_l0"
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

resp = requests.get(url)
print(resp.json())
