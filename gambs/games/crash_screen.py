"""Interactive Crash screen. All outcome math lives in games/crash.py."""

from __future__ import annotations

import random
import time

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.games import crash
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, pause
from gambs.vip import activity_xp, add_xp


def _read_key_nonblocking() -> str | None:
    """Return a pressed key if one is waiting, else None (Windows + POSIX)."""
    try:
        import msvcrt  # Windows
        if msvcrt.kbhit():
            return msvcrt.getwch()
        return None
    except ImportError:
        import select
        import sys
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            return sys.stdin.read(1)
        return None


def _rocket_panel(multiplier: float, status: str, color: str) -> Panel:
    art = Text()
    art.append(f"\n   {multiplier:.2f}x\n\n", style=f"bold {color}")
    art.append("   🚀\n\n", style=color)
    art.append(status, style=config.COLORS["gold"])
    return Panel(Align.center(art), title="CRASH", style=color)


def play_crash(console: Console, save: SaveData, bet: float) -> crash.CrashResult:
    """Run one crash round against the player's balance and return the result.

    The caller is responsible for having already validated `bet` against the
    balance and for persisting `save` afterward.
    """
    rng = random.Random()
    crash_point = crash.generate_crash_point(rng)
    start = time.monotonic()
    cashout: float | None = None

    with Live(console=console, refresh_per_second=30, screen=False) as live:
        while True:
            elapsed = time.monotonic() - start
            current = crash.multiplier_at(elapsed)
            if current >= crash_point:
                break
            key = _read_key_nonblocking()
            if key and key.lower() == "c":
                cashout = current
                break
            live.update(
                _rocket_panel(current, "[C] CASH OUT", config.COLORS["success"])
            )
            time.sleep(config.CRASH_TICK_SECONDS)

    result = crash.resolve_round(bet, crash_point, cashout)

    # Apply result to balance and stats.
    save.balance = round(save.balance + result.net, 2)
    save.stats.total_wagered += bet
    save.stats.games_played += 1
    if result.won:
        save.stats.total_won += result.winnings
        save.stats.best_crash_multiplier = max(
            save.stats.best_crash_multiplier, result.cashout_multiplier or 0.0
        )
    add_xp(save, activity_xp(bet))

    if result.won:
        msg = Text(
            f"CASHED OUT at {result.cashout_multiplier:.2f}x  +${result.winnings:,.2f}",
            style=f"bold {config.COLORS['success']}",
        )
    else:
        msg = Text(
            f"💥 CRASHED at {crash_point:.2f}x  -${bet:,.2f}",
            style=f"bold {config.COLORS['danger']}",
        )
    console.print(Panel(Align.center(msg), style=config.COLORS["gold"]))
    console.print(balance_bar_text(save))
    return result


CRASH_TUTORIAL = [
    "Enter a bet amount.",
    "Watch the multiplier rise from 1.00x.",
    "Press [C] to cash out before the rocket crashes.",
    "If it crashes first, you lose your bet.",
]


def run_crash(console: Console, save: SaveData) -> None:
    """Full Crash round flow: tutorial gate -> bet -> play -> pause."""
    tutorial_gate(console, save, "crash", "CRASH", CRASH_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    play_crash(console, save, bet)
    pause(console)
