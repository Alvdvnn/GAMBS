"""Roulette: European single-zero wheel. Pure logic, RNG injected."""

from __future__ import annotations

import random

BET_STRAIGHT = "straight"
BET_RED = "red"
BET_BLACK = "black"
BET_ODD = "odd"
BET_EVEN = "even"
BET_LOW = "low"    # 1-18
BET_HIGH = "high"  # 19-36

_RED_NUMBERS = {
    1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36
}


def spin(rng: random.Random) -> int:
    """Spin the wheel; returns 0-36."""
    return rng.randint(0, 36)


def color(n: int) -> str:
    """Return 'green' (0), 'red', or 'black' for a pocket."""
    if n == 0:
        return "green"
    return "red" if n in _RED_NUMBERS else "black"


def settle(bet_type: str, bet_value: int | None, result: int, amount: float) -> float:
    """Net result for a roulette bet.

    `bet_value` is the chosen number for STRAIGHT bets, otherwise ignored
    (pass None). Even-money outside bets all lose on 0.
    """
    if bet_type == BET_STRAIGHT:
        return round(amount * 35 if result == bet_value else -amount, 2)
    if result == 0:
        return round(-amount, 2)
    if bet_type == BET_RED:
        won = color(result) == "red"
    elif bet_type == BET_BLACK:
        won = color(result) == "black"
    elif bet_type == BET_ODD:
        won = result % 2 == 1
    elif bet_type == BET_EVEN:
        won = result % 2 == 0
    elif bet_type == BET_LOW:
        won = 1 <= result <= 18
    elif bet_type == BET_HIGH:
        won = 19 <= result <= 36
    else:
        raise ValueError(f"unknown bet type: {bet_type}")
    return round(amount if won else -amount, 2)


def settle_all(
    bets: list[tuple[str, int | None, float]], result: int
) -> list[float]:
    """Settle several bets against one spin; returns the net for each bet."""
    return [settle(bet_type, value, result, amount) for bet_type, value, amount in bets]
