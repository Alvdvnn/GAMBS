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
