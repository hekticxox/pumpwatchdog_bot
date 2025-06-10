import asyncio
import logging
import json
import numpy as np
from ta_engine import TAEngine
from scanner import KuCoinScanner
from dashboard import display_top_pumps
from alerts import send_telegram_alert
from pump_life import estimate_pump_duration
from datetime import datetime, timedelta, timezone
import pandas as pd
import os
from dotenv import load_dotenv
from collections import defaultdict

# --- Load environment variables from .env file ---
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LOGFILE = "pumpwatchdog.log"

logging.basicConfig(
    filename=LOGFILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

ta = TAEngine()

# --- Stickiness buffer ---
STICKY_CYCLES = 3   # Number of cycles to keep a coin after it drops out
sticky_coins = defaultdict(lambda: 0)  # symbol -> cycles left

def log_pump_event(symbol, price, change, score, pump_age, est_life, indicators):
    def make_json_safe(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if isinstance(obj, (pd.Timestamp,)):
            return obj.tz_localize(None).isoformat() if obj.tzinfo else obj.isoformat()
        return obj

    indicators_safe = {k: make_json_safe(v) for k, v in indicators.items()}
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "price": float(price),
        "change_15m": float(change),
        "score": int(score),
        "pump_age": int(pump_age),
        "est_life": int(est_life),
        "indicators": indicators_safe
    }
    logging.info(f"PUMP_EVENT: {json.dumps(log_entry)}")

def parse_log_for_symbol(symbol, window_minutes=180):
    meta_score = 0
    count = 0
    now = datetime.now(timezone.utc)
    try:
        with open(LOGFILE, "r") as f:
            for line in reversed(f.readlines()):
                if "PUMP_EVENT" in line and symbol in line:
                    data = json.loads(line.split("PUMP_EVENT: ", 1)[1])
                    event_time = datetime.fromisoformat(data["timestamp"])
                    if now - event_time > timedelta(minutes=window_minutes):
                        break
                    if data["score"] > 80 and data["change_15m"] > 3:
                        meta_score += 10
                    elif data["score"] > 60 and data["change_15m"] > 1:
                        meta_score += 5
                    count += 1
    except Exception:
        pass
    meta_score = min(20, meta_score)
    return meta_score, count

def display_top_pumps_with_candidates(pump_list, candidate_list):
    import rich
    from rich.console import Console
    from rich.table import Table
    from rich.theme import Theme

    custom_theme = Theme({
        "pump": "bold red",
        "candidate": "bold yellow",
        "header": "bold cyan"
    })
    console = Console(theme=custom_theme)

    # If there are pumps, display in red. If not, display "most likely to pump" in yellow.
    if pump_list:
        table = Table(title="🔥 Top Pumping Coins (Ranked by Heat Score)", show_lines=True, style="pump")
    else:
        table = Table(title="🟡 Most Likely To Pump (No current pumps detected)", show_lines=True, style="candidate")

    table.add_column("Rank", justify="center")
    table.add_column("Symbol", justify="center")
    table.add_column("Price", justify="center")
    table.add_column("% Change (15m)", justify="center")
    table.add_column("Heat Score", justify="center")
    table.add_column("Pump Age", justify="center")
    table.add_column("Est. Duration", justify="center")

    display_list = pump_list if pump_list else candidate_list

    for i, p in enumerate(display_list, 1):
        table.add_row(
            str(i),
            p.get("symbol", ""),
            f"{p.get('price', 0):.6f}",
            f"{p.get('change_15m', 0):>6.2f}%",
            str(p.get("score", "")),
            f"{p.get('pump_age', 0)}m",
            f"{p.get('est_life', 0)}m"
        )
    console.print(table)
    print(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")

async def monitor():
    scanner = KuCoinScanner()
    await scanner.fetch_symbols()
    print(f"Tracking {len(scanner.symbols)} KuCoin pairs.")

    alerted = set()
    global sticky_coins

    while True:
        try:
            await scanner.update_all_ohlcv()
            pump_list = []
            candidate_list = []
            active_symbols = set()
            for symbol, df in scanner.ohlcv_data.items():
                if df is None or len(df) < 16:
                    continue
                df_ind = ta.calculate_indicators(df)
                base_score = ta.calculate_heat_score(df_ind)
                if base_score < 60:
                    continue

                price = df_ind['close'].iloc[-1]
                change = ((df_ind['close'].iloc[-1] - df_ind['close'].iloc[-15]) / df_ind['close'].iloc[-15]) * 100

                pump_age = 0
                try:
                    recent = df_ind[df_ind['volume'].rolling(5).mean() > 1.5 * df_ind['volume'].rolling(15).mean()]
                    if not recent.empty:
                        last_idx = recent.index[-1]
                        pump_age = len(df_ind) - last_idx - 1
                except Exception:
                    pump_age = 0
                est = estimate_pump_duration(df_ind)

                duration_bonus = min(est // 5, 10)
                meta_score, meta_count = parse_log_for_symbol(symbol)
                total_score = base_score + meta_score + duration_bonus

                indicators_snapshot = df_ind.iloc[-1].to_dict()
                log_pump_event(symbol, price, change, base_score, pump_age, est, indicators_snapshot)

                # Collect main pumps (est >= 15 min)
                if est >= 15:
                    pump_list.append({
                        "symbol": symbol,
                        "price": price,
                        "change_15m": change,
                        "score": total_score,
                        "pump_age": pump_age,
                        "est_life": est,
                        "log_hits": meta_count,
                        "meta_score": meta_score,
                        "duration_bonus": duration_bonus,
                    })
                    active_symbols.add(symbol)
                    if total_score >= 80 and change > 5 and symbol not in alerted:
                        send_telegram_alert(symbol, total_score, price, change, est, TOKEN, CHAT_ID)
                        alerted.add(symbol)
                elif base_score >= 70 or change > 2:
                    candidate_list.append({
                        "symbol": symbol,
                        "price": price,
                        "change_15m": change,
                        "score": total_score,
                        "pump_age": pump_age,
                        "est_life": est,
                        "log_hits": meta_count,
                        "meta_score": meta_score,
                        "duration_bonus": duration_bonus,
                    })
                    active_symbols.add(symbol)

            # --- Stickiness: keep recently shown coins in pump_list ---
            # Update sticky_coins counters
            shown_symbols = {c["symbol"] for c in pump_list}
            # Decay counters for coins NOT in the new pump_list
            for sym in list(sticky_coins.keys()):
                if sym not in shown_symbols and (sticky_coins[sym] > 0):
                    sticky_coins[sym] -= 1
                if sticky_coins[sym] <= 0 and sym not in shown_symbols:
                    del sticky_coins[sym]
            # Add or reset counters for newly shown coins
            for c in pump_list:
                sticky_coins[c["symbol"]] = STICKY_CYCLES

            # Add sticky coins back into pump_list if they have cycles left, unless they are "dead"
            all_symbols = {c["symbol"] for c in pump_list}
            for sym, cycles in sticky_coins.items():
                if sym not in all_symbols and cycles > 0:
                    # Try to retrieve last known details from previous candidate_list
                    for old in candidate_list:
                        if old["symbol"] == sym and old["score"] > 40 and old["est_life"] >= 5:
                            pump_list.append(old)
                            break

            # Sort and display
            pump_list.sort(key=lambda x: (x["est_life"], x["score"]), reverse=True)
            candidate_list.sort(key=lambda x: (x["score"], x["change_15m"]), reverse=True)
            display_top_pumps_with_candidates(pump_list, candidate_list if not pump_list else [])

            if not pump_list:
                print("No current pump candidates detected (Heat Score < 60 on all pairs, or Est. Duration < 15min).")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error in monitor loop: {e}")
            logging.error(f"Error in monitor loop: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(monitor())
