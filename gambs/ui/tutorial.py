"""Tutorial framework: seen/unseen state plus the tutorial screen renderer."""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.save import SaveData


def should_show_tutorial(save: SaveData, game_id: str) -> bool:
    """True when this game's tutorial has not yet been dismissed."""
    return game_id not in save.tutorial_seen


def mark_tutorial_seen(save: SaveData, game_id: str) -> None:
    """Record that the player has dismissed this game's tutorial (idempotent)."""
    if game_id not in save.tutorial_seen:
        save.tutorial_seen.append(game_id)


def tutorial_panel(game_name: str, steps: list[str]) -> Panel:
    """Render the how-to-play panel for a game."""
    body = Text()
    for i, step in enumerate(steps, start=1):
        body.append(f" {i}. ", style=f"bold {config.COLORS['info']}")
        body.append(f"{step}\n", style="white")
    body.append(
        "\n [P] Play   [R] Replay demo   [D] Don't show again",
        style=config.COLORS["gold"],
    )
    return Panel(
        body,
        title=f"HOW TO PLAY: {game_name}",
        title_align="left",
        style=config.COLORS["info"],
    )
