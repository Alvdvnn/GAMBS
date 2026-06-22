"""Slots: 3 weighted reels with a fixed paytable. Pure logic, RNG injected."""

from __future__ import annotations

import random

SYMBOLS = ["7", "BAR", "♦", "♣", "♥", "♠"]
_WEIGHTS = [1, 2, 4, 5, 6, 6]  # "7" is the rarest


def spin(rng: random.Random) -> tuple[str, str, str]:
    """Spin three reels and return the visible symbols."""
    a, b, c = rng.choices(SYMBOLS, weights=_WEIGHTS, k=3)
    return a, b, c


def settle(reels: tuple[str, str, str], bet: float) -> float:
    """Net profit for a spin per the paytable."""
    a, b, c = reels
    if a == b == c:
        if a == "7":
            return round(bet * 50, 2)
        if a == "BAR":
            return round(bet * 20, 2)
        return round(bet * 5, 2)
    if [a, b, c].count("7") == 2:
        return round(bet * 2, 2)
    return round(-bet, 2)
