"""Cosmetics screen: buy and equip terminal themes. Interactive layer.

Render/IO only (manual-smoke); theme logic lives in gambs/cosmetics.py.
Equipping applies the palette live so the change is visible immediately.
"""

from __future__ import annotations

import readchar
from rich.console import Console
from rich.table import Table

from gambs import config
from gambs.cosmetics import (
    Theme,
    apply_active_theme,
    buy,
    can_buy,
    equip,
    is_active,
    is_owned,
    load_themes,
)
from gambs.save import SaveData, write_save
from gambs.ui.components import balance_bar_text


def _status(save: SaveData, theme: Theme) -> str:
    if is_active(save, theme.id):
        return f"[{config.COLORS['success']}]ACTIVE[/]"
    if is_owned(save, theme.id):
        return "owned"
    if save.vip.level < theme.unlock_level:
        return f"[dim]locked (VIP {theme.unlock_level})[/]"
    return f"${theme.price:,.0f}"


def cosmetics_table(save: SaveData, themes: list[Theme]) -> Table:
    """Render the theme catalog with price/owned/active/locked status."""
    table = Table(
        title="COSMETICS — terminal themes (vanity only)",
        title_style=f"bold {config.COLORS['gold']}",
        title_justify="left",
        style=config.COLORS["gold"],
        expand=True,
    )
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Theme", style=f"bold {config.COLORS['info']}")
    table.add_column("Status", justify="right")
    for i, theme in enumerate(themes, start=1):
        table.add_row(f"[{i}]", theme.name, _status(save, theme))
    return table


def run_cosmetics(console: Console, save: SaveData) -> None:
    """Loop the cosmetics screen until ESC/Q. Digit buys+equips or equips."""
    themes = load_themes(config.COSMETICS_PATH)
    message = ""
    while True:
        console.clear()
        console.print(balance_bar_text(save))
        console.print(cosmetics_table(save, themes))
        if message:
            console.print(message)
        console.print(
            f"[1-{len(themes)}] buy/equip   [ESC] back", style="dim"
        )
        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        if not key.isdigit():
            message = ""
            continue
        idx = int(key) - 1
        if not (0 <= idx < len(themes)):
            message = ""
            continue
        theme = themes[idx]
        if is_owned(save, theme.id):
            equip(save, theme.id)
            message = f"[{config.COLORS['success']}]Equipped {theme.name}.[/]"
        elif can_buy(save, theme):
            buy(save, theme)
            equip(save, theme.id)
            message = f"[{config.COLORS['success']}]Bought & equipped {theme.name}.[/]"
        elif save.vip.level < theme.unlock_level:
            message = f"[{config.COLORS['danger']}]{theme.name} unlocks at VIP {theme.unlock_level}.[/]"
        else:
            message = f"[{config.COLORS['danger']}]Not enough cash for {theme.name}.[/]"
        apply_active_theme(save, themes)
        write_save(config.SAVE_PATH, save)
