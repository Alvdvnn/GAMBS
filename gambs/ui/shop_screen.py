"""Item Shop screen: browse the catalog and buy consumables. Interactive layer.

Render/IO only (manual-smoke); purchase logic lives in gambs/shop.py.
"""

from __future__ import annotations

import readchar
from rich.console import Console
from rich.table import Table

from gambs import config
from gambs.save import SaveData, write_save
from gambs.shop import Item, load_items, can_afford, owned_charges, purchase
from gambs.ui.components import balance_bar_text


def shop_table(save: SaveData, items: list[Item]) -> Table:
    """Render the catalog: index, name, effect, price, and owned charges."""
    table = Table(
        title="ITEM SHOP",
        title_style=f"bold {config.COLORS['gold']}",
        title_justify="left",
        style=config.COLORS["gold"],
        expand=True,
    )
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Item", style=f"bold {config.COLORS['info']}")
    table.add_column("Effect", style="white")
    table.add_column("Price", justify="right", style=config.COLORS["gold"])
    table.add_column("Owned", justify="right")

    for i, item in enumerate(items, start=1):
        affordable = can_afford(save, item)
        owned = owned_charges(save, item.id)
        row_style = None if affordable else "dim"
        owned_text = (
            f"[{config.COLORS['success']}]{owned}[/]" if owned else "0"
        )
        table.add_row(
            f"[{i}]",
            item.name,
            item.effect,
            f"${item.price:,.0f}",
            owned_text,
            style=row_style,
        )
    return table


def run_shop(console: Console, save: SaveData) -> None:
    """Loop the shop until the player presses ESC/Q to go back."""
    items = load_items(config.ITEMS_PATH)
    message = ""
    while True:
        console.clear()
        console.print(balance_bar_text(save))
        console.print(shop_table(save, items))
        if message:
            console.print(message)
        console.print(
            f"[1-{len(items)}] buy   [ESC] back", style="dim"
        )
        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        if not key.isdigit():
            message = ""
            continue
        idx = int(key) - 1
        if not (0 <= idx < len(items)):
            message = ""
            continue
        item = items[idx]
        if purchase(save, item):
            write_save(config.SAVE_PATH, save)
            message = f"[{config.COLORS['success']}]Bought {item.name}.[/]"
        else:
            message = f"[{config.COLORS['danger']}]Not enough cash for {item.name}.[/]"
