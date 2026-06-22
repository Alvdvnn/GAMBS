"""Gamble game selector: render the list and dispatch the chosen game."""

from __future__ import annotations

import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.games.registry import GameEntry, all_games
from gambs.save import SaveData, write_save
from gambs.ui.components import balance_bar_text


def game_menu_panel(games: list[GameEntry]) -> Panel:
    """Render the numbered list of games."""
    body = Text()
    for i, entry in enumerate(games, start=1):
        body.append(f" [{i}] ", style=f"bold {config.COLORS['gold']}")
        body.append(f"{entry.label}\n", style=f"bold {config.COLORS['gamble']}")
    body.append("\n [ESC] Back to main menu", style="dim")
    return Panel(
        body, title="GAMBLE — choose a game", title_align="left", style=config.COLORS["gamble"]
    )


def resolve_game_key(key: str, games: list[GameEntry]) -> GameEntry | None:
    """Map a digit key to a game entry, or None if out of range/non-digit."""
    if not key or not key.isdigit():
        return None
    idx = int(key) - 1
    if 0 <= idx < len(games):
        return games[idx]
    return None


def run_game_select(console: Console, save: SaveData) -> None:
    """Loop the selector until the player presses ESC/Q to go back."""
    games = all_games()
    while True:
        console.clear()
        console.print(balance_bar_text(save))
        console.print(game_menu_panel(games))
        console.print("Select game: ", end="")
        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        entry = resolve_game_key(key, games)
        if entry is not None:
            entry.run(console, save)
            write_save(config.SAVE_PATH, save)
