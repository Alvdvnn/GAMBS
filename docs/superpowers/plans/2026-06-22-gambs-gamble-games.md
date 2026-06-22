# GAMBS Plan 2 — Game Selector + Non-Card Games Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a game-selector screen under the GAMBLE route and four new playable games — Coin Flip, Dice, Slots, Roulette — each with tested pure logic, an interactive screen, and a tutorial entry. Crash is refactored into the same selector/registry pattern.

**Architecture:** Each game keeps pure outcome math (RNG injected as `random.Random`) in its own logic module with unit tests, and interactive rendering in a separate `*_screen.py` exposing a `run(console, save)` entry. A registry lists all games; a selector screen renders the list and dispatches. Shared interactive helpers (bet prompt, tutorial gate, result banner, pause, stat application) live in `gambs/ui/prompts.py` and `gambs/games/outcome.py` so screens stay thin and DRY.

**Tech Stack:** Python 3.11+, `rich`, `readchar`, `pytest`. Run python via `& "D:/gambs/.venv/Scripts/python.exe"`.

**Spec:** `docs/superpowers/specs/2026-06-21-gambs-design.md` (sections 7 — Gamble Mode games; this plan covers Coin Flip, Dice, Slots, Roulette + the selector. Blackjack/Baccarat/Video Poker are deferred to Plan 3.)

**Commit messages:** Do NOT include any `Co-Authored-By` trailer (user preference).

---

## Existing patterns to follow (from Plan 1)

- `gambs/games/crash.py` — pure math, RNG injected, returns dataclass results.
- `gambs/games/crash_screen.py` — interactive `play_crash(console, save, bet)`, uses `rich.Live`, `_read_key_nonblocking`, mutates `save.balance`/`save.stats`.
- `gambs/ui/components.py:balance_bar_text(save)`, `gambs/ui/tutorial.py` (`should_show_tutorial`, `mark_tutorial_seen`, `tutorial_panel`).
- `gambs/main.py` currently has `_bet_prompt`, `_run_crash`, `CRASH_TUTORIAL`, `_coming_soon`, and a `gamble` route that calls `_run_crash`.
- Net convention: a game's `settle(...)` returns **net** profit/loss (win → positive, loss → negative, push → 0.0).

## File Structure (this plan)

```
gambs/
├── games/
│   ├── outcome.py          # NEW: apply_net(save, bet, net) — shared stat/balance update
│   ├── coinflip.py         # NEW: flip, settle
│   ├── coinflip_screen.py  # NEW: run_coinflip
│   ├── dice.py             # NEW: roll, settle + bet-type constants
│   ├── dice_screen.py      # NEW: run_dice
│   ├── slots.py            # NEW: SYMBOLS, spin, settle
│   ├── slots_screen.py     # NEW: run_slots
│   ├── roulette.py         # NEW: spin, color, settle + bet-type constants
│   ├── roulette_screen.py  # NEW: run_roulette
│   ├── crash_screen.py     # MODIFY: add run_crash(console, save) wrapper
│   └── registry.py         # NEW: GameEntry + all_games()
├── ui/
│   ├── prompts.py          # NEW: bet_prompt, tutorial_gate, result_banner, pause
│   └── game_select.py      # NEW: game_menu_panel, resolve_game_key, run_game_select
└── main.py                 # MODIFY: gamble route -> game_select; drop _bet_prompt/_run_crash
tests/
├── test_outcome.py
├── test_prompts.py
├── test_coinflip.py
├── test_dice.py
├── test_slots.py
├── test_roulette.py
└── test_game_select.py
```

**Responsibilities:** logic modules = pure math (testable, no IO). `*_screen.py` = interactive rendering only (manual smoke). `prompts.py`/`outcome.py` = shared interactive + state helpers. `registry.py` = the single list of games. `game_select.py` = render + dispatch.

---

### Task 1: Shared helpers — outcome + prompts

**Files:**
- Create: `gambs/games/outcome.py`, Test `tests/test_outcome.py`
- Create: `gambs/ui/prompts.py`, Test `tests/test_prompts.py`
- Modify: `gambs/main.py` (use `prompts.bet_prompt`, remove `_bet_prompt`)

- [ ] **Step 1: Write the failing test for outcome**

Create `tests/test_outcome.py`:
```python
from gambs.save import default_save
from gambs.games.outcome import apply_net


def test_apply_net_win_updates_balance_and_stats():
    save = default_save()
    apply_net(save, bet=100.0, net=200.0)
    assert save.balance == 1200.0
    assert save.stats.games_played == 1
    assert save.stats.total_wagered == 100.0
    assert save.stats.total_won == 300.0  # gross return = bet + net


def test_apply_net_loss_does_not_count_total_won():
    save = default_save()
    apply_net(save, bet=100.0, net=-100.0)
    assert save.balance == 900.0
    assert save.stats.total_won == 0.0
    assert save.stats.games_played == 1


def test_apply_net_push_is_neutral():
    save = default_save()
    apply_net(save, bet=100.0, net=0.0)
    assert save.balance == 1000.0
    assert save.stats.games_played == 1
    assert save.stats.total_won == 0.0
    assert save.stats.total_wagered == 100.0
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_outcome.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.outcome'`

