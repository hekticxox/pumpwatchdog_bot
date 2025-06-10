import time
from typing import List, Dict, Any, Optional
from rich.table import Table
from rich.console import Console
from rich.live import Live

def build_dashboard_table(
    pump_list: List[Dict[str, Any]],
    candidate_list: Optional[List[Dict[str, Any]]] = None
) -> Table:
    table = Table(title="KuCoin Top Bullish Scanner")

    table.add_column("Symbol", style="cyan", no_wrap=True)
    table.add_column("Score", justify="right")
    table.add_column("Triggers", style="magenta")
    table.add_column("Duration", justify="right")
    table.add_column("15m %", justify="right")
    table.add_column("Est Life", justify="right")
    table.add_column("Age", justify="right")
    table.add_column("Meta", justify="right")

    for entry in pump_list:
        symbol = entry.get("symbol", "-")
        score = f"{entry.get('score', 0):.2f}"
        triggers = str(entry.get("log_hits", "")) or "-"
        duration = f"{entry.get('duration_bonus', 0)}"
        gain = f"{entry.get('change_15m', 0):.2f}"
        est_life = f"{entry.get('est_life', 0)}"
        age = f"{entry.get('pump_age', 0)}"
        meta = f"{entry.get('meta_score', 0)}"
        table.add_row(symbol, score, triggers, duration, gain, est_life, age, meta)

    if candidate_list:
        table.add_row("", "", "", "", "", "", "", "")
        for entry in candidate_list:
            symbol = entry.get("symbol", "-")
            score = f"{entry.get('score', 0):.2f}"
            triggers = str(entry.get("log_hits", "")) or "-"
            duration = f"{entry.get('duration_bonus', 0)}"
            gain = f"{entry.get('change_15m', 0):.2f}"
            est_life = f"{entry.get('est_life', 0)}"
            age = f"{entry.get('pump_age', 0)}"
            meta = f"{entry.get('meta_score', 0)}"
            table.add_row(symbol, score, triggers, duration, gain, est_life, age, meta)
    return table

def live_dashboard(
    get_data_callback,
    refresh_interval: float = 2.0
):
    """
    Calls get_data_callback() repeatedly and updates the dashboard live.
    get_data_callback must return (pump_list, candidate_list)
    """
    console = Console()
    with Live(console=console, screen=False, auto_refresh=False) as live:
        while True:
            pump_list, candidate_list = get_data_callback()
            table = build_dashboard_table(pump_list, candidate_list)
            live.update(table, refresh=True)
            time.sleep(refresh_interval)

# If run as script (demo mode)
if __name__ == "__main__":
    import random

    def demo_data():
        # Generate fake live data
        return [
            {
                "symbol": "BTC/USDT",
                "score": random.uniform(80, 100),
                "log_hits": random.randint(1, 5),
                "duration_bonus": random.randint(10, 30),
                "change_15m": random.uniform(2, 8),
                "est_life": random.randint(10, 40),
                "pump_age": random.randint(1, 5),
                "meta_score": random.randint(5, 20)
            }
        ], [
            {
                "symbol": "DOGE/USDT",
                "score": random.uniform(60, 80),
                "log_hits": random.randint(0, 3),
                "duration_bonus": random.randint(5, 15),
                "change_15m": random.uniform(1, 3),
                "est_life": random.randint(5, 15),
                "pump_age": random.randint(0, 2),
                "meta_score": random.randint(1, 5)
            }
        ]

    live_dashboard(demo_data, refresh_interval=2.0)
