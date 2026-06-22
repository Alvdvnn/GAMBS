"""Coin Flip: even-money 50/50 call. Pure logic, RNG injected."""

from __future__ import annotations

import random

HEADS = "H"
TAILS = "T"


def flip(rng: random.Random) -> str:
    """Return 'H' or 'T'."""
    return rng.choice([HEADS, TAILS])


def settle(call: str, result: str, bet: float) -> float:
    """Net result: even money. Win -> +bet, loss -> -bet."""
    return round(bet if call == result else -bet, 2)
