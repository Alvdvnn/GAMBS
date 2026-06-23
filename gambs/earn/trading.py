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


@dataclass
class Portfolio:
    cash: float
    holdings: dict[str, int]


def new_portfolio(capital: float) -> Portfolio:
    """A fresh portfolio holding `capital` cash and zero shares of each stock."""
    return Portfolio(cash=capital, holdings={s: 0 for s in config.TRADING_STOCKS})


def buy(p: Portfolio, stock: str, qty: int, prices: dict[str, float]) -> bool:
    """Buy `qty` shares if affordable. Returns True on success, False otherwise."""
    if qty <= 0:
        return False
    cost = qty * prices[stock]
    if cost > p.cash:
        return False
    p.cash = round(p.cash - cost, 2)
    p.holdings[stock] += qty
    return True


def sell(p: Portfolio, stock: str, qty: int, prices: dict[str, float]) -> bool:
    """Sell `qty` shares if held. Returns True on success, False otherwise."""
    if qty <= 0 or p.holdings.get(stock, 0) < qty:
        return False
    p.cash = round(p.cash + qty * prices[stock], 2)
    p.holdings[stock] -= qty
    return True


def portfolio_value(p: Portfolio, prices: dict[str, float]) -> float:
    """Cash plus the marked-to-market value of all holdings."""
    held = sum(shares * prices.get(stock, 0.0) for stock, shares in p.holdings.items())
    return round(p.cash + held, 2)


def settle(p: Portfolio, prices: dict[str, float], starting_capital: float) -> float:
    """Session payout: profit above starting capital, floored at $0 (never lose)."""
    return round(max(0.0, portfolio_value(p, prices) - starting_capital), 2)
