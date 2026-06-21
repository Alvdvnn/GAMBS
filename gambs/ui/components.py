"""Shared UI render helpers. Pure text/renderable builders."""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.save import SaveData


def balance_bar_text(save: SaveData) -> str:
    """Plain-text content of the always-visible status bar."""
    return (
        f"♠ GAMBS   "
        f"\U0001f4b0 ${save.balance:,.2f}   "
        f"⭐ VIP {save.vip.level} "
        f"({save.vip.xp}/{config.VIP_XP_PER_LEVEL} XP)"
    )


def balance_bar_panel(save: SaveData) -> Panel:
    """Rich panel wrapping the status bar, styled gold-on-dark."""
    body = Text(balance_bar_text(save), style=config.COLORS["gold"])
    return Panel(body, style=config.COLORS["gold"], expand=True)
