"""Main menu: pure key->route resolution and the menu panel renderer."""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.save import SaveData

ROUTES: dict[str, str] = {
    "g": "gamble",
    "e": "earn",
    "p": "shop",
    "v": "vip",
    "s": "stats",
    "q": "quit",
}

_MENU_ITEMS = [
    ("G", "GAMBLE", "Play the casino games", "gamble"),
    ("E", "EARN", "Work mini-games for cash", "earn"),
    ("P", "SHOP", "Buy items & cosmetics", "gamble"),
    ("V", "VIP", "Level, XP & prestige", "earn"),
    ("S", "STATS", "Your record so far", "info"),
    ("Q", "QUIT", "Save and exit", "danger"),
]


def resolve_route(key: str) -> str | None:
    """Map a pressed key to a route name, or None if unbound."""
    if not key:
        return None
    return ROUTES.get(key.lower())


def menu_panel(save: SaveData) -> Panel:
    """Render the main menu as a rich Panel."""
    body = Text()
    for hotkey, label, desc, color_key in _MENU_ITEMS:
        color = config.COLORS.get(color_key, config.COLORS["gold"])
        body.append(f" [{hotkey}] ", style=f"bold {config.COLORS['gold']}")
        body.append(f"{label:<8}", style=f"bold {color}")
        body.append(f"  {desc}\n", style="white")
    return Panel(
        body,
        title="MAIN MENU",
        title_align="left",
        style=config.COLORS["gold"],
    )
