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
from gambs.ui.earn_select import run_earn_select
from gambs.save import SaveData, load_save, write_save
from gambs.ui import splash
from gambs.ui.components import balance_bar_text
from gambs.ui.game_select import run_game_select
from gambs.ui.menu import menu_panel, resolve_route
from gambs.ui.shop_screen import run_shop
from gambs.ui.stats_screen import run_stats


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
    session_start = time.monotonic()
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
            run_game_select(console, save)
            write_save(config.SAVE_PATH, save)
        elif route == "earn":
            run_earn_select(console, save)
            write_save(config.SAVE_PATH, save)
        elif route == "shop":
            run_shop(console, save)
        elif route == "stats":
            run_stats(console, save, session_start)
        elif route == "vip":
            _coming_soon(console, route.upper())
        # unknown key: loop again (no disk write)


if __name__ == "__main__":
    main()
