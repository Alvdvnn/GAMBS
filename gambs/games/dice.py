"""Dice: two dice, bet LOW/HIGH/SEVEN. LOW/HIGH push on 7. Pure logic."""

from __future__ import annotations

import random

BET_LOW = "low"
BET_HIGH = "high"
BET_SEVEN = "seven"


def roll(rng: random.Random) -> tuple[int, int]:
    """Roll two six-sided dice."""
    return rng.randint(1, 6), rng.randint(1, 6)


def settle(bet_type: str, dice: tuple[int, int], bet: float) -> float:
    """Net result for a dice bet.

    LOW wins on total < 7, HIGH on total > 7; both push (0.0) on a 7.
    SEVEN pays 4:1 on exactly 7, otherwise loses.
    """
    total = dice[0] + dice[1]
    if bet_type == BET_SEVEN:
        return round(bet * 4 if total == 7 else -bet, 2)
    if bet_type == BET_LOW:
        if total == 7:
            return 0.0
        return round(bet if total < 7 else -bet, 2)
    if bet_type == BET_HIGH:
        if total == 7:
            return 0.0
        return round(bet if total > 7 else -bet, 2)
    raise ValueError(f"unknown bet type: {bet_type}")
