"""VIP screen: show level, XP progress, prestige, and the privilege table.

Interactive/render layer (manual-smoke); progression logic lives in
gambs/vip.py. Offers a prestige action when the player is at the max level.
"""

from __future__ import annotations

import readchar
from rich.console import Console
from rich.table import Table
from rich.text import Text

from gambs import config
from gambs.save import SaveData, write_save
from gambs.ui.components import balance_bar_text
from gambs.vip import can_prestige, do_prestige, privilege_bands, xp_to_next


def _xp_bar(save: SaveData, width: int = 24) -> str:
    """A simple [####----] progress bar for XP within the current level."""
    filled = int(width * save.vip.xp / config.VIP_XP_PER_LEVEL)
    filled = max(0, min(width, filled))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def vip_panel(save: SaveData) -> Table:
    """Build the privilege/challenge table, marking the player's active band."""
    vip = save.vip
    table = Table(
        title=(
            f"VIP — Level {vip.level}  ·  Prestige {vip.prestige}  ·  "
            f"Luck +{vip.luck_buff * 100:.0f}%"
        ),
        title_style=f"bold {config.COLORS['gold']}",
        title_justify="left",
        style=config.COLORS["gold"],
        expand=True,
    )
    table.add_column("Lvl", justify="right", style="dim", no_wrap=True)
    table.add_column("Privilege", style=f"bold {config.COLORS['info']}")
    table.add_column("Challenge", style="white")

    bands = privilege_bands()
    for i, (min_level, priv, chal) in enumerate(bands):
        nxt = bands[i + 1][0] if i + 1 < len(bands) else config.MAX_VIP_LEVEL + 1
        active = min_level <= vip.level < nxt
        marker = "> " if active else "  "
        row_style = config.COLORS["success"] if active else None
        table.add_row(f"{marker}{min_level}+", priv, chal, style=row_style)
    return table


def run_vip(console: Console, save: SaveData) -> None:
    """Show the VIP screen; allow prestige at max level, ESC/Q to go back."""
    while True:
        console.clear()
        console.print(balance_bar_text(save))
        console.print(vip_panel(save))
        bar = _xp_bar(save)
        console.print(
            Text(
                f"XP {save.vip.xp}/{config.VIP_XP_PER_LEVEL}  {bar}  "
                f"({xp_to_next(save)} to next)",
                style=config.COLORS["info"],
            )
        )
        if can_prestige(save):
            console.print(
                Text(
                    "[P] PRESTIGE — reset to Level 1 for a permanent +"
                    f"{config.PRESTIGE_LUCK_STEP * 100:.0f}% luck buff",
                    style=f"bold {config.COLORS['gold']}",
                )
            )
        console.print("[ESC] back", style="dim")

        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        if key in ("p", "P") and can_prestige(save):
            do_prestige(save)
            write_save(config.SAVE_PATH, save)
