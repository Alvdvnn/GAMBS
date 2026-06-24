"""Pure item-effect helpers. RNG is injected; no save mutation here.

Screens consume the item charge and call these to adjust a round's outcome.
Effects are capped and never guarantee a win, honoring the shop fairness rules.
"""

from __future__ import annotations

import random

from gambs import config


def lucky_rescue(net: float, bet: float, rng: random.Random, buff: float) -> float:
    """Lucky Charm: with probability `buff`, turn a loss into an even-money win.

    Wins and pushes are returned unchanged.
    """
    if net < 0 and rng.random() < buff:
        return round(bet, 2)
    return net


def insurance_refund(bet: float) -> float:
    """Insurance Card: the amount refunded when a Crash round busts."""
    return round(bet * config.INSURANCE_REFUND_RATE, 2)