- [ ] **Step 3: Implement outcome.py**

Create `gambs/games/outcome.py`:
```python
"""Shared outcome application: update balance and stats from a net result."""

from __future__ import annotations

from gambs.save import SaveData


def apply_net(save: SaveData, bet: float, net: float) -> None:
    """Apply one round's net result to the player's balance and stats.

    `net` is profit (positive), loss (negative), or push (0.0). On a win,
    `total_won` accumulates the gross return (stake + profit) to mirror the
    crash game's accounting.
    """
    save.balance = round(save.balance + net, 2)
    save.stats.total_wagered += bet
    save.stats.games_played += 1
    if net > 0:
        save.stats.total_won += round(bet + net, 2)
```

- [ ] **Step 4: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_outcome.py`
Expected: PASS (3 passed)

- [ ] **Step 5: Write the failing test for prompts**

Create `tests/test_prompts.py`:
```python
import io

from rich.console import Console

from gambs.save import default_save
from gambs.ui.prompts import bet_prompt


def _console():
    return Console(file=io.StringIO())


def test_bet_prompt_accepts_valid(monkeypatch):
    save = default_save()
    monkeypatch.setattr("builtins.input", lambda: "100")
    assert bet_prompt(_console(), save) == 100.0


def test_bet_prompt_blank_cancels(monkeypatch):
    save = default_save()
    monkeypatch.setattr("builtins.input", lambda: "   ")
    assert bet_prompt(_console(), save) is None


def test_bet_prompt_rejects_over_balance(monkeypatch):
    save = default_save()
    save.balance = 50.0
    monkeypatch.setattr("builtins.input", lambda: "100")
    assert bet_prompt(_console(), save) is None


def test_bet_prompt_rejects_nonpositive(monkeypatch):
    save = default_save()
    monkeypatch.setattr("builtins.input", lambda: "0")
    assert bet_prompt(_console(), save) is None


def test_bet_prompt_rejects_garbage(monkeypatch):
    save = default_save()
    monkeypatch.setattr("builtins.input", lambda: "abc")
    assert bet_prompt(_console(), save) is None
```

- [ ] **Step 6: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_prompts.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.ui.prompts'`

- [ ] **Step 7: Implement prompts.py**

Create `gambs/ui/prompts.py`:
```python
"""Shared interactive helpers used by every game screen.

`bet_prompt` is unit-tested (input is monkeypatched). The other helpers wrap
`readchar`/`rich` rendering and are exercised by manual smoke tests.
"""

from __future__ import annotations

import readchar
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.save import SaveData
from gambs.ui.tutorial import (
    should_show_tutorial,
    mark_tutorial_seen,
    tutorial_panel,
)


def bet_prompt(console: Console, save: SaveData) -> float | None:
    """Ask for a bet; return a valid amount within balance, or None to cancel."""
    console.print(
        f"Balance: ${save.balance:,.2f}. Enter bet (blank to cancel): ", end=""
    )
    raw = input().strip()
    if not raw:
        return None
    try:
        bet = float(raw)
    except ValueError:
        console.print(Text("Invalid amount.", style=config.COLORS["danger"]))
        return None
    if bet <= 0 or bet > save.balance:
        console.print(
            Text(
                "Bet must be positive and within your balance.",
                style=config.COLORS["danger"],
            )
        )
        return None
    return round(bet, 2)


def tutorial_gate(
    console: Console, save: SaveData, game_id: str, game_name: str, steps: list[str]
) -> None:
    """Show the tutorial once per game; [D] dismisses it permanently."""
    if not should_show_tutorial(save, game_id):
        return
    console.clear()
    console.print(tutorial_panel(game_name, steps))
    if readchar.readkey().lower() == "d":
        mark_tutorial_seen(save, game_id)


def result_banner(console: Console, won: bool, message: str) -> None:
    """Print a centered win/lose banner."""
    color = config.COLORS["success"] if won else config.COLORS["danger"]
    console.print(
        Panel(Align.center(Text(message, style=f"bold {color}")), style=config.COLORS["gold"])
    )


def pause(console: Console) -> None:
    """Wait for any keypress before returning to the previous screen."""
    console.print(Text("Press any key to return...", style="dim"))
    readchar.readkey()
```

- [ ] **Step 8: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_prompts.py`
Expected: PASS (5 passed)

- [ ] **Step 9: Refactor main.py to use prompts.bet_prompt**

In `gambs/main.py`, delete the entire `_bet_prompt` function (the `def _bet_prompt(...)` block). Add this import near the other `gambs.ui` imports:
```python
from gambs.ui.prompts import bet_prompt
```
Then in `_run_crash`, change the line `bet = _bet_prompt(console, save)` to:
```python
    bet = bet_prompt(console, save)
