"""Shared interactive helpers used by every game screen.

`bet_prompt` is unit-tested (input is monkeypatched). The other helpers wrap
`readchar`/`rich` rendering and are exercised by manual smoke tests.
"""

from __future__ import annotations

import readchar
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.difficulty import min_bet_for
from gambs.save import SaveData
from gambs.ui.tutorial import (
    should_show_tutorial,
    mark_tutorial_seen,
    tutorial_panel,
)


def bet_prompt(console: Console, save: SaveData) -> float | None:
    """Ask for a bet; return a valid amount within balance, or None to cancel.

    The minimum bet rises with VIP level (a balancing challenge), so high-rank
    players can no longer place trivial bets.
    """
    min_bet = min_bet_for(save.vip.level)
    console.print(
        f"Balance: ${save.balance:,.2f}. Min bet ${min_bet:,.0f}. "
        "Enter bet (blank to cancel): ",
        end="",
    )
    raw = input().strip()
    if not raw:
        return None
    try:
        bet = float(raw)
    except ValueError:
        console.print(Text("Invalid amount.", style=config.COLORS["danger"]))
        return None
    if bet < min_bet or bet > save.balance:
        console.print(
            Text(
                f"Bet must be at least ${min_bet:,.0f} and within your balance.",
                style=config.COLORS["danger"],
            )
        )
        return None
    return round(bet, 2)


def tutorial_gate(
    console: Console, save: SaveData, game_id: str, game_name: str, steps: list[str]
) -> None:
    """Show the tutorial once per game; [D] dismisses it permanently."""
    if not should_show_tutorial(save, game_id):
        return
    console.clear()
    console.print(tutorial_panel(game_name, steps))
    if readchar.readkey().lower() == "d":
        mark_tutorial_seen(save, game_id)


def result_banner(console: Console, won: bool, message: str) -> None:
    """Print a centered win/lose banner."""
    color = config.COLORS["success"] if won else config.COLORS["danger"]
    console.print(
        Panel(Align.center(Text(message, style=f"bold {color}")), style=config.COLORS["gold"])
    )


def pause(console: Console) -> None:
    """Wait for any keypress before returning to the previous screen."""
    console.print(Text("Press any key to return...", style="dim"))
    readchar.readkey()
