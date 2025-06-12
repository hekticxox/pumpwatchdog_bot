import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.")

import time
import csv
import os
import ccxt
import argparse
from indicators import get_real_indicators
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.live import Live

LOG_FILE = "pumpwatchdog_log.csv"
DISPLAY_LIMIT = 20  # Show more coins
THREAD_WORKERS = 12

def get_top_usdt_pairs(n=100, exchange_name='kucoin', verbose=False):
    try:
        exchange = getattr(ccxt, exchange_name)()
        tickers = exchange.fetch_tickers()
        usdt_pairs = [
            symbol for symbol in tickers
            if symbol.endswith('/USDT')
            and not symbol.startswith('BULL/')
            and not symbol.startswith('BEAR/')
            and not symbol.startswith('UP/')
            and not symbol.startswith('DOWN/')
        ]
        usdt_pairs.sort(key=lambda s: tickers[s].get('quoteVolume', 0), reverse=True)
        if verbose:
            print(f"[DEBUG] Found {len(usdt_pairs)} USDT pairs, selecting top {n}.")
        return usdt_pairs[:n]
    except Exception as e:
        print(f"Error fetching dynamic pairs: {e}")
        return [
            "UNI/USDT", "ETH/USDT", "BTC/USDT", "AVAX/USDT",
            "DOGE/USDT", "PEPE/USDT", "LAUNCHCOIN/USDT"
        ]