```

- [ ] **Step 10: Verify nothing broke**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "import gambs.main; print('import ok')"`
Expected: `import ok`
Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all prior tests + 8 new still pass (46 passed).

- [ ] **Step 11: Commit**

```bash
git -C "D:/gambs" add gambs/games/outcome.py gambs/ui/prompts.py gambs/main.py tests/test_outcome.py tests/test_prompts.py
git -C "D:/gambs" commit -m "feat: add shared outcome + prompt helpers"
```

---

### Task 2: Game registry, selector, and Crash refactor

**Files:**
- Modify: `gambs/games/crash_screen.py` (add `run_crash`)
- Create: `gambs/games/registry.py`
- Create: `gambs/ui/game_select.py`, Test `tests/test_game_select.py`
- Modify: `gambs/main.py` (route `gamble` → selector; remove `_run_crash`/`CRASH_TUTORIAL`)

- [ ] **Step 1: Add run_crash wrapper to crash_screen.py**

Append to `gambs/games/crash_screen.py`:
```python
from gambs.ui.prompts import bet_prompt, tutorial_gate, pause

CRASH_TUTORIAL = [
    "Enter a bet amount.",
    "Watch the multiplier rise from 1.00x.",
    "Press [C] to cash out before the rocket crashes.",
    "If it crashes first, you lose your bet.",
]


def run_crash(console: Console, save: SaveData) -> None:
    """Full Crash round flow: tutorial gate -> bet -> play -> pause."""
    tutorial_gate(console, save, "crash", "CRASH", CRASH_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    play_crash(console, save, bet)
    pause(console)
```

- [ ] **Step 2: Write the failing test for game_select**

Create `tests/test_game_select.py`:
```python
import io

from rich.console import Console

from gambs.games.registry import all_games, GameEntry
from gambs.ui.game_select import resolve_game_key, game_menu_panel


def test_registry_lists_crash_first():
    games = all_games()
    assert isinstance(games[0], GameEntry)
    assert games[0].id == "crash"


def test_registry_entries_are_callable():
    for entry in all_games():
        assert callable(entry.run)
        assert entry.label


def test_resolve_game_key_maps_digits_to_entries():
    games = all_games()
    assert resolve_game_key("1", games) is games[0]
    assert resolve_game_key("2", games) is games[1]


def test_resolve_game_key_out_of_range_is_none():
    games = all_games()
    assert resolve_game_key("0", games) is None
    assert resolve_game_key("9", games) is None
    assert resolve_game_key("x", games) is None


def test_menu_panel_lists_all_labels():
    games = all_games()
    console = Console(width=80, file=io.StringIO())
    with console.capture() as cap:
        console.print(game_menu_panel(games))
    out = cap.get()
    for entry in games:
        assert entry.label in out
```

- [ ] **Step 3: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_game_select.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.registry'`

- [ ] **Step 4: Implement registry.py**

Create `gambs/games/registry.py`:
```python
"""The single registry of playable gamble games.

Screen modules are imported lazily inside `all_games()` so importing the
registry never triggers heavy/interactive imports at module load.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rich.console import Console

from gambs.save import SaveData

RunFn = Callable[[Console, SaveData], None]


@dataclass
class GameEntry:
    id: str
    label: str
    run: RunFn


def all_games() -> list[GameEntry]:
    """Return every registered game, in display order."""
    from gambs.games.crash_screen import run_crash
    from gambs.games.coinflip_screen import run_coinflip
    from gambs.games.dice_screen import run_dice
    from gambs.games.slots_screen import run_slots
    from gambs.games.roulette_screen import run_roulette

    return [
        GameEntry("crash", "🚀 Crash", run_crash),
        GameEntry("coinflip", "🪙 Coin Flip", run_coinflip),
        GameEntry("dice", "🎲 Dice", run_dice),
        GameEntry("slots", "🎰 Slots", run_slots),
        GameEntry("roulette", "🎡 Roulette", run_roulette),
    ]
```

NOTE: This test (Task 2) will not pass until the coinflip/dice/slots/roulette screen modules exist (Tasks 3–6). That is expected — see Step 6. Implement registry and game_select now; the test for `all_games()` is fully green only after Task 6. To keep this task self-contained and committable, temporarily reduce `all_games()` to only the entries whose screens exist, then add the others as their tasks land. For THIS task, return only the Crash entry:

```python
    return [
        GameEntry("crash", "🚀 Crash", run_crash),
    ]
```
and import only `run_crash`. Tasks 3–6 each append their entry (and import) to `all_games()`.

- [ ] **Step 5: Implement game_select.py**

