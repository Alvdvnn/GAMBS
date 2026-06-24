"""Cosmetics pure logic: theme catalog, ownership, and palette application.

Themes are pure vanity — zero gameplay impact. The active theme overrides
entries in `config.COLORS` (which every screen reads at call time), so applying
a theme propagates globally without per-screen rewiring.

Mutating helpers (`buy`, `equip`, `apply_active_theme`) change only the passed
SaveData / the shared palette.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path

from gambs import config
from gambs.save import SaveData

# Snapshot the default palette once, before any theme is applied, so we can
# restore it when the player equips a theme that doesn't override a key.
_BASE_PALETTE: dict[str, str] = copy.deepcopy(config.COLORS)


@dataclass
class Theme:
    id: str
    name: str
    price: float
    unlock_level: int
    palette: dict[str, str]


def load_themes(path: Path) -> list[Theme]:
    """Load the cosmetics catalog from a JSON array file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Theme(
            id=row["id"],
            name=row["name"],
            price=float(row["price"]),
            unlock_level=int(row.get("unlock_level", 1)),
            palette=dict(row.get("palette", {})),
        )
        for row in data
    ]


def find_theme(themes: list[Theme], theme_id: str) -> Theme | None:
    return next((t for t in themes if t.id == theme_id), None)


def is_owned(save: SaveData, theme_id: str) -> bool:
    return theme_id in save.cosmetics.get("owned", [])


def is_active(save: SaveData, theme_id: str) -> bool:
    return save.cosmetics.get("active") == theme_id


def can_buy(save: SaveData, theme: Theme) -> bool:
    """True if the theme is unowned, affordable, and VIP-unlocked."""
    if is_owned(save, theme.id):
        return False
    if save.vip.level < theme.unlock_level:
        return False
    return save.balance >= theme.price


def buy(save: SaveData, theme: Theme) -> bool:
    """Purchase a theme into the owned set (does not auto-equip)."""
    if not can_buy(save, theme):
        return False
    save.balance = round(save.balance - theme.price, 2)
    save.cosmetics.setdefault("owned", []).append(theme.id)
    return True


def equip(save: SaveData, theme_id: str) -> bool:
    """Set the active theme; must already be owned."""
    if not is_owned(save, theme_id):
        return False
    save.cosmetics["active"] = theme_id
    return True


def apply_active_theme(save: SaveData, themes: list[Theme]) -> None:
    """Mutate the shared palette to the active theme's overrides.

    Resets to the base palette first, then layers the active theme's overrides,
    so switching themes never leaves stale colors behind.
    """
    config.COLORS.clear()
    config.COLORS.update(_BASE_PALETTE)
    active = find_theme(themes, save.cosmetics.get("active", "default"))
    if active:
        config.COLORS.update(active.palette)
