# Earn Mode (Rest) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish Earn Mode by adding an earn-game selector plus two new earn games — Terminal Trading (turn-based market) and Bounty Jobs (data-driven branching missions) — wired into the [E] EARN route.

**Architecture:** Mirror the existing gamble side. A new earn registry + earn selector replace the hardwired Typing Heist route. Each new game keeps pure, RNG-injected logic in its own module with unit tests, and interactive rendering in a separate `*_screen.py` (manual-smoke only). Trading is turn-based (one price step per player action) so the logic stays pure and testable — the screen fakes real-time feel. Bounty Jobs is a scripted branch tree authored in `data/bounty_jobs.json`; the engine traverses nodes and only consults the injected RNG at "risk" nodes.

**Tech Stack:** Python 3.10+, rich, readchar, pytest. Reuse `gambs/ui/prompts.py`, `gambs/ui/components.py:balance_bar_text`, the registry/selector pattern from `gambs/games/registry.py` + `gambs/ui/game_select.py`.

**Conventions (must keep):**
- Commit messages must NOT contain any `Co-Authored-By` trailer.
- Earn games only ever credit the player: balance and `save.stats.total_earned` go up, never down.
- Run tests with: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
- Run a single test with: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_x.py::test_name" -v`

---

## File Structure

**Create:**
- `gambs/earn/registry.py` — `EarnEntry` dataclass + `all_earn_games()` (lazy imports).
- `gambs/ui/earn_select.py` — earn selector loop (`earn_menu_panel`, `resolve_earn_key`, `run_earn_select`).
- `gambs/earn/trading.py` — pure trading logic (price walk, portfolio, settle).
- `gambs/earn/trading_screen.py` — interactive Terminal Trading screen.
- `gambs/earn/bounty.py` — pure bounty engine (load jobs, traverse nodes, reward/cooldown helpers).
- `gambs/earn/bounty_screen.py` — interactive Bounty Jobs screen.
- `gambs/data/bounty_jobs.json` — job content (3 tiers).
- `tests/test_earn_select.py`, `tests/test_trading.py`, `tests/test_bounty.py`.

**Modify:**
- `gambs/save.py` — add `Stats.bounty_jobs_attempted` and `SaveData.bounty_cooldown_until`.
- `gambs/config.py` — trading + bounty constants and paths.
- `gambs/main.py` — route `earn` to `run_earn_select` instead of `run_typing_heist`.
- `tests/test_save.py` — assert new fields default and round-trip.

---

## Task 1: Save schema additions

**Files:**
- Modify: `gambs/save.py:22-28` (Stats), `gambs/save.py:31-42` (SaveData)
- Test: `tests/test_save.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_save.py`:

```python
def test_stats_has_bounty_jobs_attempted_default():
    from gambs.save import Stats
    assert Stats().bounty_jobs_attempted == 0


def test_savedata_has_bounty_cooldown_until_default():
    from gambs.save import SaveData
    assert SaveData().bounty_cooldown_until == 0.0


def test_from_dict_defaults_new_fields_for_old_saves():
    from gambs.save import from_dict
    save = from_dict({"balance": 500.0, "stats": {"total_won": 10.0}})
    assert save.stats.bounty_jobs_attempted == 0
    assert save.bounty_cooldown_until == 0.0


def test_roundtrip_preserves_new_fields():
    from gambs.save import SaveData, to_dict, from_dict
    save = SaveData(bounty_cooldown_until=123.0)
    save.stats.bounty_jobs_attempted = 4
    restored = from_dict(to_dict(save))
    assert restored.bounty_cooldown_until == 123.0
    assert restored.stats.bounty_jobs_attempted == 4
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_save.py" -v`
Expected: FAIL — `TypeError: Stats.__init__() got an unexpected keyword argument` / `AttributeError`.

- [ ] **Step 3: Add the fields**

In `gambs/save.py`, add to the `Stats` dataclass (after `total_earned`):

```python
    bounty_jobs_attempted: int = 0
```

Add to the `SaveData` dataclass (after `last_played`):

```python
    bounty_cooldown_until: float = 0.0
```

