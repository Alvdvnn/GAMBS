"""Terminal Trading (Earn Mode): trade 4 virtual stocks over a fixed number of
turn-based ticks.

Pure logic only — RNG is injected and prices advance one step per player action,
so the whole engine is deterministic and unit-testable. This is an *earn* game:
the session uses virtual capital that is NOT drawn from the real balance, and the
payout floor is $0, so the player can never lose real money (spec: downside capped
at session buy-in, unlimited upside).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from gambs import config


def volatility_for_balance(balance: float) -> float:
    """Map the player's balance to a per-tick volatility fraction. Richer = wilder.

    Stands in for VIP-level scaling until the VIP system exists.
    """
    if balance < 1000:
        return 0.05
    if balance < 5000:
        return 0.08
    if balance < 20000:
        return 0.12
    return 0.16


def initial_prices() -> dict[str, float]:
    """Every stock starts at the configured start price."""
    return {stock: config.TRADING_START_PRICE for stock in config.TRADING_STOCKS}


def step_price(rng: random.Random, price: float, volatility: float) -> float:
    """Advance one price by a random-walk step, floored at the min price."""
    factor = 1.0 + rng.uniform(-volatility, volatility)
    return round(max(config.TRADING_MIN_PRICE, price * factor), 2)


def step_prices(
    rng: random.Random, prices: dict[str, float], volatility: float
) -> dict[str, float]:
    """Return a new price map with every stock advanced one step."""
    return {stock: step_price(rng, price, volatility) for stock, price in prices.items()}
