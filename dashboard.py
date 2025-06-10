import logging
from typing import List, Dict, Any, Optional

from rich.table import Table
from rich.console import Console
from rich.live import Live

def display_top_pumps(
    pump_list: List[Dict[str, Any]],
    candidate_list: Optional[List[Dict[str, Any]]] = None,
    refresh_interval: float = 0.5
) -> None:
    """
    Displays a live dashboard of the most bullish setups using `rich`.

    Args:
        pump_list (List[Dict[str, Any]]): List of main pump dictionaries.
        candidate_list (Optional[List[Dict[str, Any]]]): List of candidate pumps.
        refresh_interval (float): Dashboard refresh rate in seconds.
    """
    console = Console()
    table = Table(title="KuCoin Top 100 Bullish Scanner")

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

    # Optionally show candidate list
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

    # Live update the dashboard
    with Live(table, refresh_per_second=int(1 / refresh_interval), console=console, screen=False):
        pass  # Table is static per call; for live updating call this function repeatedly

if __name__ == "__main__":
    # Example usage
    import time
    example_pumps = [
        {"symbol": "BTC/USDT", "score": 92.5, "log_hits": 3, "duration_bonus": 20, "change_15m": 5.1, "est_life": 30, "pump_age": 2, "meta_score": 10},
        {"symbol": "ETH/USDT", "score": 85.2, "log_hits": 2, "duration_bonus": 15, "change_15m": 4.3, "est_life": 25, "pump_age": 1, "meta_score": 8}
    ]
    example_candidates = [
        {"symbol": "DOGE/USDT", "score": 60.0, "log_hits": 1, "duration_bonus": 10, "change_15m": 2.5, "est_life": 10, "pump_age": 0, "meta_score": 3}
    ]
    display_top_pumps(example_pumps, example_candidates)
    time.sleep(2)
