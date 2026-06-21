"""GAMBS entry point: splash -> main menu loop -> game dispatch."""

from __future__ import annotations

import random
import time

import readchar
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.games.crash_screen import play_crash
from gambs.save import SaveData, load_save, write_save
from gambs.ui import splash
from gambs.ui.components import balance_bar_text
from gambs.ui.menu import menu_panel, resolve_route
from gambs.ui.tutorial import should_show_tutorial, mark_tutorial_seen, tutorial_panel

CRASH_TUTORIAL = [
    "Enter a bet amount.",
    "Watch the multiplier rise from 1.00x.",
    "Press [C] to cash out before the rocket crashes.",
    "If it crashes first, you lose your bet.",
]


def _play_splash(console: Console) -> None:
    rng = random.Random()
    console.clear()
    for locked in range(6):
        frame = splash.reel_frame(locked, rng)
        console.clear()
        console.print(Align.center(Text(frame, style=config.COLORS["success"])))
        console.print(Align.center(Text("[ Terminal Game Station ]", style=config.COLORS["gold"])))
        time.sleep(0.35)
    console.print(Align.center(Text("Press any key to start...", style="dim")))
    readchar.readkey()


def _bet_prompt(console: Console, save: SaveData) -> float | None:
    """Ask for a bet; return a valid amount or None to cancel."""
    console.print(f"Balance: ${save.balance:,.2f}. Enter bet (blank to cancel): ", end="")
    raw = input().strip()
    if not raw:
        return None
    try:
        bet = float(raw)
    except ValueError:
        console.print(Text("Invalid amount.", style=config.COLORS["danger"]))
        return None
    if bet <= 0 or bet > save.balance:
        console.print(Text("Bet must be positive and within your balance.", style=config.COLORS["danger"]))
        return None
    return round(bet, 2)


def _run_crash(console: Console, save: SaveData) -> None:
    if should_show_tutorial(save, "crash"):
        console.clear()
        console.print(tutorial_panel("CRASH", CRASH_TUTORIAL))
        choice = readchar.readkey().lower()
        if choice == "d":
            mark_tutorial_seen(save, "crash")
    bet = _bet_prompt(console, save)
    if bet is None:
        return
    play_crash(console, save, bet)
    console.print(Text("Press any key to return to menu...", style="dim"))
    readchar.readkey()


def _coming_soon(console: Console, name: str) -> None:
    console.clear()
    console.print(Panel(Align.center(Text(f"{name} — coming soon", style=config.COLORS['info'])), style=config.COLORS["gold"]))
    console.print(Text("Press any key...", style="dim"))
    readchar.readkey()


def _make_console() -> Console:
    """Build the console, forcing UTF-8 so emoji/box glyphs don't crash on
    legacy Windows code pages (cp1252)."""
    try:
        import sys

        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass  # older stream without reconfigure; rich still degrades gracefully
    return Console()


def main() -> None:
    console = _make_console()
    save = load_save(config.SAVE_PATH)
    _play_splash(console)

    while True:
        console.clear()
        console.print(balance_bar_text(save))
        console.print(menu_panel(save))
        console.print("Select: ", end="")
        key = readchar.readkey()
        route = resolve_route(key)

        if route == "quit":
            write_save(config.SAVE_PATH, save)
            console.print(Text("Saved. See you next time. ♠", style=config.COLORS["gold"]))
            break
        elif route == "gamble":
            _run_crash(console, save)  # Plan 2 adds a game selector here
            write_save(config.SAVE_PATH, save)  # persist only after a state change
        elif route in ("earn", "shop", "vip", "stats"):
            _coming_soon(console, route.upper())
        # unknown key: loop again (no disk write)


if __name__ == "__main__":
    main()
