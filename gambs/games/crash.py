"""Pure crash-game math: crash point, multiplier curve, payout. No I/O."""

from __future__ import annotations

import math
import random

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
