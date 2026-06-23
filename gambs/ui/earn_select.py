"""Earn game selector: render the list and dispatch the chosen mini-game.

Mirrors gambs/ui/game_select.py but uses the earn registry and the magenta
earn theme.
"""

from __future__ import annotations

import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.earn.registry import EarnEntry, all_earn_games
from gambs.save import SaveData, write_save
from gambs.ui.components import balance_bar_text


def earn_menu_panel(games: list[EarnEntry]) -> Panel:
    """Render the numbered list of earn games."""
    body = Text()
    for i, entry in enumerate(games, start=1):
        body.append(f" [{i}] ", style=f"bold {config.COLORS['gold']}")
        body.append(f"{entry.label}\n", style=f"bold {config.COLORS['earn']}")
    body.append("\n [ESC] Back to main menu", style="dim")
    return Panel(
        body,
        title="EARN — choose a job",
        title_align="left",
        style=config.COLORS["earn"],
    )


def resolve_earn_key(key: str, games: list[EarnEntry]) -> EarnEntry | None:
    """Map a digit key to an earn entry, or None if out of range/non-digit."""
    if not key or not key.isdigit():
        return None
    idx = int(key) - 1
    if 0 <= idx < len(games):
        return games[idx]
    return None


def run_earn_select(console: Console, save: SaveData) -> None:
    """Loop the earn selector until the player presses ESC/Q to go back."""
    games = all_earn_games()
    while True:
        console.clear()
        console.print(balance_bar_text(save))
        console.print(earn_menu_panel(games))
        console.print("Select job: ", end="")
        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        entry = resolve_earn_key(key, games)
        if entry is not None:
            entry.run(console, save)
            write_save(config.SAVE_PATH, save)
