from rich.console import Console
from rich.table import Table
from datetime import datetime, timezone

def display_top_pumps(pump_data, top_n=10):
    console = Console()
    table = Table(title="🔥 Top Pumping Coins (Ranked by Heat Score)", show_lines=True)

    table.add_column("Rank", justify="center")
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Price", justify="right")
    table.add_column("% Change (15m)", justify="right")
    table.add_column("Heat Score", justify="center")
    table.add_column("Pump Age", justify="right")
    table.add_column("Est. Duration", justify="right")

    for i, data in enumerate(pump_data[:top_n], start=1):
        table.add_row(
            f"{i}",
            data["symbol"],
            f"{data['price']:.6f}",
            f"{data['change_15m']:.2f}%",
            f"[bold {'green' if data['score'] >= 80 else 'yellow' if data['score'] >= 60 else 'red'}]{data['score']}[/]",
            f"{data['pump_age']}m",
            f"{data['est_life']}m"
        )
    console.clear()
    console.print(table)
    console.print(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