Create `gambs/ui/game_select.py`:
```python
"""Gamble game selector: render the list and dispatch the chosen game."""

from __future__ import annotations

import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.games.registry import GameEntry, all_games
from gambs.save import SaveData, write_save
from gambs.ui.components import balance_bar_text


def game_menu_panel(games: list[GameEntry]) -> Panel:
    """Render the numbered list of games."""
    body = Text()
    for i, entry in enumerate(games, start=1):
        body.append(f" [{i}] ", style=f"bold {config.COLORS['gold']}")
        body.append(f"{entry.label}\n", style=f"bold {config.COLORS['gamble']}")
    body.append("\n [ESC] Back to main menu", style="dim")
    return Panel(
        body, title="GAMBLE — choose a game", title_align="left", style=config.COLORS["gamble"]
    )


def resolve_game_key(key: str, games: list[GameEntry]) -> GameEntry | None:
    """Map a digit key to a game entry, or None if out of range/non-digit."""
    if not key or not key.isdigit():
        return None
    idx = int(key) - 1
    if 0 <= idx < len(games):
        return games[idx]
    return None


def run_game_select(console: Console, save: SaveData) -> None:
    """Loop the selector until the player presses ESC/Q to go back."""
    games = all_games()
    while True:
        console.clear()
        console.print(balance_bar_text(save))
        console.print(game_menu_panel(games))
        console.print("Select game: ", end="")
        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        entry = resolve_game_key(key, games)
        if entry is not None:
            entry.run(console, save)
            write_save(config.SAVE_PATH, save)
```

- [ ] **Step 6: Run game_select tests (partial pass expected)**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_game_select.py`
Expected: `test_registry_lists_crash_first`, `test_registry_entries_are_callable`, and `test_menu_panel_lists_all_labels` PASS. `test_resolve_game_key_maps_digits_to_entries` and `test_resolve_game_key_out_of_range_is_none` may still pass too (they only index existing entries: with one game, `resolve_game_key("2", games)` returns None, so the `is games[1]` assertion would FAIL). To keep the suite green during incremental build, mark the two multi-game tests as expected-to-fill-in: temporarily skip them by adding at the top of each of those two test functions:
```python
    import pytest
    if len(all_games()) < 5:
        pytest.skip("remaining games added in Tasks 3-6")
```
Remove these skips in Task 6 Step (final) once all five games are registered.

- [ ] **Step 7: Rewire main.py**

In `gambs/main.py`:
1. Remove the `_run_crash` function and the `CRASH_TUTORIAL` list entirely.
2. Remove now-unused imports: `from gambs.games.crash_screen import play_crash`, `from gambs.ui.prompts import bet_prompt`, `from gambs.ui.tutorial import should_show_tutorial, mark_tutorial_seen, tutorial_panel`. (Keep `from gambs.ui.components import balance_bar_text`.)
3. Add import: `from gambs.ui.game_select import run_game_select`.
4. In `main()`, change the gamble branch from:
```python
        elif route == "gamble":
            _run_crash(console, save)  # Plan 2 adds a game selector here
            write_save(config.SAVE_PATH, save)  # persist only after a state change
```
to:
```python
        elif route == "gamble":
            run_game_select(console, save)
            write_save(config.SAVE_PATH, save)
```

- [ ] **Step 8: Verify imports + suite**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "import gambs.main; import gambs.ui.game_select; print('import ok')"`
Expected: `import ok`
Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all green (no failures; the two multi-game selector tests skipped).

- [ ] **Step 9: Commit**

```bash
git -C "D:/gambs" add gambs/games/crash_screen.py gambs/games/registry.py gambs/ui/game_select.py gambs/main.py tests/test_game_select.py
git -C "D:/gambs" commit -m "feat: add game selector and registry; route gamble through selector"
```

---

### Task 3: Coin Flip

**Files:**
- Create: `gambs/games/coinflip.py`, Test `tests/test_coinflip.py`
- Create: `gambs/games/coinflip_screen.py`
- Modify: `gambs/games/registry.py` (register coinflip)

- [ ] **Step 1: Write the failing test**

Create `tests/test_coinflip.py`:
```python
import random

from gambs.games.coinflip import flip, settle


def test_flip_returns_only_heads_or_tails():
    for seed in range(50):
        assert flip(random.Random(seed)) in ("H", "T")


def test_flip_is_deterministic_for_a_seed():
    assert flip(random.Random(7)) == flip(random.Random(7))


def test_settle_win_pays_even_money():
    assert settle("H", "H", 100.0) == 100.0


def test_settle_loss_returns_negative_bet():
    assert settle("H", "T", 100.0) == -100.0
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_coinflip.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.coinflip'`

- [ ] **Step 3: Implement coinflip.py**

Create `gambs/games/coinflip.py`:
```python
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
```

