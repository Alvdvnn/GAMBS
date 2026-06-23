"""The single registry of Earn Mode mini-games.

Screen modules are imported lazily inside `all_earn_games()` so importing the
registry never triggers heavy/interactive imports at module load. Mirrors
gambs/games/registry.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rich.console import Console

from gambs.save import SaveData

RunFn = Callable[[Console, SaveData], None]


@dataclass
class EarnEntry:
    id: str
    label: str
    run: RunFn


def all_earn_games() -> list[EarnEntry]:
    """Return every registered earn game, in display order."""
    from gambs.earn.typing_heist_screen import run_typing_heist
    from gambs.earn.trading_screen import run_trading
    from gambs.earn.bounty_screen import run_bounty

    return [
        EarnEntry("typing_heist", "⌨  Typing Heist", run_typing_heist),
        EarnEntry("trading", "📈  Terminal Trading", run_trading),
        EarnEntry("bounty", "🎯  Bounty Jobs", run_bounty),
    ]
