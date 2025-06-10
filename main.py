import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from scanner import get_all_symbols, fetch_ohlcv_for_symbol
from alerts import send_alert
from ta_engine import calculate_all_indicators
from scoring_engine import calculate_score
from dashboard import live_dashboard

import numpy as np

SIGNALS_FILE = "signals.json"
REFRESH_INTERVAL = 60  # seconds between scans
TOP_N = 10

SCAN_SYMBOL_LIMIT = int(os.environ.get("SCAN_SYMBOL_LIMIT", 5))
THREAD_WORKERS = int(os.environ.get("THREAD_WORKERS", 5))
TIMEFRAME = '15m'

load_dotenv(override=True)

def json_safe(val):
    if isinstance(val, (np.integer,)):
        return int(val)
    elif isinstance(val, (np.floating,)):
        return float(val)
    elif isinstance(val, (pd.Timestamp,)):
        return val.isoformat()
    elif hasattr(val, "item"):  # For np scalars
        return val.item()
    else:
        return val

def process_symbol(symbol):
    try:
        df = fetch_ohlcv_for_symbol(symbol, timeframe=TIMEFRAME)
        if df is not None and not df.empty and len(df) > 10:
            signal_triggers = calculate_all_indicators(df)
            triggered = [k for k, v in signal_triggers.items() if bool(v)]
            log_hits = len(triggered)
            triggers_str = ", ".join(triggered)

            score = float(log_hits)
            meta = triggers_str

            duration_bonus = 0
            closes = df["close"]
            opens = df["open"]
            for c, o in zip(reversed(closes), reversed(opens)):
                if c > o:
                    duration_bonus += 1
                else:
                    break

            change_15m = 0.0
            if len(df) >= 4:
                change_15m = ((df["close"].iloc[-1] - df["close"].iloc[-4]) / df["close"].iloc[-4]) * 100

            est_life = duration_bonus * 15
            pump_age = duration_bonus
            meta_score = log_hits

            result = {
                "symbol": str(symbol),
                "score": float(score),
                "meta": str(meta),
                "timestamp": str(df.iloc[-1]["timestamp"]) if "timestamp" in df.columns else "",
                "log_hits": int(log_hits),
                "triggers": [str(t) for t in triggered],
                "triggers_str": str(triggers_str),
                "duration_bonus": int(duration_bonus),
                "change_15m": float(round(change_15m, 2)),
                "est_life": int(est_life),
                "pump_age": int(pump_age),
                "meta_score": int(meta_score),
            }
            return result
    except Exception as e:
        print(f"    [!] Exception for {symbol}: {e}")
    return None

def scan_and_score():
    all_symbols = get_all_symbols()
    if SCAN_SYMBOL_LIMIT:
        all_symbols = all_symbols[:SCAN_SYMBOL_LIMIT]
    results = []

    print(f"Scanning {len(all_symbols)} symbols with {THREAD_WORKERS} threads (15m candles)...")

    with ThreadPoolExecutor(max_workers=THREAD_WORKERS) as executor:
        futures = {executor.submit(process_symbol, symbol): symbol for symbol in all_symbols}
        for idx, future in enumerate(as_completed(futures), 1):
            symbol = futures[future]
            try:
                res = future.result()
                if res is not None:
                    triggers_str = res.get('triggers_str', "")
                    print(f"  [{idx}/{len(all_symbols)}] {symbol:<12} OK (score: {res['score']:.2f}) Triggers: {triggers_str}")
                    results.append(res)
                else:
                    print(f"  [{idx}/{len(all_symbols)}] {symbol:<12} No data.")
            except Exception as e:
                print(f"  [{idx}/{len(all_symbols)}] {symbol:<12} ERROR: {e}")

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:TOP_N]

def persist_signals(signals):
    try:
        with open(SIGNALS_FILE, "w") as f:
            json.dump(signals, f, indent=2, default=json_safe)
    except Exception as e:
        print(f"Failed to write signals file: {e}")

def get_dashboard_data():
    try:
        with open(SIGNALS_FILE) as f:
            signals = json.load(f)
            return signals, []
    except Exception:
        return [], []

def main():
    print("=== PumpWatchdog Bot Main Scanner ===")
    print("Running in REAL-TIME MODE (fetching live KuCoin data).")

    import threading
    dashboard_enable = os.environ.get("DASHBOARD", "1") == "1"
    if dashboard_enable:
        t = threading.Thread(target=live_dashboard, args=(get_dashboard_data,), daemon=True)
        t.start()

    while True:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scanning markets...")
        signals = scan_and_score()
        persist_signals(signals)
        print(f"Top {TOP_N} signals:")
        for i, s in enumerate(signals, 1):
            triggers_str = s.get('triggers_str', "")
            print(f"{i:2d}. {s['symbol']}: {s['score']:.2f} [{s['meta']}] Triggers: {triggers_str}")
            alert_msg = (
                f"🚨 Pump Signal #{i}: {s['symbol']}\n"
                f"Score: {s['score']:.2f}\n"
                f"Meta: {s['meta']}\n"
                f"Triggers: {triggers_str} | Duration: {s.get('duration_bonus', 0)} | "
                f"15m%: {s.get('change_15m', 0)} | Est Life: {s.get('est_life', 0)} | Age: {s.get('pump_age', 0)}"
            )
            try:
                send_alert(alert_msg)
            except Exception as e:
                print(f"[alerts] Telegram alert exception: {e}")
        print(f"Sleeping {REFRESH_INTERVAL} seconds...\n")
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
