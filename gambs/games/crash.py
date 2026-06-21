"""Pure crash-game math: crash point, multiplier curve, payout. No I/O."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from gambs import config


def generate_crash_point(
    rng: random.Random, house_edge: float = config.HOUSE_EDGE
) -> float:
    """Sample the multiplier at which the rocket crashes.

    Uses the standard crash distribution: crash = (1 - edge) / (1 - r) for a
    uniform r in [0, 1). Floored to 2 decimals, clamped to a minimum of 1.00.
    """
    r = rng.random()
    if r >= 1.0:  # defensive; random() is [0, 1)
        r = 0.0
    raw = (1.0 - house_edge) / (1.0 - r)
    return max(1.0, math.floor(raw * 100) / 100)


def multiplier_at(elapsed: float, growth: float = config.CRASH_GROWTH_RATE) -> float:
    """Current multiplier after `elapsed` seconds: e^(growth * elapsed)."""
    return round(math.exp(growth * elapsed), 2)


def payout(bet: float, cashout_multiplier: float) -> float:
    """Winnings returned when cashing out at a given multiplier."""
    return math.floor(bet * cashout_multiplier * 100 + 0.5) / 100


@dataclass
class CrashResult:
    won: bool
    cashout_multiplier: float | None
    winnings: float
    net: float


def resolve_round(
    bet: float, crash_point: float, cashout_multiplier: float | None
) -> CrashResult:
    """Decide the outcome of a crash round.

    The player wins only if they cashed out strictly before the crash point.
    """
    if cashout_multiplier is not None and cashout_multiplier < crash_point:
        winnings = payout(bet, cashout_multiplier)
        return CrashResult(
            won=True,
            cashout_multiplier=cashout_multiplier,
            winnings=winnings,
            net=round(winnings - bet, 2),
        )
    return CrashResult(
        won=False, cashout_multiplier=None, winnings=0.0, net=round(-bet, 2)
    )
