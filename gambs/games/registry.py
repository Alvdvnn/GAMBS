"""The single registry of playable gamble games.

Screen modules are imported lazily inside `all_games()` so importing the
registry never triggers heavy/interactive imports at module load.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rich.console import Console

from gambs.save import SaveData

RunFn = Callable[[Console, SaveData], None]


@dataclass
class GameEntry:
    id: str
    label: str
    run: RunFn


def all_games() -> list[GameEntry]:
    """Return every registered game, in display order."""
    from gambs.games.crash_screen import run_crash
    from gambs.games.coinflip_screen import run_coinflip
    from gambs.games.dice_screen import run_dice
    from gambs.games.slots_screen import run_slots
    from gambs.games.roulette_screen import run_roulette
    from gambs.games.blackjack_screen import run_blackjack
    from gambs.games.baccarat_screen import run_baccarat

    return [
        GameEntry("crash", "🚀 Crash", run_crash),
        GameEntry("coinflip", "🪙 Coin Flip", run_coinflip),
        GameEntry("dice", "🎲 Dice", run_dice),
        GameEntry("slots", "🎰 Slots", run_slots),
        GameEntry("roulette", "🎡 Roulette", run_roulette),
        GameEntry("blackjack", "🃏 Blackjack", run_blackjack),
        GameEntry("baccarat", "🎴 Baccarat", run_baccarat),
    ]
