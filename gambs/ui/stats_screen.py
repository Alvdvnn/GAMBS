"""Stats screen: render the player's lifetime record. Read-only.

Interactive/render layer (manual-smoke only); derived metrics live in
gambs/ui/stats.py.
"""

from __future__ import annotations

import time

import readchar
from rich.console import Console
from rich.table import Table

from gambs import config
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.stats import net_pl, stats_rows


def stats_panel(save: SaveData, session_seconds: int) -> Table:
    """Build the stats table from the row model, coloring P/L by sign."""
    table = Table(
        title="STATS — your record",
        title_style=f"bold {config.COLORS['gold']}",
        title_justify="left",
        style=config.COLORS["gold"],
        show_header=False,
        expand=True,
    )
    table.add_column("Stat", style="dim")
    table.add_column("Value", justify="right", style=f"bold {config.COLORS['info']}")

    pl_style = config.COLORS["success"] if net_pl(save) >= 0 else config.COLORS["danger"]
    for label, value in stats_rows(save, session_seconds):
        value_style = pl_style if label == "Net P/L" else None
        table.add_row(label, value if value_style is None else f"[{value_style}]{value}[/]")
    return table


def run_stats(console: Console, save: SaveData, session_start: float) -> None:
    """Show the stats screen until the player presses a key to go back."""
    session_seconds = int(time.monotonic() - session_start)
    console.clear()
    console.print(balance_bar_text(save))
    console.print(stats_panel(save, session_seconds))
    console.print("Press any key to return...", style="dim")
    readchar.readkey()