- [ ] **Step 4: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_coinflip.py`
Expected: PASS (4 passed)

- [ ] **Step 5: Implement coinflip_screen.py**

Create `gambs/games/coinflip_screen.py`:
```python
"""Interactive Coin Flip screen."""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import coinflip
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

COINFLIP_TUTORIAL = [
    "Enter a bet amount.",
    "Call Heads or Tails.",
    "Win pays even money (1:1); wrong call loses your bet.",
]


def run_coinflip(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "coinflip", "COIN FLIP", COINFLIP_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    console.print("Call [H]eads or [T]ails: ", end="")
    call = readchar.readkey().upper()
    if call not in (coinflip.HEADS, coinflip.TAILS):
        return
    rng = random.Random()
    for _ in range(12):
        console.print(Text("  ...flipping...", style=config.COLORS["gold"]), end="\r")
        time.sleep(0.06)
    result = coinflip.flip(rng)
    net = coinflip.settle(call, result, bet)
    apply_net(save, bet, net)
    face = "HEADS" if result == coinflip.HEADS else "TAILS"
    won = net > 0
    sign = "+" if won else "-"
    result_banner(console, won, f"{face}  {sign}${abs(net):,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
```

- [ ] **Step 6: Register coinflip in registry.py**

In `gambs/games/registry.py`, inside `all_games()`, add the import `from gambs.games.coinflip_screen import run_coinflip` and append the entry so the list reads:
```python
    return [
        GameEntry("crash", "🚀 Crash", run_crash),
        GameEntry("coinflip", "🪙 Coin Flip", run_coinflip),
    ]
```

- [ ] **Step 7: Verify**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "import gambs.games.coinflip_screen; from gambs.games.registry import all_games; print([g.id for g in all_games()])"`
Expected: `['crash', 'coinflip']`
Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all green.

- [ ] **Step 8: Commit**

```bash
git -C "D:/gambs" add gambs/games/coinflip.py gambs/games/coinflip_screen.py gambs/games/registry.py tests/test_coinflip.py
git -C "D:/gambs" commit -m "feat: add coin flip game"
```

---

### Task 4: Dice

**Files:**
- Create: `gambs/games/dice.py`, Test `tests/test_dice.py`
- Create: `gambs/games/dice_screen.py`
- Modify: `gambs/games/registry.py` (register dice)

Game design: two dice. Bet LOW (total 2–6), HIGH (total 8–12), or SEVEN (total == 7). LOW/HIGH pay 1:1 and **push (return stake)** on a 7, making them fair; SEVEN pays 4:1.

- [ ] **Step 1: Write the failing test**

Create `tests/test_dice.py`:
```python
import random

from gambs.games.dice import roll, settle, BET_LOW, BET_HIGH, BET_SEVEN


def test_roll_returns_two_dice_in_range():
    for seed in range(50):
        d1, d2 = roll(random.Random(seed))
        assert 1 <= d1 <= 6 and 1 <= d2 <= 6


def test_low_wins_below_seven():
    assert settle(BET_LOW, (2, 3), 100.0) == 100.0   # total 5


def test_low_loses_above_seven():
    assert settle(BET_LOW, (5, 4), 100.0) == -100.0  # total 9


def test_low_pushes_on_seven():
    assert settle(BET_LOW, (3, 4), 100.0) == 0.0     # total 7


def test_high_wins_above_seven():
    assert settle(BET_HIGH, (6, 4), 100.0) == 100.0  # total 10


def test_high_pushes_on_seven():
    assert settle(BET_HIGH, (1, 6), 100.0) == 0.0    # total 7


def test_seven_bet_pays_four_to_one():
    assert settle(BET_SEVEN, (3, 4), 100.0) == 400.0


def test_seven_bet_loses_off_seven():
    assert settle(BET_SEVEN, (2, 2), 100.0) == -100.0


def test_unknown_bet_type_raises():
    import pytest
    with pytest.raises(ValueError):
        settle("nope", (1, 1), 100.0)
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_dice.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.dice'`

- [ ] **Step 3: Implement dice.py**

Create `gambs/games/dice.py`:
```python
"""Dice: two dice, bet LOW/HIGH/SEVEN. LOW/HIGH push on 7. Pure logic."""

from __future__ import annotations

import random

BET_LOW = "low"
BET_HIGH = "high"
BET_SEVEN = "seven"


def roll(rng: random.Random) -> tuple[int, int]:
    """Roll two six-sided dice."""
    return rng.randint(1, 6), rng.randint(1, 6)


def settle(bet_type: str, dice: tuple[int, int], bet: float) -> float:
    """Net result for a dice bet.

    LOW wins on total < 7, HIGH on total > 7; both push (0.0) on a 7.
    SEVEN pays 4:1 on exactly 7, otherwise loses.
    """
    total = dice[0] + dice[1]
    if bet_type == BET_SEVEN:
        return round(bet * 4 if total == 7 else -bet, 2)
    if bet_type == BET_LOW:
        if total == 7:
            return 0.0
        return round(bet if total < 7 else -bet, 2)
    if bet_type == BET_HIGH:
        if total == 7:
            return 0.0
        return round(bet if total > 7 else -bet, 2)
    raise ValueError(f"unknown bet type: {bet_type}")
```

- [ ] **Step 4: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_dice.py`
Expected: PASS (9 passed)

- [ ] **Step 5: Implement dice_screen.py**

Create `gambs/games/dice_screen.py`:
```python
"""Interactive Dice screen."""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import dice
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

DICE_TUTORIAL = [
    "Enter a bet amount.",
    "Bet LOW (2-6), HIGH (8-12), or SEVEN (=7).",
    "LOW/HIGH pay 1:1 and push on a 7. SEVEN pays 4:1.",
]

_CHOICES = {"l": dice.BET_LOW, "h": dice.BET_HIGH, "s": dice.BET_SEVEN}


def run_dice(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "dice", "DICE", DICE_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    console.print("Bet [L]ow  [H]igh  [S]even: ", end="")
    key = readchar.readkey().lower()
    bet_type = _CHOICES.get(key)
    if bet_type is None:
        return
    rng = random.Random()
    for _ in range(12):
        d = (rng.randint(1, 6), rng.randint(1, 6))
        console.print(Text(f"  rolling... {d[0]} {d[1]}", style=config.COLORS["gold"]), end="\r")
        time.sleep(0.06)
    result = dice.roll(rng)
    net = dice.settle(bet_type, result, bet)
    apply_net(save, bet, net)
    total = result[0] + result[1]
    if net > 0:
        result_banner(console, True, f"Rolled {result[0]}+{result[1]}={total}  WIN +${net:,.2f}")
    elif net == 0:
        result_banner(console, False, f"Rolled {total} — PUSH, bet returned")
    else:
        result_banner(console, False, f"Rolled {result[0]}+{result[1]}={total}  LOSE -${abs(net):,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
```

- [ ] **Step 6: Register dice in registry.py**

Add `from gambs.games.dice_screen import run_dice` in `all_games()` and append `GameEntry("dice", "🎲 Dice", run_dice),` after the coinflip entry.

- [ ] **Step 7: Verify**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all green.

- [ ] **Step 8: Commit**

```bash
git -C "D:/gambs" add gambs/games/dice.py gambs/games/dice_screen.py gambs/games/registry.py tests/test_dice.py
git -C "D:/gambs" commit -m "feat: add dice game"
```

---

### Task 5: Slots

**Files:**
- Create: `gambs/games/slots.py`, Test `tests/test_slots.py`
- Create: `gambs/games/slots_screen.py`
- Modify: `gambs/games/registry.py` (register slots)

Game design: 3 reels over symbols `["7", "BAR", "♦", "♣", "♥", "♠"]` with weights (7 rarest). Three 7s pay 50:1, three BAR 20:1, any other three-of-a-kind 5:1, exactly two 7s 2:1, else lose. `settle` returns net profit.

- [ ] **Step 1: Write the failing test**

Create `tests/test_slots.py`:
```python
import random

from gambs.games.slots import SYMBOLS, spin, settle


def test_spin_returns_three_valid_symbols():
    for seed in range(50):
        reels = spin(random.Random(seed))
        assert len(reels) == 3
        for s in reels:
            assert s in SYMBOLS


def test_three_sevens_pays_50x():
    assert settle(("7", "7", "7"), 10.0) == 500.0


def test_three_bars_pays_20x():
    assert settle(("BAR", "BAR", "BAR"), 10.0) == 200.0


def test_three_of_a_kind_pays_5x():
    assert settle(("♥", "♥", "♥"), 10.0) == 50.0


def test_two_sevens_pays_2x():
    assert settle(("7", "7", "♠"), 10.0) == 20.0


def test_no_match_loses():
    assert settle(("♦", "♣", "♥"), 10.0) == -10.0
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_slots.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.slots'`

- [ ] **Step 3: Implement slots.py**

Create `gambs/games/slots.py`:
```python
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
```

- [ ] **Step 4: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_slots.py`
Expected: PASS (6 passed)

- [ ] **Step 5: Implement slots_screen.py**

Create `gambs/games/slots_screen.py`:
```python
"""Interactive Slots screen."""

from __future__ import annotations

import random
import time

from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import slots
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

SLOTS_TUTORIAL = [
    "Enter a bet amount.",
    "Three 7s pay 50x, three BARs 20x, any other triple 5x.",
    "Exactly two 7s pay 2x. Anything else loses.",
]


def run_slots(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "slots", "SLOTS", SLOTS_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    rng = random.Random()
    for _ in range(14):
        temp = rng.choices(slots.SYMBOLS, k=3)
        console.print(
            Text(f"  [ {temp[0]} | {temp[1]} | {temp[2]} ]", style=config.COLORS["gold"]),
            end="\r",
        )
        time.sleep(0.07)
    reels = slots.spin(rng)
    net = slots.settle(reels, bet)
    apply_net(save, bet, net)
    console.print(Text(f"  [ {reels[0]} | {reels[1]} | {reels[2]} ]", style=config.COLORS["gold"]))
    won = net > 0
    sign = "+" if won else "-"
    result_banner(console, won, f"{'WIN' if won else 'LOSE'} {sign}${abs(net):,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
```

- [ ] **Step 6: Register slots in registry.py**

Add `from gambs.games.slots_screen import run_slots` in `all_games()` and append `GameEntry("slots", "🎰 Slots", run_slots),` after the dice entry.

- [ ] **Step 7: Verify**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all green.

- [ ] **Step 8: Commit**

```bash
git -C "D:/gambs" add gambs/games/slots.py gambs/games/slots_screen.py gambs/games/registry.py tests/test_slots.py
git -C "D:/gambs" commit -m "feat: add slots game"
```

---

### Task 6: Roulette

**Files:**
- Create: `gambs/games/roulette.py`, Test `tests/test_roulette.py`
- Create: `gambs/games/roulette_screen.py`
- Modify: `gambs/games/registry.py` (register roulette)
- Modify: `tests/test_game_select.py` (remove the temporary skips from Task 2 Step 6)

Game design: European single-zero (0–36). Bets: STRAIGHT (a number, pays 35:1), RED/BLACK/ODD/EVEN/LOW(1–18)/HIGH(19–36) (all 1:1). Any outside bet loses on 0.

- [ ] **Step 1: Write the failing test**

Create `tests/test_roulette.py`:
```python
import random

from gambs.games.roulette import (
    spin, color, settle,
    BET_STRAIGHT, BET_RED, BET_BLACK, BET_ODD, BET_EVEN, BET_LOW, BET_HIGH,
)


def test_spin_in_range():
    for seed in range(100):
        assert 0 <= spin(random.Random(seed)) <= 36


def test_color_mapping():
    assert color(0) == "green"
    assert color(1) == "red"
    assert color(2) == "black"


def test_straight_hit_pays_35():
    assert settle(BET_STRAIGHT, 17, 17, 10.0) == 350.0


def test_straight_miss_loses():
    assert settle(BET_STRAIGHT, 17, 18, 10.0) == -10.0


def test_red_wins_on_red():
    assert settle(BET_RED, None, 1, 10.0) == 10.0


def test_red_loses_on_black():
    assert settle(BET_RED, None, 2, 10.0) == -10.0


def test_outside_bet_loses_on_zero():
    assert settle(BET_RED, None, 0, 10.0) == -10.0
    assert settle(BET_EVEN, None, 0, 10.0) == -10.0
    assert settle(BET_LOW, None, 0, 10.0) == -10.0


def test_even_and_odd():
    assert settle(BET_EVEN, None, 4, 10.0) == 10.0
    assert settle(BET_ODD, None, 4, 10.0) == -10.0


def test_low_and_high():
    assert settle(BET_LOW, None, 10, 10.0) == 10.0
    assert settle(BET_HIGH, None, 10, 10.0) == -10.0
    assert settle(BET_HIGH, None, 25, 10.0) == 10.0
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_roulette.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.roulette'`

- [ ] **Step 3: Implement roulette.py**

Create `gambs/games/roulette.py`:
```python
"""Roulette: European single-zero wheel. Pure logic, RNG injected."""

from __future__ import annotations

import random

BET_STRAIGHT = "straight"
BET_RED = "red"
BET_BLACK = "black"
BET_ODD = "odd"
BET_EVEN = "even"
BET_LOW = "low"    # 1-18
BET_HIGH = "high"  # 19-36

_RED_NUMBERS = {
    1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36
}


def spin(rng: random.Random) -> int:
    """Spin the wheel; returns 0-36."""
    return rng.randint(0, 36)


def color(n: int) -> str:
    """Return 'green' (0), 'red', or 'black' for a pocket."""
    if n == 0:
        return "green"
    return "red" if n in _RED_NUMBERS else "black"


def settle(bet_type: str, bet_value: int | None, result: int, amount: float) -> float:
    """Net result for a roulette bet.

    `bet_value` is the chosen number for STRAIGHT bets, otherwise ignored
    (pass None). Even-money outside bets all lose on 0.
    """
    if bet_type == BET_STRAIGHT:
        return round(amount * 35 if result == bet_value else -amount, 2)
    if result == 0:
        return round(-amount, 2)
    if bet_type == BET_RED:
        won = color(result) == "red"
    elif bet_type == BET_BLACK:
        won = color(result) == "black"
    elif bet_type == BET_ODD:
        won = result % 2 == 1
    elif bet_type == BET_EVEN:
        won = result % 2 == 0
    elif bet_type == BET_LOW:
        won = 1 <= result <= 18
    elif bet_type == BET_HIGH:
        won = 19 <= result <= 36
    else:
        raise ValueError(f"unknown bet type: {bet_type}")
    return round(amount if won else -amount, 2)
```

- [ ] **Step 4: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_roulette.py`
Expected: PASS (10 passed)

- [ ] **Step 5: Implement roulette_screen.py**

Create `gambs/games/roulette_screen.py`:
```python
"""Interactive Roulette screen."""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import roulette
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

ROULETTE_TUTORIAL = [
    "Enter a bet amount.",
    "Pick a bet: a single number (35:1) or red/black/odd/even/low/high (1:1).",
    "Any outside bet loses if the ball lands on 0.",
]

# key -> (bet_type, needs_number)
_OUTSIDE = {
    "r": roulette.BET_RED,
    "b": roulette.BET_BLACK,
    "o": roulette.BET_ODD,
    "e": roulette.BET_EVEN,
    "l": roulette.BET_LOW,
    "h": roulette.BET_HIGH,
}


def run_roulette(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "roulette", "ROULETTE", ROULETTE_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    console.print("Bet [N]umber, [R]ed [B]lack [O]dd [E]ven [L]ow [H]igh: ", end="")
    key = readchar.readkey().lower()
    bet_value: int | None = None
    if key == "n":
        console.print("\nNumber 0-36: ", end="")
        raw = input().strip()
        try:
            bet_value = int(raw)
        except ValueError:
            return
        if not 0 <= bet_value <= 36:
            return
        bet_type = roulette.BET_STRAIGHT
    else:
        bet_type = _OUTSIDE.get(key)
        if bet_type is None:
            return
    rng = random.Random()
    for _ in range(16):
        n = rng.randint(0, 36)
        console.print(Text(f"  spinning... {n:>2}", style=config.COLORS["gold"]), end="\r")
        time.sleep(0.06)
    result = roulette.spin(rng)
    net = roulette.settle(bet_type, bet_value, result, bet)
    apply_net(save, bet, net)
    won = net > 0
    sign = "+" if won else "-"
    result_banner(
        console, won, f"Ball on {result} ({roulette.color(result)})  {'WIN' if won else 'LOSE'} {sign}${abs(net):,.2f}"
    )
    console.print(balance_bar_text(save))
    pause(console)
```

- [ ] **Step 6: Register roulette in registry.py**

Add `from gambs.games.roulette_screen import run_roulette` in `all_games()` and append `GameEntry("roulette", "🎡 Roulette", run_roulette),` after the slots entry. The final list must be exactly the five entries in the order: crash, coinflip, dice, slots, roulette.

- [ ] **Step 7: Remove the temporary skips in test_game_select.py**

In `tests/test_game_select.py`, delete the two `pytest.skip("remaining games added in Tasks 3-6")` guard blocks added in Task 2 Step 6, so `test_resolve_game_key_maps_digits_to_entries` and `test_resolve_game_key_out_of_range_is_none` run for real (there are now 5 games, so `games[1]` exists and `resolve_game_key("9", games)` is None).

- [ ] **Step 8: Verify full suite**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all green, no skips. Confirm registry order:
Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "from gambs.games.registry import all_games; print([g.id for g in all_games()])"`
Expected: `['crash', 'coinflip', 'dice', 'slots', 'roulette']`

- [ ] **Step 9: Commit**

```bash
git -C "D:/gambs" add gambs/games/roulette.py gambs/games/roulette_screen.py gambs/games/registry.py tests/test_roulette.py tests/test_game_select.py
git -C "D:/gambs" commit -m "feat: add roulette game and finalize selector tests"
```

---

## Definition of Done (Plan 2)

- [ ] GAMBLE route opens a selector listing Crash, Coin Flip, Dice, Slots, Roulette.
- [ ] Each new game is playable: tutorial (first time) → bet → play → result → balance updated → back to selector. ESC/Q returns to the main menu.
- [ ] All pure logic (coinflip/dice/slots/roulette settle + spin/roll/flip) is unit-tested; full suite green with no skips.
- [ ] Save persists after each game round.
- [ ] No `Co-Authored-By` trailer in any commit.

## Manual smoke test (human, real terminal)

```powershell
cd D:\gambs
& "D:/gambs/.venv/Scripts/python.exe" -m gambs.main
```
Press `G` → selector. Play each of `1`–`5`, confirm bet/animation/result/balance work and ESC returns to the main menu.

## Roadmap (remaining)

- **Plan 3 — Card games:** shared `gambs/games/cards.py` (Card, deck, display) + Blackjack, Baccarat, Video Poker, each registered in the selector.
- **Plan 4 — Earn Mode:** Typing Heist, Terminal Trading, Bounty Jobs.
- **Plan 5 — Economy:** Item Shop, VIP leveling/prestige, Cosmetics, global difficulty scaling.
