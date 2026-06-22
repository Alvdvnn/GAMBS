"""Slots: 3 weighted reels with a fixed paytable. Pure logic, RNG injected."""

from __future__ import annotations

import random

SYMBOLS = ["7", "BAR", "♦", "♣", "♥", "♠"]
# Weights tuned for a ~6% house edge (test_house_edge_in_target_band locks the
# band). "7" is the most common symbol on purpose: the two-7s payout (2x) is the
# main source of frequent small wins, so making 7 rare pushes the edge to ~70%.
# BAR stays slightly rarer than the suits since its triple pays 20x.
_WEIGHTS = [9, 6, 7, 7, 7, 7]


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
