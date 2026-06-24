"""Interactive Terminal Trading screen.

Turn-based: each tick the player buys/sells/holds, then prices advance one step.
A short render delay fakes a live-market feel; all decision logic lives in
gambs/earn/trading.py.
"""

from __future__ import annotations

import random
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gambs import config
from gambs.earn import trading
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import tutorial_gate, result_banner, pause
from gambs.vip import activity_xp, add_xp

TRADING_TUTORIAL = [
    "Four stocks — LUCK, CHIP, DICE, RISK — drift every tick.",
    "Buy low, sell high using your virtual session capital.",
    "You get a fixed number of ticks, then the market closes and settles.",
    "This is an EARN job: profit is paid out, losses never touch your real cash.",
]


def _market_table(prices: dict[str, float], prev: dict[str, float]) -> Table:
    table = Table(title="MARKET", title_style=config.COLORS["earn"])
    table.add_column("Stock")
    table.add_column("Price", justify="right")
    table.add_column("Move", justify="right")
    for stock, price in prices.items():
        delta = price - prev.get(stock, price)
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "·")
        color = (
            config.COLORS["success"]
            if delta > 0
            else (config.COLORS["danger"] if delta < 0 else "dim")
        )
        table.add_row(
            stock,
            f"${price:,.2f}",
            Text(f"{arrow} {delta:+.2f}", style=color),
        )
    return table


def _portfolio_text(p: trading.Portfolio, prices: dict[str, float]) -> Text:
    lines = Text()
    lines.append(f"  Cash: ${p.cash:,.2f}\n", style=config.COLORS["gold"])
    for stock, shares in p.holdings.items():
        if shares:
            lines.append(
                f"  {stock}: {shares} sh  (${shares * prices[stock]:,.2f})\n",
                style=config.COLORS["info"],
            )
    lines.append(
        f"  Net worth: ${trading.portfolio_value(p, prices):,.2f}",
        style=config.COLORS["earn"],
    )
    return lines


def _prompt_trade(console: Console, p: trading.Portfolio, prices: dict[str, float]) -> None:
    """One action: B/S to buy/sell, anything else to hold."""
    raw = input("  [B]uy / [S]ell / Enter to hold: ").strip().lower()
    if raw not in ("b", "s"):
        return
    stock = input(f"  Stock {config.TRADING_STOCKS}: ").strip().upper()
    if stock not in prices:
        console.print(Text("  Unknown stock.", style=config.COLORS["danger"]))
        return
    try:
        qty = int(input("  Shares: ").strip())
    except ValueError:
        console.print(Text("  Invalid quantity.", style=config.COLORS["danger"]))
        return
    if raw == "b":
        if not trading.buy(p, stock, qty, prices):
            console.print(Text("  Trade rejected (not enough cash).", style=config.COLORS["danger"]))
    else:
        if not trading.sell(p, stock, qty, prices):
            console.print(Text("  Trade rejected (not enough shares).", style=config.COLORS["danger"]))


def run_trading(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "trading", "TERMINAL TRADING", TRADING_TUTORIAL)
    rng = random.Random()
    volatility = trading.volatility_for_balance(save.balance)
    prices = trading.initial_prices()
    prev = dict(prices)
    portfolio = trading.new_portfolio(config.TRADING_CAPITAL)

    for tick in range(1, config.TRADING_TICKS + 1):
        console.clear()
        console.print(balance_bar_text(save))
        console.print(
            Panel(
                Text(
                    f"Tick {tick}/{config.TRADING_TICKS}  ·  "
                    f"Session capital ${config.TRADING_CAPITAL:,.0f}",
                    style=config.COLORS["earn"],
                ),
                title="📈  TERMINAL TRADING",
                title_align="left",
                style=config.COLORS["earn"],
            )
        )
        console.print(_market_table(prices, prev))
        console.print(_portfolio_text(portfolio, prices))
        _prompt_trade(console, portfolio, prices)
        prev = dict(prices)
        prices = trading.step_prices(rng, prices, volatility)
        time.sleep(0.15)  # fake live-market tick feel

    reward = trading.settle(portfolio, prices, config.TRADING_CAPITAL)
    save.balance = round(save.balance + reward, 2)
    save.stats.total_earned = round(save.stats.total_earned + reward, 2)
    if reward > 0:
        add_xp(save, activity_xp(reward))

    console.print(
        Text(
            f"  Final net worth ${trading.portfolio_value(portfolio, prices):,.2f}  "
            f"from ${config.TRADING_CAPITAL:,.0f} capital",
            style=config.COLORS["info"],
        )
    )
    result_banner(console, reward > 0, f"MARKET CLOSED  +${reward:,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
