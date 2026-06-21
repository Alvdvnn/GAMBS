"""Persistent player state: model, defaults, and JSON serialization."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

from gambs import config


@dataclass
class VipState:
    level: int = 1
    xp: int = 0
    prestige: int = 0
    luck_buff: float = 0.0


@dataclass
class Stats:
    total_wagered: float = 0.0
    total_won: float = 0.0
    games_played: int = 0
    best_crash_multiplier: float = 0.0
    bounty_jobs_completed: int = 0


@dataclass
class SaveData:
    balance: float = config.STARTING_BALANCE
    tutorial_seen: list[str] = field(default_factory=list)
    vip: VipState = field(default_factory=VipState)
    inventory: list[dict] = field(default_factory=list)
    cosmetics: dict = field(
        default_factory=lambda: {"owned": ["default"], "active": "default"}
    )
    stats: Stats = field(default_factory=Stats)
    created_at: str = ""
    last_played: str = ""


def default_save() -> SaveData:
    """Return a fresh save for a brand-new player."""
    today = date.today().isoformat()
    return SaveData(created_at=today, last_played=today)


def to_dict(save: SaveData) -> dict:
    """Serialize SaveData (with nested dataclasses) to a plain dict."""
    return asdict(save)


def from_dict(data: dict) -> SaveData:
    """Reconstruct SaveData from a plain dict, rebuilding nested dataclasses."""
    data = dict(data)  # shallow copy so we don't mutate caller's dict
    vip = VipState(**data.get("vip", {}))
    stats = Stats(**data.get("stats", {}))
    data.pop("vip", None)
    data.pop("stats", None)
    return SaveData(vip=vip, stats=stats, **data)


def write_save(path: Path, save: SaveData) -> None:
    """Persist a save to disk as pretty JSON, creating parent dirs."""
    save.last_played = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_dict(save), indent=2), encoding="utf-8")


def load_save(path: Path) -> SaveData:
    """Load a save from disk; if absent, create and persist a default."""
    if not path.exists():
        save = default_save()
        write_save(path, save)
        return save
    data = json.loads(path.read_text(encoding="utf-8"))
    return from_dict(data)
