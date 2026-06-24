"""Item Shop pure logic: catalog loading, lookup, and purchase.

No RNG and no rendering. `purchase` is the only mutating function and it
changes only the SaveData passed to it. Item effects are NOT applied here —
this layer just sells items and tracks owned charges.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from gambs.save import SaveData


@dataclass
class Item:
    id: str
    name: str
    effect: str
    charges: int
    price: float


def load_items(path: Path) -> list[Item]:
    """Load the item catalog from a JSON array file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Item(
            id=row["id"],
            name=row["name"],
            effect=row["effect"],
            charges=int(row["charges"]),
            price=float(row["price"]),
        )
        for row in data
    ]


def find_item(items: list[Item], item_id: str) -> Item | None:
    """Return the catalog item with this id, or None."""
    return next((it for it in items if it.id == item_id), None)


def _inventory_entry(save: SaveData, item_id: str) -> dict | None:
    return next((e for e in save.inventory if e.get("item_id") == item_id), None)


def owned_charges(save: SaveData, item_id: str) -> int:
    """How many charges of this item the player currently holds (0 if none)."""
    entry = _inventory_entry(save, item_id)
    return int(entry["charges"]) if entry else 0


def can_afford(save: SaveData, item: Item) -> bool:
    """True if the balance covers the item's price (inclusive)."""
    return save.balance >= item.price


def purchase(save: SaveData, item: Item) -> bool:
    """Buy one unit of `item`: deduct price, top up charges additively.

    Returns False without mutating anything if the player cannot afford it.
    Re-buying an owned item adds its charge count to the existing entry.
    """
    if not can_afford(save, item):
        return False
    save.balance = round(save.balance - item.price, 2)
    entry = _inventory_entry(save, item.id)
    if entry is None:
        save.inventory.append({"item_id": item.id, "charges": item.charges})
    else:
        entry["charges"] = int(entry["charges"]) + item.charges
    return True