(No change needed to `from_dict`: `Stats(**...)` and `SaveData(**data)` pick up defaults for missing keys.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_save.py" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add gambs/save.py tests/test_save.py
git commit -m "feat: add bounty attempt count and cooldown to save model"
```

---

## Task 2: Earn registry

**Files:**
- Create: `gambs/earn/registry.py`
- Test: `tests/test_earn_select.py` (registry portion)

- [ ] **Step 1: Write the failing test**

Create `tests/test_earn_select.py`:

```python
import io

from rich.console import Console

from gambs.earn.registry import all_earn_games, EarnEntry


def test_registry_lists_typing_heist_first():
    games = all_earn_games()
    assert isinstance(games[0], EarnEntry)
    assert games[0].id == "typing_heist"


def test_registry_entries_are_callable():
    for entry in all_earn_games():
        assert callable(entry.run)
        assert entry.label
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_earn_select.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.earn.registry'`.

- [ ] **Step 3: Create the registry**

Create `gambs/earn/registry.py`:

```python
"""The single registry of Earn Mode mini-games.

Screen modules are imported lazily inside `all_earn_games()` so importing the
registry never triggers heavy/interactive imports at module load. Mirrors
gambs/games/registry.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rich.console import Console

from gambs.save import SaveData

RunFn = Callable[[Console, SaveData], None]


@dataclass
class EarnEntry:
    id: str
    label: str
    run: RunFn


def all_earn_games() -> list[EarnEntry]:
    """Return every registered earn game, in display order."""
    from gambs.earn.typing_heist_screen import run_typing_heist

    return [
        EarnEntry("typing_heist", "⌨  Typing Heist", run_typing_heist),
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_earn_select.py" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add gambs/earn/registry.py tests/test_earn_select.py
git commit -m "feat: add earn game registry"
```

---

## Task 3: Earn selector UI

**Files:**
- Create: `gambs/ui/earn_select.py`
- Test: `tests/test_earn_select.py` (selector portion)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_earn_select.py`:

```python
from gambs.ui.earn_select import resolve_earn_key, earn_menu_panel


def test_resolve_earn_key_maps_digits_to_entries():
    games = all_earn_games()
    assert resolve_earn_key("1", games) is games[0]


def test_resolve_earn_key_out_of_range_is_none():
    games = all_earn_games()
    assert resolve_earn_key("0", games) is None
    assert resolve_earn_key("9", games) is None
    assert resolve_earn_key("x", games) is None


def test_earn_menu_panel_lists_all_labels():
    games = all_earn_games()
    console = Console(width=80, file=io.StringIO())
    with console.capture() as cap:
        console.print(earn_menu_panel(games))
    out = cap.get()
    for entry in games:
        assert entry.label in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_earn_select.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.ui.earn_select'`.

- [ ] **Step 3: Create the selector**

Create `gambs/ui/earn_select.py`:

```python
"""Earn game selector: render the list and dispatch the chosen mini-game.

Mirrors gambs/ui/game_select.py but uses the earn registry and the magenta
earn theme.
"""

from __future__ import annotations

import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.earn.registry import EarnEntry, all_earn_games
from gambs.save import SaveData, write_save
from gambs.ui.components import balance_bar_text


def earn_menu_panel(games: list[EarnEntry]) -> Panel:
    """Render the numbered list of earn games."""
    body = Text()
    for i, entry in enumerate(games, start=1):
        body.append(f" [{i}] ", style=f"bold {config.COLORS['gold']}")
        body.append(f"{entry.label}\n", style=f"bold {config.COLORS['earn']}")
    body.append("\n [ESC] Back to main menu", style="dim")
    return Panel(
        body,
        title="EARN — choose a job",
        title_align="left",
        style=config.COLORS["earn"],
    )


def resolve_earn_key(key: str, games: list[EarnEntry]) -> EarnEntry | None:
    """Map a digit key to an earn entry, or None if out of range/non-digit."""
    if not key or not key.isdigit():
        return None
    idx = int(key) - 1
    if 0 <= idx < len(games):
        return games[idx]
    return None


def run_earn_select(console: Console, save: SaveData) -> None:
    """Loop the earn selector until the player presses ESC/Q to go back."""
    games = all_earn_games()
    while True:
        console.clear()
        console.print(balance_bar_text(save))
        console.print(earn_menu_panel(games))
        console.print("Select job: ", end="")
        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        entry = resolve_earn_key(key, games)
        if entry is not None:
            entry.run(console, save)
            write_save(config.SAVE_PATH, save)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_earn_select.py" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add gambs/ui/earn_select.py tests/test_earn_select.py
git commit -m "feat: add earn game selector"
```

---

## Task 4: Wire EARN route to the selector

**Files:**
- Modify: `gambs/main.py:15` (import), `gambs/main.py:75-77` (route)

- [ ] **Step 1: Swap the import**

In `gambs/main.py`, replace:

```python
from gambs.earn.typing_heist_screen import run_typing_heist
```

with:

```python
from gambs.ui.earn_select import run_earn_select
```

- [ ] **Step 2: Swap the route body**

In `gambs/main.py`, replace:

```python
        elif route == "earn":
            run_typing_heist(console, save)
            write_save(config.SAVE_PATH, save)
```

with:

```python
        elif route == "earn":
            run_earn_select(console, save)
            write_save(config.SAVE_PATH, save)
```

- [ ] **Step 3: Verify the package still imports**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "import gambs.main"`
Expected: no output, exit code 0 (no import errors).

- [ ] **Step 4: Run the full suite**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: PASS (all previously-passing tests plus the new ones).

- [ ] **Step 5: Manual smoke (optional but recommended)**

Run: `cd D:\gambs; & "D:/gambs/.venv/Scripts/python.exe" -m gambs.main`
Press `E`. Confirm the earn selector lists "⌨  Typing Heist" and `[1]` launches it, `ESC` returns to main menu.

- [ ] **Step 6: Commit**

```bash
git add gambs/main.py
git commit -m "feat: route EARN to earn selector"
```

---

## Task 5: Terminal Trading — config + price walk

**Files:**
- Modify: `gambs/config.py` (append trading constants)
- Create: `gambs/earn/trading.py`
- Test: `tests/test_trading.py`

- [ ] **Step 1: Add config constants**

Append to `gambs/config.py` (after the Crash tunables block):

```python
# --- Terminal Trading tunables ---
TRADING_STOCKS: list[str] = ["LUCK", "CHIP", "DICE", "RISK"]
TRADING_START_PRICE: float = 100.0
TRADING_MIN_PRICE: float = 1.0
TRADING_TICKS: int = 20          # player actions per session
TRADING_CAPITAL: float = 1000.0  # virtual session chips, NOT real balance
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_trading.py`:

```python
import random

from gambs import config
from gambs.earn.trading import (
    volatility_for_balance,
    initial_prices,
    step_price,
    step_prices,
)


def test_volatility_rises_with_balance():
    assert volatility_for_balance(500) < volatility_for_balance(3000)
    assert volatility_for_balance(3000) < volatility_for_balance(10000)
    assert volatility_for_balance(10000) < volatility_for_balance(50000)


def test_initial_prices_cover_all_stocks_at_start_price():
    prices = initial_prices()
    assert set(prices) == set(config.TRADING_STOCKS)
    assert all(p == config.TRADING_START_PRICE for p in prices.values())


def test_step_price_is_deterministic_for_a_seed():
    a = step_price(random.Random(7), 100.0, 0.1)
    b = step_price(random.Random(7), 100.0, 0.1)
    assert a == b


def test_step_price_never_below_min():
    rng = random.Random(1)
    price = 100.0
    for _ in range(500):
        price = step_price(rng, price, 0.5)
        assert price >= config.TRADING_MIN_PRICE


def test_step_prices_steps_every_stock():
    prices = initial_prices()
    stepped = step_prices(random.Random(0), prices, 0.1)
    assert set(stepped) == set(prices)
    assert stepped is not prices  # returns a new dict
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_trading.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.earn.trading'`.

- [ ] **Step 4: Create the price-walk logic**

Create `gambs/earn/trading.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_trading.py" -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add gambs/config.py gambs/earn/trading.py tests/test_trading.py
git commit -m "feat: add terminal trading price-walk logic"
```

---

## Task 6: Terminal Trading — portfolio + settle

**Files:**
- Modify: `gambs/earn/trading.py` (add Portfolio + trade functions)
- Test: `tests/test_trading.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_trading.py`:

```python
from gambs.earn.trading import (
    Portfolio,
    new_portfolio,
    buy,
    sell,
    portfolio_value,
    settle,
)


def test_new_portfolio_holds_capital_and_zero_shares():
    p = new_portfolio(1000.0)
    assert p.cash == 1000.0
    assert all(shares == 0 for shares in p.holdings.values())
    assert set(p.holdings) == set(config.TRADING_STOCKS)


def test_buy_deducts_cash_and_adds_shares():
    p = new_portfolio(1000.0)
    ok = buy(p, "LUCK", 3, {"LUCK": 100.0})
    assert ok is True
    assert p.cash == 700.0
    assert p.holdings["LUCK"] == 3


def test_buy_rejected_when_insufficient_cash():
    p = new_portfolio(100.0)
    ok = buy(p, "LUCK", 5, {"LUCK": 100.0})
    assert ok is False
    assert p.cash == 100.0
    assert p.holdings["LUCK"] == 0


def test_sell_adds_cash_and_removes_shares():
    p = new_portfolio(1000.0)
    buy(p, "LUCK", 3, {"LUCK": 100.0})
    ok = sell(p, "LUCK", 2, {"LUCK": 120.0})
    assert ok is True
    assert p.holdings["LUCK"] == 1
    assert p.cash == 700.0 + 240.0


def test_sell_rejected_when_not_enough_shares():
    p = new_portfolio(1000.0)
    ok = sell(p, "LUCK", 1, {"LUCK": 100.0})
    assert ok is False


def test_portfolio_value_is_cash_plus_holdings():
    p = new_portfolio(1000.0)
    buy(p, "LUCK", 2, {"LUCK": 100.0})  # cash 800, 2 shares
    assert portfolio_value(p, {"LUCK": 150.0}) == 800.0 + 300.0


def test_settle_returns_profit_above_capital():
    p = new_portfolio(1000.0)
    buy(p, "LUCK", 5, {"LUCK": 100.0})  # cash 500, 5 shares
    # 5 shares now worth 200 each = 1000, + 500 cash = 1500 value, capital 1000
    assert settle(p, {"LUCK": 200.0}, 1000.0) == 500.0


def test_settle_floors_at_zero_on_a_loss():
    p = new_portfolio(1000.0)
    buy(p, "LUCK", 5, {"LUCK": 100.0})  # cash 500, 5 shares
    # 5 shares now worth 10 each = 50, + 500 cash = 550 value < 1000 capital
    assert settle(p, {"LUCK": 10.0}, 1000.0) == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_trading.py" -v`
Expected: FAIL — `ImportError: cannot import name 'Portfolio'`.

- [ ] **Step 3: Add the portfolio logic**

Append to `gambs/earn/trading.py`:

```python
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
    held = sum(shares * prices[stock] for stock, shares in p.holdings.items())
    return round(p.cash + held, 2)


def settle(p: Portfolio, prices: dict[str, float], starting_capital: float) -> float:
    """Session payout: profit above starting capital, floored at $0 (never lose)."""
    return round(max(0.0, portfolio_value(p, prices) - starting_capital), 2)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_trading.py" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add gambs/earn/trading.py tests/test_trading.py
git commit -m "feat: add terminal trading portfolio and settle logic"
```

---

## Task 7: Terminal Trading — interactive screen

**Files:**
- Create: `gambs/earn/trading_screen.py`

Manual-smoke only (no unit tests for the screen, per the rendering convention).

- [ ] **Step 1: Create the screen**

Create `gambs/earn/trading_screen.py`:

```python
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
```

- [ ] **Step 2: Verify it imports**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "import gambs.earn.trading_screen"`
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add gambs/earn/trading_screen.py
git commit -m "feat: add terminal trading screen"
```

---

## Task 8: Register Terminal Trading in the earn selector

**Files:**
- Modify: `gambs/earn/registry.py`
- Test: `tests/test_earn_select.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_earn_select.py`:

```python
def test_registry_includes_trading():
    ids = [g.id for g in all_earn_games()]
    assert "trading" in ids
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_earn_select.py::test_registry_includes_trading" -v`
Expected: FAIL — `assert 'trading' in ['typing_heist']`.

- [ ] **Step 3: Add the entry**

In `gambs/earn/registry.py`, update `all_earn_games()`:

```python
def all_earn_games() -> list[EarnEntry]:
    """Return every registered earn game, in display order."""
    from gambs.earn.typing_heist_screen import run_typing_heist
    from gambs.earn.trading_screen import run_trading

    return [
        EarnEntry("typing_heist", "⌨  Typing Heist", run_typing_heist),
        EarnEntry("trading", "📈  Terminal Trading", run_trading),
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_earn_select.py" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add gambs/earn/registry.py tests/test_earn_select.py
git commit -m "feat: register terminal trading in earn selector"
```

---

## Task 9: Bounty Jobs — content file + config path

**Files:**
- Modify: `gambs/config.py` (append bounty path + constants)
- Create: `gambs/data/bounty_jobs.json`

- [ ] **Step 1: Add config**

Append to `gambs/config.py` (after the Trading tunables block):

```python
# --- Bounty Jobs tunables ---
BOUNTY_JOBS_PATH: Path = DATA_DIR / "bounty_jobs.json"
BOUNTY_COOLDOWN_SECONDS: float = 120.0
```

- [ ] **Step 2: Create the job content**

Create `gambs/data/bounty_jobs.json`. Each tier maps to a list of jobs. A job has
a `start` node id and a `nodes` map. A node is one of: a **choice node**
(`choices` list, each `{label, next}`), a **risk node** (`risk` with
`success_chance`, `on_success`, `on_fail`), or a **terminal node** (`terminal`
with either `{payout: N}` for success or `{fail: true}`).

```json
{
  "LOW": [
    {
      "id": "corner_store",
      "title": "Corner Store Snatch",
      "start": "n1",
      "nodes": {
        "n1": {
          "text": "A sleepy corner store, register full. How do you get in?",
          "choices": [
            { "label": "Walk in casual", "next": "n2" },
            { "label": "Force the back door", "next": "risk_door" }
          ]
        },
        "risk_door": {
          "text": "The back door is alarmed. Try to disable it?",
          "risk": { "success_chance": 0.6, "on_success": "n2", "on_fail": "busted" }
        },
        "n2": {
          "text": "You're at the register. Grab and go, or crack the safe too?",
          "choices": [
            { "label": "Grab the till", "next": "win_small" },
            { "label": "Crack the safe", "next": "risk_safe" }
          ]
        },
        "risk_safe": {
          "text": "The safe is old but stubborn.",
          "risk": { "success_chance": 0.5, "on_success": "win_big", "on_fail": "busted" }
        },
        "win_small": { "text": "Clean getaway with the till.", "terminal": { "payout": 150 } },
        "win_big": { "text": "Till and safe — tidy haul.", "terminal": { "payout": 300 } },
        "busted": { "text": "Sirens. You bolt empty-handed.", "terminal": { "fail": true } }
      }
    }
  ],
  "MEDIUM": [
    {
      "id": "armored_van",
      "title": "Armored Van Tail",
      "start": "n1",
      "nodes": {
        "n1": {
          "text": "An armored van runs a fixed route. Where do you hit it?",
          "choices": [
            { "label": "Quiet underpass", "next": "risk_block" },
            { "label": "Busy intersection", "next": "n2" }
          ]
        },
        "risk_block": {
          "text": "Block it in the underpass — risky but isolated.",
          "risk": { "success_chance": 0.55, "on_success": "n3", "on_fail": "busted" }
        },
        "n2": {
          "text": "Too many eyes. Abort or improvise a distraction?",
          "choices": [
            { "label": "Abort to the underpass", "next": "risk_block" },
            { "label": "Pull the fire alarm nearby", "next": "n3" }
          ]
        },
        "n3": {
          "text": "Doors are open. Take one bag or all three?",
          "choices": [
            { "label": "One bag, leave clean", "next": "win_small" },
            { "label": "All three, push your luck", "next": "risk_greed" }
          ]
        },
        "risk_greed": {
          "text": "Loading all three takes precious seconds.",
          "risk": { "success_chance": 0.45, "on_success": "win_big", "on_fail": "busted" }
        },
        "win_small": { "text": "One bag, gone before backup.", "terminal": { "payout": 500 } },
        "win_big": { "text": "All three bags — legendary run.", "terminal": { "payout": 800 } },
        "busted": { "text": "Reinforcements box you in. Nothing.", "terminal": { "fail": true } }
      }
    }
  ],
  "HIGH": [
    {
      "id": "casino_vault",
      "title": "Casino Vault Job",
      "start": "n1",
      "nodes": {
        "n1": {
          "text": "The GAMBS vault. How do you breach the floor?",
          "choices": [
            { "label": "Bribe a dealer for access", "next": "risk_bribe" },
            { "label": "Pose as maintenance", "next": "n2" }
          ]
        },
        "risk_bribe": {
          "text": "The dealer might rat you out.",
          "risk": { "success_chance": 0.5, "on_success": "n3", "on_fail": "busted" }
        },
        "n2": {
          "text": "Maintenance badge works. Stairs or the freight elevator?",
          "choices": [
            { "label": "Stairs (slow, quiet)", "next": "n3" },
            { "label": "Freight elevator (fast, watched)", "next": "risk_elevator" }
          ]
        },
        "risk_elevator": {
          "text": "Cameras sweep the elevator bay.",
          "risk": { "success_chance": 0.55, "on_success": "n3", "on_fail": "busted" }
        },
        "n3": {
          "text": "At the vault door. Drill it or use the stolen code?",
          "choices": [
            { "label": "Use the stolen code", "next": "risk_code" },
            { "label": "Drill the hinges", "next": "win_small" }
          ]
        },
        "risk_code": {
          "text": "The code may already be rotated.",
          "risk": { "success_chance": 0.5, "on_success": "win_big", "on_fail": "busted" }
        },
        "win_small": { "text": "Drilled in, grabbed a stack, slipped out.", "terminal": { "payout": 1000 } },
        "win_big": { "text": "Full vault. You own the night.", "terminal": { "payout": 2000 } },
        "busted": { "text": "Lockdown. Guards everywhere. You flee broke.", "terminal": { "fail": true } }
      }
    }
  ]
}
```

- [ ] **Step 3: Verify it is valid JSON**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "import json,pathlib; json.loads(pathlib.Path('gambs/data/bounty_jobs.json').read_text(encoding='utf-8')); print('ok')"`
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add gambs/config.py gambs/data/bounty_jobs.json
git commit -m "feat: add bounty jobs content and config"
```

---

## Task 10: Bounty Jobs — traversal engine

**Files:**
- Create: `gambs/earn/bounty.py`
- Test: `tests/test_bounty.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_bounty.py`:

```python
import random

from gambs import config
from gambs.earn.bounty import (
    load_jobs,
    tier_jobs,
    start_node,
    get_node,
    is_terminal,
    is_risk,
    is_choice,
    resolve_choice,
    resolve_risk,
    terminal_result,
)

# A small in-memory job used by traversal tests (no disk dependency).
SAMPLE_JOB = {
    "id": "test_job",
    "title": "Test Job",
    "start": "n1",
    "nodes": {
        "n1": {
            "text": "start",
            "choices": [
                {"label": "safe", "next": "win"},
                {"label": "risky", "next": "r1"},
            ],
        },
        "r1": {
            "text": "roll",
            "risk": {"success_chance": 0.5, "on_success": "win", "on_fail": "lose"},
        },
        "win": {"text": "done", "terminal": {"payout": 200}},
        "lose": {"text": "caught", "terminal": {"fail": True}},
    },
}


def test_load_jobs_reads_all_tiers():
    jobs = load_jobs(config.BOUNTY_JOBS_PATH)
    assert set(jobs) == {"LOW", "MEDIUM", "HIGH"}
    assert tier_jobs(jobs, "LOW")  # non-empty


def test_loaded_jobs_have_required_shape():
    jobs = load_jobs(config.BOUNTY_JOBS_PATH)
    for tier in ("LOW", "MEDIUM", "HIGH"):
        for job in tier_jobs(jobs, tier):
            assert job["start"] in job["nodes"]


def test_start_node_returns_start_id():
    assert start_node(SAMPLE_JOB) == "n1"


def test_node_type_predicates():
    assert is_choice(get_node(SAMPLE_JOB, "n1"))
    assert is_risk(get_node(SAMPLE_JOB, "r1"))
    assert is_terminal(get_node(SAMPLE_JOB, "win"))


def test_resolve_choice_follows_next():
    assert resolve_choice(SAMPLE_JOB, "n1", 0) == "win"
    assert resolve_choice(SAMPLE_JOB, "n1", 1) == "r1"


def test_resolve_risk_success_with_low_roll():
    # success_chance 0.5; force a roll below it
    node = get_node(SAMPLE_JOB, "r1")
    rng = random.Random()
    rng.random = lambda: 0.1  # < 0.5 -> success
    assert resolve_risk(node, rng) == "win"


def test_resolve_risk_failure_with_high_roll():
    node = get_node(SAMPLE_JOB, "r1")
    rng = random.Random()
    rng.random = lambda: 0.9  # >= 0.5 -> fail
    assert resolve_risk(node, rng) == "lose"


def test_terminal_result_success_and_failure():
    assert terminal_result(get_node(SAMPLE_JOB, "win")) == (True, 200.0)
    assert terminal_result(get_node(SAMPLE_JOB, "lose")) == (False, 0.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_bounty.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.earn.bounty'`.

- [ ] **Step 3: Create the engine**

Create `gambs/earn/bounty.py`:

```python
"""Bounty Jobs (Earn Mode): scripted branching missions loaded from JSON.

Pure engine — traversal is deterministic and the injected RNG is consulted only
at "risk" nodes. This is an *earn* game: success pays out and increments stats,
failure costs no money (only a cooldown). The screen layer drives I/O.

Node shapes (in bounty_jobs.json):
- choice node:   {"text": ..., "choices": [{"label": ..., "next": node_id}, ...]}
- risk node:     {"text": ..., "risk": {"success_chance": f, "on_success": id, "on_fail": id}}
- terminal node: {"text": ..., "terminal": {"payout": N}}  OR  {"terminal": {"fail": true}}
"""

from __future__ import annotations

import json
import random
from pathlib import Path


def load_jobs(path: Path) -> dict[str, list[dict]]:
    """Load the tier -> [job, ...] map from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def tier_jobs(jobs: dict[str, list[dict]], tier: str) -> list[dict]:
    """Return the list of jobs for a tier (empty list if the tier is absent)."""
    return jobs.get(tier, [])


def start_node(job: dict) -> str:
    """The id of the job's entry node."""
    return job["start"]


def get_node(job: dict, node_id: str) -> dict:
    """Look up a node by id."""
    return job["nodes"][node_id]


def is_terminal(node: dict) -> bool:
    return "terminal" in node


def is_risk(node: dict) -> bool:
    return "risk" in node


def is_choice(node: dict) -> bool:
    return "choices" in node


def resolve_choice(job: dict, node_id: str, choice_index: int) -> str:
    """Return the next node id for a chosen option at a choice node."""
    return get_node(job, node_id)["choices"][choice_index]["next"]


def resolve_risk(node: dict, rng: random.Random) -> str:
    """Roll the risk gate; return the on_success or on_fail node id."""
    risk = node["risk"]
    if rng.random() < risk["success_chance"]:
        return risk["on_success"]
    return risk["on_fail"]


def terminal_result(node: dict) -> tuple[bool, float]:
    """Interpret a terminal node as (success, payout). Failure pays $0."""
    terminal = node["terminal"]
    if terminal.get("fail"):
        return (False, 0.0)
    return (True, float(terminal["payout"]))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_bounty.py" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add gambs/earn/bounty.py tests/test_bounty.py
git commit -m "feat: add bounty jobs traversal engine"
```

---

## Task 11: Bounty Jobs — reward + cooldown helpers

**Files:**
- Modify: `gambs/earn/bounty.py` (add save-mutating helpers)
- Test: `tests/test_bounty.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bounty.py`:

```python
from gambs.earn.bounty import (
    is_on_cooldown,
    cooldown_remaining,
    apply_success,
    apply_failure,
)
from gambs.save import SaveData


def test_not_on_cooldown_by_default():
    save = SaveData()
    assert is_on_cooldown(save, now=1000.0) is False


def test_on_cooldown_when_now_before_until():
    save = SaveData(bounty_cooldown_until=2000.0)
    assert is_on_cooldown(save, now=1500.0) is True
    assert cooldown_remaining(save, now=1500.0) == 500.0


def test_cooldown_remaining_never_negative():
    save = SaveData(bounty_cooldown_until=1000.0)
    assert cooldown_remaining(save, now=3000.0) == 0.0


def test_apply_success_credits_and_counts():
    save = SaveData(balance=500.0)
    apply_success(save, 300.0)
    assert save.balance == 800.0
    assert save.stats.total_earned == 300.0
    assert save.stats.bounty_jobs_completed == 1
    assert save.stats.bounty_jobs_attempted == 1


def test_apply_failure_sets_cooldown_and_counts_attempt_only():
    save = SaveData(balance=500.0)
    apply_failure(save, now=1000.0)
    assert save.balance == 500.0  # no money lost
    assert save.stats.bounty_jobs_completed == 0
    assert save.stats.bounty_jobs_attempted == 1
    assert save.bounty_cooldown_until == 1000.0 + config.BOUNTY_COOLDOWN_SECONDS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_bounty.py" -v`
Expected: FAIL — `ImportError: cannot import name 'is_on_cooldown'`.

- [ ] **Step 3: Add the helpers**

Append to `gambs/earn/bounty.py` (and add `from gambs import config` and
`from gambs.save import SaveData` to the imports at the top of the file):

```python
def is_on_cooldown(save: SaveData, now: float) -> bool:
    """True if the player is still inside the post-failure cooldown window."""
    return now < save.bounty_cooldown_until


def cooldown_remaining(save: SaveData, now: float) -> float:
    """Seconds left on the cooldown, floored at 0."""
    return max(0.0, save.bounty_cooldown_until - now)


def apply_success(save: SaveData, payout: float) -> None:
    """Credit a winning job: balance + total_earned up, both counters up."""
    save.balance = round(save.balance + payout, 2)
    save.stats.total_earned = round(save.stats.total_earned + payout, 2)
    save.stats.bounty_jobs_completed += 1
    save.stats.bounty_jobs_attempted += 1


def apply_failure(save: SaveData, now: float) -> None:
    """Record a failed job: no money lost, attempt counted, cooldown started."""
    save.stats.bounty_jobs_attempted += 1
    save.bounty_cooldown_until = now + config.BOUNTY_COOLDOWN_SECONDS
```

The top-of-file import block becomes:

```python
from __future__ import annotations

import json
import random
from pathlib import Path

from gambs import config
from gambs.save import SaveData
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_bounty.py" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add gambs/earn/bounty.py tests/test_bounty.py
git commit -m "feat: add bounty reward and cooldown helpers"
```

---

## Task 12: Bounty Jobs — interactive screen

**Files:**
- Create: `gambs/earn/bounty_screen.py`

Manual-smoke only.

- [ ] **Step 1: Create the screen**

Create `gambs/earn/bounty_screen.py`:

```python
"""Interactive Bounty Jobs screen.

Shows a tiered job board, runs the chosen job through the pure engine in
gambs/earn/bounty.py, and applies the reward or cooldown. RNG is real here; the
engine stays pure.
"""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.earn import bounty
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import tutorial_gate, result_banner, pause

BOUNTY_TUTORIAL = [
    "Pick a job from the board — LOW, MEDIUM, or HIGH tier.",
    "Each job is a chain of decisions; some choices roll the dice.",
    "Succeed and you bank the payout. Fail and you wait out a short cooldown.",
    "This is an EARN job: failing never costs you money, only time.",
]

_TIERS = ["LOW", "MEDIUM", "HIGH"]


def _board_panel(jobs: dict, save: SaveData, now: float) -> Panel:
    body = Text()
    for i, tier in enumerate(_TIERS, start=1):
        entries = bounty.tier_jobs(jobs, tier)
        title = entries[0]["title"] if entries else "(none)"
        body.append(f" [{i}] ", style=f"bold {config.COLORS['gold']}")
        body.append(f"{tier:<7} — {title}\n", style=f"bold {config.COLORS['earn']}")
    if bounty.is_on_cooldown(save, now):
        body.append(
            f"\n On cooldown: {bounty.cooldown_remaining(save, now):.0f}s left",
            style=config.COLORS["danger"],
        )
    body.append("\n [ESC] Back", style="dim")
    return Panel(
        body, title="🎯  BOUNTY BOARD", title_align="left", style=config.COLORS["earn"]
    )


def _play_job(console: Console, job: dict, rng: random.Random) -> tuple[bool, float]:
    """Walk the job to a terminal node. Returns (success, payout)."""
    node_id = bounty.start_node(job)
    while True:
        node = bounty.get_node(job, node_id)
        console.print(Text(f"\n  {node['text']}", style=config.COLORS["info"]))

        if bounty.is_terminal(node):
            return bounty.terminal_result(node)

        if bounty.is_risk(node):
            console.print(Text("  ...rolling the dice...", style="dim"))
            time.sleep(0.6)
            node_id = bounty.resolve_risk(node, rng)
            continue

        # choice node
        choices = node["choices"]
        for idx, choice in enumerate(choices, start=1):
            console.print(
                Text(f"   [{idx}] ", style=f"bold {config.COLORS['gold']}")
                + Text(choice["label"], style=config.COLORS["earn"])
            )
        console.print("  Choose: ", end="")
        key = readchar.readkey()
        if key.isdigit() and 1 <= int(key) <= len(choices):
            node_id = bounty.resolve_choice(job, node_id, int(key) - 1)


def run_bounty(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "bounty", "BOUNTY JOBS", BOUNTY_TUTORIAL)
    jobs = bounty.load_jobs(config.BOUNTY_JOBS_PATH)

    while True:
        now = time.time()
        console.clear()
        console.print(balance_bar_text(save))
        console.print(_board_panel(jobs, save, now))
        console.print("Pick a tier: ", end="")
        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        if not (key.isdigit() and 1 <= int(key) <= len(_TIERS)):
            continue

        if bounty.is_on_cooldown(save, now):
            console.print(
                Text(
                    f"  Still on cooldown ({bounty.cooldown_remaining(save, now):.0f}s).",
                    style=config.COLORS["danger"],
                )
            )
            pause(console)
            continue

        tier = _TIERS[int(key) - 1]
        entries = bounty.tier_jobs(jobs, tier)
        if not entries:
            continue
        job = random.choice(entries)
        rng = random.Random()

        success, payout = _play_job(console, job, rng)
        if success:
            bounty.apply_success(save, payout)
            result_banner(console, True, f"JOB COMPLETE  +${payout:,.2f}")
        else:
            bounty.apply_failure(save, time.time())
            result_banner(console, False, "JOB FAILED — cooldown started")

        console.print(balance_bar_text(save))
        pause(console)
```

- [ ] **Step 2: Verify it imports**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "import gambs.earn.bounty_screen"`
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add gambs/earn/bounty_screen.py
git commit -m "feat: add bounty jobs screen"
```

---

## Task 13: Register Bounty Jobs in the earn selector

**Files:**
- Modify: `gambs/earn/registry.py`
- Test: `tests/test_earn_select.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_earn_select.py`:

```python
def test_registry_includes_bounty():
    ids = [g.id for g in all_earn_games()]
    assert "bounty" in ids


def test_registry_has_three_earn_games():
    assert len(all_earn_games()) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_earn_select.py::test_registry_includes_bounty" -v`
Expected: FAIL — `assert 'bounty' in ['typing_heist', 'trading']`.

- [ ] **Step 3: Add the entry**

In `gambs/earn/registry.py`, update `all_earn_games()`:

```python
def all_earn_games() -> list[EarnEntry]:
    """Return every registered earn game, in display order."""
    from gambs.earn.typing_heist_screen import run_typing_heist
    from gambs.earn.trading_screen import run_trading
    from gambs.earn.bounty_screen import run_bounty

    return [
        EarnEntry("typing_heist", "⌨  Typing Heist", run_typing_heist),
        EarnEntry("trading", "📈  Terminal Trading", run_trading),
        EarnEntry("bounty", "🎯  Bounty Jobs", run_bounty),
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_earn_select.py" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add gambs/earn/registry.py tests/test_earn_select.py
git commit -m "feat: register bounty jobs in earn selector"
```

---

## Task 14: Full-suite verification

**Files:** none (verification only)

- [ ] **Step 1: Run the entire test suite**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: PASS — all 151 previous tests plus the new ones (earn select, trading, bounty).

- [ ] **Step 2: Manual smoke of the EARN flow**

Run: `cd D:\gambs; & "D:/gambs/.venv/Scripts/python.exe" -m gambs.main`
- Press `E`: the earn selector lists Typing Heist, Terminal Trading, Bounty Jobs.
- `[2]` Terminal Trading: trade across ticks; market closes; payout ≥ $0; balance only rises.
- `[3]` Bounty Jobs: pick a tier; make choices; success pays out, failure starts a cooldown (no balance change); re-entering the board shows the cooldown timer.
- `ESC` returns cleanly to the main menu.

- [ ] **Step 3: Confirm no regressions in save round-trip**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs/tests/test_save.py" -v`
Expected: PASS.

(No commit — verification only. Any fixes needed get committed under their own task.)

---

## Self-Review Notes

- **Spec coverage:** Terminal Trading (§8) — 4 stocks, random walk, fixed session, downside capped → `trading.py` + screen. Bounty Jobs (§8) — 3 tiers, 2–4 decision points, branching, failure cooldown, JSON content → `bounty.py` + `bounty_jobs.json` + screen. Earn games credit-only invariant honored (settle floors at $0; bounty failure costs nothing).
- **Deferred (out of scope, noted):** Market Intel / Vault Key items belong to the Economy plan; the cooldown gate (`is_on_cooldown`) is the hook Vault Key will later bypass. Trading volatility scales by balance as a stand-in until the VIP system exists.
- **Type consistency:** `EarnEntry(id,label,run)` matches `GameEntry`. Trading uses `Portfolio(cash, holdings)` consistently across Tasks 6–7. Bounty node predicates (`is_choice`/`is_risk`/`is_terminal`) and `resolve_choice`/`resolve_risk`/`terminal_result` names are reused identically in Task 12.
- **Stats:** `bounty_jobs_completed` (success only) and `bounty_jobs_attempted` (both) give the Stats screen its success-rate inputs later.