def log_scan(rows, filename=LOG_FILE):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = [
            "rank", "symbol", "score", "status", "conf%", "pumptime",
            "age", "num_triggers", "change_15m", "change_30m", "triggers"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

def get_status(num_triggers, score):
    if num_triggers >= 20:
        return "🟣 PARABOLIC"
    if num_triggers >= 15:
        return "🟢 STRONGUPTREND"
    if score >= 10:
        return "🔥 HOT"
    elif score >= 7:
        return "🚀 Pump"
    elif score >= 4:
        return "Watch"
    elif score > 0:
        return "Weak"
    else:
        return "N/A"

def get_status_color(status):
    if status == "🟣 PARABOLIC":
        return "bold magenta"
    if status == "🟢 STRONGUPTREND":
        return "bold green"
    if status == "🔥 HOT":
        return "bold red"
    if status == "🚀 Pump":
        return "bold yellow"
    if status == "Watch":
        return "cyan"
    if status == "Weak":
        return "grey50"
    return "white"

def fetch_symbol_indicators(symbol, verbose=False):
    if verbose:
        print(f"[VERBOSE] Starting scan for {symbol}")
    try:
        indicators, used_exchange = get_real_indicators(symbol, fallback=False, return_exchange=True)
    except TypeError:
        try:
            indicators = get_real_indicators(symbol, fallback=False)
            used_exchange = None
        except Exception as e:
            if verbose:
                print(f"[DEBUG] Error in get_real_indicators for {symbol}: {e}")
            indicators = None
            used_exchange = None
    except Exception as e:
        if verbose:
            print(f"[DEBUG] Unexpected error in get_real_indicators for {symbol}: {e}")
        indicators = None
        used_exchange = None

    if indicators is None:
        if verbose:
            print(f"[DEBUG] No indicator data for {symbol}")
        return (symbol, None, None)
    if len(indicators.get("trigger_list", [])) == 0:
        if verbose:
            print(f"[DEBUG] No triggers fired for {symbol}")
    else:
        if verbose:
            print(f"[DEBUG] {symbol}: {len(indicators.get('trigger_list', []))} triggers fired")
    if verbose:
        print(f"[VERBOSE] Finished scan for {symbol}")
    return (symbol, indicators, used_exchange)

def build_table(symbol_rows, symbol_age, display_limit=DISPLAY_LIMIT):
    table = Table(title="Top Bullish Coins", highlight=True, border_style="bright_magenta")
    table.add_column("Rank", justify="right", style="bold", no_wrap=True)
    table.add_column("Symbol", style="bold")
    table.add_column("Score", justify="center")
    table.add_column("Status", style="bold")
    table.add_column("Conf%", justify="center")
    table.add_column("PumpTime", justify="center")
    table.add_column("Age", justify="center")
    table.add_column("#Trig", justify="center")
    table.add_column("%Δ15m", justify="right")
    table.add_column("%Δ30m", justify="right")
    # Triggers column removed from table

    display_idx = 1
    for symbol, indicators, used_exchange in symbol_rows[:display_limit]:
        if indicators is None:
            continue
        score = indicators.get("score", 0)
        conf = indicators.get("confidence", 0)
        pumptime = indicators.get("pumptime", "N/A")
        age = symbol_age.get(symbol, 1)
        triggers = indicators.get("trigger_list", [])
        num_triggers = len(triggers)
        status = get_status(num_triggers, score)
        status_color = get_status_color(status)
        notable = status in ["🟣 PARABOLIC", "🔥 HOT", "🚀 Pump", "🟢 STRONGUPTREND"]
        star = "★" if notable else ""
        change_15m = indicators.get("change_15m", "N/A")
        change_30m = indicators.get("change_30m", "N/A")
        def fmt_pct(val):
            try:
                v = float(val)
                return f"{v:+.2f}%"
            except:
                return str(val)
        table.add_row(
            f"{display_idx}{star}",
            f"[white]{symbol}[/white]" if not notable else f"[bold magenta]{symbol}[/bold magenta]",
            f"[bold]{score}[/bold]",
            f"[{status_color}]{status}[/{status_color}]",
            f"{conf}%",
            f"{pumptime}",
            f"{age}",
            f"{num_triggers}",
            fmt_pct(change_15m),
            fmt_pct(change_30m),
        )
        display_idx += 1
    return table

def update_symbol_ages(symbol_age, top_symbols):
    new_symbol_age = {}
    for symbol in top_symbols:
        if symbol in symbol_age:
            new_symbol_age[symbol] = symbol_age[symbol] + 1
        else:
            new_symbol_age[symbol] = 1
    return new_symbol_age

def main():
    parser = argparse.ArgumentParser(description='PumpWatchdog Multi-Timeframe Scanner')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose debug output')
    args = parser.parse_args()
    verbose = args.verbose

    console = Console()
    console.rule("[bold cyan]🚨 PumpWatchdog Multi-Timeframe Scanner (REAL DATA) 🚨", style="bold blue")

    symbol_age = {}

    try:
        while True:
            cycle_start_time = time.time()
            SYMBOLS = get_top_usdt_pairs(n=100, verbose=verbose)
            result_rows = []
            symbol_rows = []
            notable_coins = []

            if not SYMBOLS:
                console.print("[yellow][DEBUG] No symbols found from exchange.[/yellow]")
                time.sleep(60)
                continue
            else:
                if verbose:
                    console.print(f"[yellow][DEBUG] Checking {len(SYMBOLS)} symbols from KuCoin...[/yellow]")

            completed_map = {}
            symbol_rows_live = [(s, None, None) for s in SYMBOLS]

            with Live(build_table(symbol_rows_live, symbol_age, DISPLAY_LIMIT), refresh_per_second=4, console=console, screen=False) as live:
                with ThreadPoolExecutor(max_workers=THREAD_WORKERS) as executor:
                    futures = {executor.submit(fetch_symbol_indicators, symbol, verbose): symbol for symbol in SYMBOLS}
                    for future in as_completed(futures):
                        symbol, indicators, used_exchange = future.result()
                        completed_map[symbol] = (symbol, indicators, used_exchange)
                        symbol_rows_live = [completed_map.get(s, (s, None, None)) for s in SYMBOLS]
                        displayable = [row for row in symbol_rows_live if row[1] is not None]
                        displayable.sort(key=lambda x: (x[1]['score'] if x[1] else 0), reverse=True)
                        not_displayed = [row for row in symbol_rows_live if row[1] is None]
                        table_data = displayable[:DISPLAY_LIMIT] + not_displayed[:max(0, DISPLAY_LIMIT-len(displayable))]
                        live.update(build_table(table_data, symbol_age, DISPLAY_LIMIT))

                symbol_rows = sorted([completed_map[s] for s in SYMBOLS if completed_map[s][1] is not None],
                                     key=lambda x: (x[1]['score'] if x[1] else 0), reverse=True)
                top_n_symbols = [row[0] for row in symbol_rows[:DISPLAY_LIMIT] if row[1] is not None]
                symbol_age = update_symbol_ages(symbol_age, top_n_symbols)
                symbol_rows = symbol_rows[:DISPLAY_LIMIT]
                symbol_rows += [completed_map[s] for s in SYMBOLS if completed_map[s][1] is None][:max(0, DISPLAY_LIMIT - len(symbol_rows))]

            console.print(build_table(symbol_rows, symbol_age, DISPLAY_LIMIT))

            display_idx = 1
            for symbol, indicators, used_exchange in symbol_rows:
                if display_idx > DISPLAY_LIMIT:
                    break
                if indicators is None:
                    continue
                score = indicators.get("score", 0)
                conf = indicators.get("confidence", 0)
                pumptime = indicators.get("pumptime", "N/A")
                age = symbol_age.get(symbol, 1)
                triggers = indicators.get("trigger_list", [])
                num_triggers = len(triggers)
                status = get_status(num_triggers, score)
                notable = status in ["🟣 PARABOLIC", "🔥 HOT", "🚀 Pump", "🟢 STRONGUPTREND"]
                change_15m = indicators.get("change_15m", "N/A")
                change_30m = indicators.get("change_30m", "N/A")
                def fmt_pct(val):
                    try:
                        v = float(val)
                        return f"{v:+.2f}%"
                    except:
                        return str(val)
                result_rows.append({
                    "rank": display_idx,
                    "symbol": symbol,
                    "score": score,
                    "status": status,
                    "conf%": conf,
                    "pumptime": pumptime,
                    "age": age,
                    "num_triggers": num_triggers,
                    "change_15m": fmt_pct(change_15m),
                    "change_30m": fmt_pct(change_30m),
                    "triggers": " ".join(triggers)  # Log full triggers in CSV only
                })
                if notable:
                    notable_coins.append({
                        "symbol": symbol,
                        "score": score,
                        "status": status,
                        "triggers": " ".join(triggers)
                    })
                display_idx += 1

            log_scan(result_rows)
            console.print("-" * 110)

            panel_content = ""
            if notable_coins:
                for coin in notable_coins:
                    panel_content += f"[bold magenta]{coin['symbol']}[/bold magenta]: [bold]{coin['status']}[/bold] | Score: [bold]{coin['score']}[/bold] | Triggers: [dim]{coin['triggers']}[/dim]\n"
            else:
                panel_content = "[red]No notable coins found this scan.[/red]"
            console.print(Panel(panel_content, title="Notable Coins This Scan (PARABOLIC / HOT / Pump / STRONGUPTREND)", border_style="bold bright_cyan"))

            cycle_end_time = time.time()
            if verbose:
                elapsed = cycle_end_time - cycle_start_time
                console.print(f"[bold green][VERBOSE] Scan completed in {elapsed:.2f}s for {len(SYMBOLS)} symbols.[/bold green]")

            console.print("-" * 110)
            console.print("[dim]Press Ctrl+C to exit. Refreshing in 60 seconds...[/dim]\n")
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nExiting gracefully.")

if __name__ == "__main__":
    main()
