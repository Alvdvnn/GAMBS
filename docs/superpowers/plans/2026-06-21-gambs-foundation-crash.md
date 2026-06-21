# GAMBS Plan 1 — Foundation + Crash Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable, playable vertical slice of GAMBS: animated slot-machine splash screen → main menu with persistent balance bar → a fully playable Crash game → persistent JSON save, with a reusable tutorial framework.

**Architecture:** Pure game/data logic (save model, RNG math, routing, tutorial state) is separated from terminal rendering so it can be unit-tested without a TTY. Rendering uses the `rich` library; raw key input uses `readchar`. RNG is always injected as a `random.Random` instance so tests are deterministic. Interactive loops delegate all decisions to tested pure functions.

**Tech Stack:** Python 3.11+, `rich` (rendering), `readchar` (key input), `pytest` (tests).

**Spec:** `docs/superpowers/specs/2026-06-21-gambs-design.md`

**This plan covers spec sections:** 1 (Architecture — core files), 2 (Navigation), 3 (Splash), 4 (Visual Theme), 5 (Persistent Save), 6 (Tutorial System), 7 (Crash Game only). Remaining games and economy are deferred to Plans 2–4.

---

## File Structure (this plan)

```
gambs/
├── __init__.py
├── config.py                # constants, colors, paths, tunables
├── save.py                  # SaveData model + load/write JSON
├── games/
│   ├── __init__.py
│   └── crash.py             # crash math: crash point, multiplier curve, payout
├── ui/
│   ├── __init__.py
│   ├── components.py        # balance bar text + panel helpers
│   ├── splash.py            # slot-machine ASCII logo + reel frames
│   ├── menu.py              # route resolution (pure) + menu render
│   └── tutorial.py          # tutorial state + render
├── main.py                  # entry point: splash → menu loop → game dispatch
└── data/                    # save.json created at runtime (gitignored)
tests/
├── test_save.py
├── test_crash.py
├── test_components.py
├── test_splash.py
├── test_menu.py
└── test_tutorial.py
requirements.txt
pytest.ini
.gitignore
```

**Responsibilities:**
- `config.py` — single source of truth for tunable numbers and the color palette. No logic.
- `save.py` — the persisted player state model and its JSON serialization. No game rules.
- `games/crash.py` — pure crash math. No I/O, no rendering.
- `ui/components.py` — shared render helpers (balance bar). Pure string/renderable builders.
- `ui/splash.py` — ASCII logo assembly and reel animation frames. Frame builders are pure; the play loop is thin.
- `ui/menu.py` — pure key→route resolution plus the menu panel renderer.
- `ui/tutorial.py` — tutorial seen/unseen state plus the tutorial screen renderer.
- `main.py` — wiring only: owns the `rich` Console, the input loop, and dispatch. Contains no game math.

---

### Task 0: Project setup

**Files:**
- Create: `gambs/__init__.py`, `gambs/games/__init__.py`, `gambs/ui/__init__.py`
- Create: `requirements.txt`, `pytest.ini`, `.gitignore`

- [ ] **Step 1: Initialize git repo**

Run:
```bash
git -C "D:/gambs" init
git -C "D:/gambs" branch -M main
```
Expected: `Initialized empty Git repository in D:/gambs/.git/`

- [ ] **Step 2: Create package directories and init files**

Create `gambs/__init__.py` with content:
```python
"""GAMBS — terminal gambling game station."""

__version__ = "0.1.0"
```

Create `gambs/games/__init__.py` (empty file):
```python
```

Create `gambs/ui/__init__.py` (empty file):
```python
```

- [ ] **Step 3: Create requirements.txt**

```
rich>=13.7
readchar>=4.0
pytest>=8.0
```

- [ ] **Step 4: Create pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v
```

- [ ] **Step 5: Create .gitignore**

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
gambs/data/save.json
.superpowers/
```

- [ ] **Step 6: Create and activate virtual environment, install deps**

Run (PowerShell):
```powershell
py -m venv "D:/gambs/.venv"
& "D:/gambs/.venv/Scripts/python.exe" -m pip install -r "D:/gambs/requirements.txt"
```
Expected: `Successfully installed rich-... readchar-... pytest-...`

- [ ] **Step 7: Verify pytest runs (zero tests collected is fine)**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"
```
Expected: `no tests ran` (exit 5) — confirms pytest is installed and configured.

- [ ] **Step 8: Commit**

```bash
git -C "D:/gambs" add -A
git -C "D:/gambs" commit -m "chore: project scaffold, deps, pytest config"
```

---

### Task 1: config.py constants

**Files:**
- Create: `gambs/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_config.py`:
```python
from gambs import config


def test_starting_balance_is_1000():
    assert config.STARTING_BALANCE == 1000.0


def test_house_edge_is_positive_fraction():
    assert 0.0 < config.HOUSE_EDGE < 0.2


def test_palette_has_required_keys():
    for key in ("gold", "gamble", "earn", "success", "danger", "info"):
        assert key in config.COLORS
        assert config.COLORS[key].startswith("#")


def test_save_path_under_data_dir():
    assert config.SAVE_PATH.parent == config.DATA_DIR
    assert config.SAVE_PATH.name == "save.json"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_config.py
```
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.config'`

- [ ] **Step 3: Write minimal implementation**

Create `gambs/config.py`:
```python
"""Central constants, color palette, and tunable parameters for GAMBS."""

from pathlib import Path

# --- Economy ---
STARTING_BALANCE: float = 1000.0
HOUSE_EDGE: float = 0.03

# --- VIP (used in later plans, defined here for the save model) ---
VIP_XP_PER_LEVEL: int = 500
MAX_VIP_LEVEL: int = 10

# --- Crash game tunables ---
CRASH_GROWTH_RATE: float = 0.15  # k in multiplier = e^(k * elapsed_seconds)
CRASH_TICK_SECONDS: float = 0.08  # animation frame interval

# --- Paths ---
DATA_DIR: Path = Path(__file__).resolve().parent / "data"
SAVE_PATH: Path = DATA_DIR / "save.json"

# --- Color palette (hex, consumed by rich styles) ---
COLORS: dict[str, str] = {
    "bg": "#0a0a0f",
    "gold": "#ffd700",
    "gamble": "#ff6600",
    "earn": "#ff00ff",
    "success": "#00ff41",
    "danger": "#ff4444",
    "info": "#00ffff",
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_config.py
```
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/config.py tests/test_config.py
git -C "D:/gambs" commit -m "feat: add config constants and color palette"
```

---

### Task 2: SaveData model + defaults

**Files:**
- Create: `gambs/save.py`
- Test: `tests/test_save.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_save.py`:
```python
from gambs.save import SaveData, default_save


def test_default_save_starts_at_1000():
    save = default_save()
    assert save.balance == 1000.0


def test_default_save_has_empty_tutorial_and_inventory():
    save = default_save()
    assert save.tutorial_seen == []
    assert save.inventory == []


def test_default_vip_is_level_1():
    save = default_save()
    assert save.vip.level == 1
    assert save.vip.xp == 0
    assert save.vip.prestige == 0


def test_default_cosmetics_has_default_active():
    save = default_save()
    assert save.cosmetics == {"owned": ["default"], "active": "default"}


def test_default_save_sets_dates():
    save = default_save()
    assert save.created_at != ""
    assert save.last_played == save.created_at


def test_savedata_is_constructable_directly():
    save = SaveData(balance=42.0)
    assert save.balance == 42.0
    assert save.stats.games_played == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_save.py
```
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.save'`

- [ ] **Step 3: Write minimal implementation**

Create `gambs/save.py`:
```python
"""Persistent player state: model, defaults, and JSON serialization."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

from gambs import config


@dataclass
class VipState:
    level: int = 1
    xp: int = 0
    prestige: int = 0
    luck_buff: float = 0.0


@dataclass
class Stats:
    total_wagered: float = 0.0
    total_won: float = 0.0
    games_played: int = 0
    best_crash_multiplier: float = 0.0
    bounty_jobs_completed: int = 0


@dataclass
class SaveData:
    balance: float = config.STARTING_BALANCE
    tutorial_seen: list[str] = field(default_factory=list)
    vip: VipState = field(default_factory=VipState)
    inventory: list[dict] = field(default_factory=list)
    cosmetics: dict = field(
        default_factory=lambda: {"owned": ["default"], "active": "default"}
    )
    stats: Stats = field(default_factory=Stats)
    created_at: str = ""
    last_played: str = ""


def default_save() -> SaveData:
    """Return a fresh save for a brand-new player."""
    today = date.today().isoformat()
    return SaveData(created_at=today, last_played=today)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_save.py
```
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/save.py tests/test_save.py
git -C "D:/gambs" commit -m "feat: add SaveData model and default_save"
```

---

### Task 3: Save load/write round-trip

**Files:**
- Modify: `gambs/save.py` (add `to_dict`, `from_dict`, `write_save`, `load_save`)
- Modify: `tests/test_save.py` (add round-trip tests)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_save.py`:
```python
from gambs.save import write_save, load_save, to_dict, from_dict


def test_to_dict_round_trips_nested_state():
    save = default_save()
    save.vip.level = 4
    save.inventory.append({"item_id": "lucky_charm", "charges": 2})
    restored = from_dict(to_dict(save))
    assert restored.vip.level == 4
    assert restored.inventory == [{"item_id": "lucky_charm", "charges": 2}]
    assert restored.cosmetics == {"owned": ["default"], "active": "default"}


def test_write_then_load_round_trip(tmp_path):
    path = tmp_path / "save.json"
    save = default_save()
    save.balance = 777.5
    save.stats.games_played = 3
    write_save(path, save)
    loaded = load_save(path)
    assert loaded.balance == 777.5
    assert loaded.stats.games_played == 3


def test_load_missing_file_returns_default(tmp_path):
    path = tmp_path / "does_not_exist.json"
    loaded = load_save(path)
    assert loaded.balance == 1000.0
    assert path.exists()  # default is persisted on first load
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_save.py
```
Expected: FAIL — `ImportError: cannot import name 'write_save' from 'gambs.save'`

- [ ] **Step 3: Write minimal implementation**

Append to `gambs/save.py`:
```python
def to_dict(save: SaveData) -> dict:
    """Serialize SaveData (with nested dataclasses) to a plain dict."""
    return asdict(save)


def from_dict(data: dict) -> SaveData:
    """Reconstruct SaveData from a plain dict, rebuilding nested dataclasses."""
    data = dict(data)  # shallow copy so we don't mutate caller's dict
    vip = VipState(**data.get("vip", {}))
    stats = Stats(**data.get("stats", {}))
    data.pop("vip", None)
    data.pop("stats", None)
    return SaveData(vip=vip, stats=stats, **data)


def write_save(path: Path, save: SaveData) -> None:
    """Persist a save to disk as pretty JSON, creating parent dirs."""
    save.last_played = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_dict(save), indent=2), encoding="utf-8")


def load_save(path: Path) -> SaveData:
    """Load a save from disk; if absent, create and persist a default."""
    if not path.exists():
        save = default_save()
        write_save(path, save)
        return save
    data = json.loads(path.read_text(encoding="utf-8"))
    return from_dict(data)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_save.py
```
Expected: PASS (9 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/save.py tests/test_save.py
git -C "D:/gambs" commit -m "feat: add save load/write JSON round-trip"
```

---

### Task 4: Crash point generation

**Files:**
- Create: `gambs/games/crash.py`
- Test: `tests/test_crash.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_crash.py`:
```python
import random

from gambs.games.crash import generate_crash_point


def test_crash_point_is_deterministic_with_seed():
    rng = random.Random(42)
    assert generate_crash_point(rng) == 2.69


def test_crash_point_never_below_one():
    for seed in range(200):
        rng = random.Random(seed)
        assert generate_crash_point(rng) >= 1.0


def test_higher_house_edge_lowers_average_crash():
    low = [generate_crash_point(random.Random(s), house_edge=0.01) for s in range(500)]
    high = [generate_crash_point(random.Random(s), house_edge=0.10) for s in range(500)]
    assert sum(low) / len(low) > sum(high) / len(high)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_crash.py
```
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.crash'`

- [ ] **Step 3: Write minimal implementation**

Create `gambs/games/crash.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_crash.py
```
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/games/crash.py tests/test_crash.py
git -C "D:/gambs" commit -m "feat: add crash point generation"
```

---

### Task 5: Multiplier curve + payout

**Files:**
- Modify: `gambs/games/crash.py` (add `multiplier_at`, `payout`)
- Modify: `tests/test_crash.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_crash.py`:
```python
from gambs.games.crash import multiplier_at, payout


def test_multiplier_starts_at_one():
    assert multiplier_at(0.0) == 1.0


def test_multiplier_grows_over_time():
    assert multiplier_at(10.0, growth=0.15) == 4.48


def test_multiplier_is_monotonic_increasing():
    prev = 0.0
    for t in range(0, 50):
        m = multiplier_at(t * 0.5)
        assert m >= prev
        prev = m


def test_payout_multiplies_bet_by_multiplier():
    assert payout(100.0, 2.5) == 250.0


def test_payout_rounds_to_cents():
    assert payout(33.33, 1.5) == 50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_crash.py
```
Expected: FAIL — `ImportError: cannot import name 'multiplier_at' from 'gambs.games.crash'`

- [ ] **Step 3: Write minimal implementation**

Append to `gambs/games/crash.py`:
```python
def multiplier_at(elapsed: float, growth: float = config.CRASH_GROWTH_RATE) -> float:
    """Current multiplier after `elapsed` seconds: e^(growth * elapsed)."""
    return round(math.exp(growth * elapsed), 2)


def payout(bet: float, cashout_multiplier: float) -> float:
    """Winnings returned when cashing out at a given multiplier."""
    return round(bet * cashout_multiplier, 2)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_crash.py
```
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/games/crash.py tests/test_crash.py
git -C "D:/gambs" commit -m "feat: add crash multiplier curve and payout"
```

---

### Task 6: Balance bar component

**Files:**
- Create: `gambs/ui/components.py`
- Test: `tests/test_components.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_components.py`:
```python
from gambs.save import default_save
from gambs.ui.components import balance_bar_text


def test_balance_bar_shows_formatted_balance():
    save = default_save()
    save.balance = 1250.0
    text = balance_bar_text(save)
    assert "$1,250.00" in text


def test_balance_bar_shows_vip_level_and_xp():
    save = default_save()
    save.vip.level = 4
    save.vip.xp = 320
    text = balance_bar_text(save)
    assert "VIP 4" in text
    assert "320/500" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_components.py
```
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.ui.components'`

- [ ] **Step 3: Write minimal implementation**

Create `gambs/ui/components.py`:
```python
"""Shared UI render helpers. Pure text/renderable builders."""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.save import SaveData


def balance_bar_text(save: SaveData) -> str:
    """Plain-text content of the always-visible status bar."""
    return (
        f"♠ GAMBS   "
        f"\U0001f4b0 ${save.balance:,.2f}   "
        f"⭐ VIP {save.vip.level} "
        f"({save.vip.xp}/{config.VIP_XP_PER_LEVEL} XP)"
    )


def balance_bar_panel(save: SaveData) -> Panel:
    """Rich panel wrapping the status bar, styled gold-on-dark."""
    body = Text(balance_bar_text(save), style=config.COLORS["gold"])
    return Panel(body, style=config.COLORS["gold"], expand=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_components.py
```
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/ui/components.py tests/test_components.py
git -C "D:/gambs" commit -m "feat: add balance bar component"
```

---

### Task 7: Splash screen logo + reel frames

**Files:**
- Create: `gambs/ui/splash.py`
- Test: `tests/test_splash.py`

The logo is assembled from per-letter ASCII art. Each letter is a list of 6 equal-width lines. `render_logo` joins the five letters column-wise into a single 6-line string. `reel_frame` produces an intermediate animation frame where some reels still show random scrambled characters (used by the play loop).

- [ ] **Step 1: Write the failing test**

Create `tests/test_splash.py`:
```python
import random

from gambs.ui.splash import LETTERS, render_logo, reel_frame


def test_every_letter_has_six_equal_width_lines():
    for ch in "GAMBS":
        rows = LETTERS[ch]
        assert len(rows) == 6
        assert len({len(r) for r in rows}) == 1  # all rows same width


def test_render_logo_is_six_lines():
    logo = render_logo()
    assert logo.count("\n") == 5  # 6 lines => 5 newlines


def test_reel_frame_with_all_locked_equals_logo():
    # When all 5 reels are locked, the frame is the final logo.
    frame = reel_frame(locked=5, rng=random.Random(0))
    assert frame == render_logo()


def test_reel_frame_is_six_lines_when_spinning():
    frame = reel_frame(locked=2, rng=random.Random(0))
    assert frame.count("\n") == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_splash.py
```
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.ui.splash'`

- [ ] **Step 3: Write minimal implementation**

Create `gambs/ui/splash.py`:
```python
"""Slot-machine splash: ASCII logo assembly and reel animation frames.

The logo is built from five 6-line letter blocks (G A M B S). During the
intro, reels lock left-to-right; unlocked reels show scrambled glyphs.
"""

from __future__ import annotations

import random

# Each letter: exactly 6 rows, each row the same width for that letter.
LETTERS: dict[str, list[str]] = {
    "G": [
        " ██████╗ ",
        "██╔════╝ ",
        "██║  ███╗",
        "██║   ██║",
        "╚██████╔╝",
        " ╚═════╝ ",
    ],
    "A": [
        " █████╗ ",
        "██╔══██╗",
        "███████║",
        "██╔══██║",
        "██║  ██║",
        "╚═╝  ╚═╝",
    ],
    "M": [
        "███╗   ███╗",
        "████╗ ████║",
        "██╔████╔██║",
        "██║╚██╔╝██║",
        "██║ ╚═╝ ██║",
        "╚═╝     ╚═╝",
    ],
    "B": [
        "██████╗ ",
        "██╔══██╗",
        "██████╔╝",
        "██╔══██╗",
        "██████╔╝",
        "╚═════╝ ",
    ],
    "S": [
        "███████╗",
        "██╔════╝",
        "███████╗",
        "╚════██║",
        "███████║",
        "╚══════╝",
    ],
}

WORD = "GAMBS"
_SCRAMBLE = "▓▒░#@$%&*0123456789ABCDEF"


def render_logo() -> str:
    """Join all five letter blocks column-wise into a 6-line string."""
    rows = []
    for line_idx in range(6):
        rows.append("  ".join(LETTERS[ch][line_idx] for ch in WORD))
    return "\n".join(rows)


def _scrambled_block(width: int, rng: random.Random) -> list[str]:
    """A 6-line block of random glyphs at the given width."""
    return [
        "".join(rng.choice(_SCRAMBLE) for _ in range(width)) for _ in range(6)
    ]


def reel_frame(locked: int, rng: random.Random) -> str:
    """Build one animation frame.

    The first `locked` reels show their final letter; the rest show scrambled
    glyphs of the same width. `locked == 5` yields the final logo exactly.
    """
    blocks: list[list[str]] = []
    for i, ch in enumerate(WORD):
        width = len(LETTERS[ch][0])
        if i < locked:
            blocks.append(LETTERS[ch])
        else:
            blocks.append(_scrambled_block(width, rng))
    rows = []
    for line_idx in range(6):
        rows.append("  ".join(block[line_idx] for block in blocks))
    return "\n".join(rows)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_splash.py
```
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/ui/splash.py tests/test_splash.py
git -C "D:/gambs" commit -m "feat: add splash logo and reel frame builders"
```

---

### Task 8: Menu route resolution

**Files:**
- Create: `gambs/ui/menu.py`
- Test: `tests/test_menu.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_menu.py`:
```python
from gambs.save import default_save
from gambs.ui.menu import resolve_route, ROUTES, menu_panel


def test_known_keys_map_to_routes():
    assert resolve_route("g") == "gamble"
    assert resolve_route("e") == "earn"
    assert resolve_route("p") == "shop"
    assert resolve_route("v") == "vip"
    assert resolve_route("s") == "stats"
    assert resolve_route("q") == "quit"


def test_route_resolution_is_case_insensitive():
    assert resolve_route("G") == "gamble"


def test_unknown_key_returns_none():
    assert resolve_route("z") is None
    assert resolve_route("") is None


def test_menu_panel_lists_all_routes():
    panel = menu_panel(default_save())
    # Render to plain text via the panel's title/renderable for assertion.
    from rich.console import Console
    console = Console(width=80)
    with console.capture() as cap:
        console.print(panel)
    out = cap.get()
    for label in ("GAMBLE", "EARN", "SHOP", "VIP", "STATS", "QUIT"):
        assert label in out
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_menu.py
```
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.ui.menu'`

- [ ] **Step 3: Write minimal implementation**

Create `gambs/ui/menu.py`:
```python
"""Main menu: pure key->route resolution and the menu panel renderer."""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.save import SaveData

ROUTES: dict[str, str] = {
    "g": "gamble",
    "e": "earn",
    "p": "shop",
    "v": "vip",
    "s": "stats",
    "q": "quit",
}

_MENU_ITEMS = [
    ("G", "GAMBLE", "Play the casino games", "gamble"),
    ("E", "EARN", "Work mini-games for cash", "earn"),
    ("P", "SHOP", "Buy items & cosmetics", "gamble"),
    ("V", "VIP", "Level, XP & prestige", "earn"),
    ("S", "STATS", "Your record so far", "info"),
    ("Q", "QUIT", "Save and exit", "danger"),
]


def resolve_route(key: str) -> str | None:
    """Map a pressed key to a route name, or None if unbound."""
    if not key:
        return None
    return ROUTES.get(key.lower())


def menu_panel(save: SaveData) -> Panel:
    """Render the main menu as a rich Panel."""
    body = Text()
    for hotkey, label, desc, color_key in _MENU_ITEMS:
        color = config.COLORS.get(color_key, config.COLORS["gold"])
        body.append(f" [{hotkey}] ", style=f"bold {config.COLORS['gold']}")
        body.append(f"{label:<8}", style=f"bold {color}")
        body.append(f"  {desc}\n", style="white")
    return Panel(
        body,
        title="MAIN MENU",
        title_align="left",
        style=config.COLORS["gold"],
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_menu.py
```
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/ui/menu.py tests/test_menu.py
git -C "D:/gambs" commit -m "feat: add menu route resolution and panel"
```

---

### Task 9: Tutorial state framework

**Files:**
- Create: `gambs/ui/tutorial.py`
- Test: `tests/test_tutorial.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_tutorial.py`:
```python
from gambs.save import default_save
from gambs.ui.tutorial import should_show_tutorial, mark_tutorial_seen, tutorial_panel


def test_unseen_game_shows_tutorial():
    save = default_save()
    assert should_show_tutorial(save, "crash") is True


def test_seen_game_does_not_show_tutorial():
    save = default_save()
    mark_tutorial_seen(save, "crash")
    assert should_show_tutorial(save, "crash") is False


def test_mark_seen_is_idempotent():
    save = default_save()
    mark_tutorial_seen(save, "crash")
    mark_tutorial_seen(save, "crash")
    assert save.tutorial_seen.count("crash") == 1


def test_tutorial_panel_includes_title_and_steps():
    panel = tutorial_panel("CRASH", ["Place a bet", "Press C to cash out"])
    from rich.console import Console
    console = Console(width=80)
    with console.capture() as cap:
        console.print(panel)
    out = cap.get()
    assert "CRASH" in out
    assert "Place a bet" in out
    assert "Press C to cash out" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_tutorial.py
```
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.ui.tutorial'`

- [ ] **Step 3: Write minimal implementation**

Create `gambs/ui/tutorial.py`:
```python
"""Tutorial framework: seen/unseen state plus the tutorial screen renderer."""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.save import SaveData


def should_show_tutorial(save: SaveData, game_id: str) -> bool:
    """True when this game's tutorial has not yet been dismissed."""
    return game_id not in save.tutorial_seen


def mark_tutorial_seen(save: SaveData, game_id: str) -> None:
    """Record that the player has dismissed this game's tutorial (idempotent)."""
    if game_id not in save.tutorial_seen:
        save.tutorial_seen.append(game_id)


def tutorial_panel(game_name: str, steps: list[str]) -> Panel:
    """Render the how-to-play panel for a game."""
    body = Text()
    for i, step in enumerate(steps, start=1):
        body.append(f" {i}. ", style=f"bold {config.COLORS['info']}")
        body.append(f"{step}\n", style="white")
    body.append(
        "\n [P] Play   [R] Replay demo   [D] Don't show again",
        style=config.COLORS["gold"],
    )
    return Panel(
        body,
        title=f"HOW TO PLAY: {game_name}",
        title_align="left",
        style=config.COLORS["info"],
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_tutorial.py
```
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/ui/tutorial.py tests/test_tutorial.py
git -C "D:/gambs" commit -m "feat: add tutorial state framework and panel"
```

---

### Task 10: Crash round resolver (pure outcome)

This binds the math together into a single testable outcome function the interactive loop will call. It decides, given a bet, a crash point, and the moment the player cashed out (or `None` if they never did), the net result and updated stats.

**Files:**
- Modify: `gambs/games/crash.py` (add `CrashResult`, `resolve_round`)
- Modify: `tests/test_crash.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_crash.py`:
```python
from gambs.games.crash import resolve_round, CrashResult


def test_cashout_before_crash_wins():
    result = resolve_round(bet=100.0, crash_point=5.0, cashout_multiplier=2.0)
    assert isinstance(result, CrashResult)
    assert result.won is True
    assert result.cashout_multiplier == 2.0
    assert result.winnings == 200.0
    assert result.net == 100.0  # winnings minus the bet


def test_never_cashed_out_loses_bet():
    result = resolve_round(bet=100.0, crash_point=3.2, cashout_multiplier=None)
    assert result.won is False
    assert result.winnings == 0.0
    assert result.net == -100.0


def test_cashout_at_or_after_crash_loses():
    # Asking to cash out at 5.0 when it crashed at 3.0 is too late.
    result = resolve_round(bet=50.0, crash_point=3.0, cashout_multiplier=5.0)
    assert result.won is False
    assert result.net == -50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_crash.py
```
Expected: FAIL — `ImportError: cannot import name 'resolve_round' from 'gambs.games.crash'`

- [ ] **Step 3: Write minimal implementation**

Append to `gambs/games/crash.py`:
```python
from dataclasses import dataclass


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
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_crash.py
```
Expected: PASS (11 passed)

- [ ] **Step 5: Commit**

```bash
git -C "D:/gambs" add gambs/games/crash.py tests/test_crash.py
git -C "D:/gambs" commit -m "feat: add crash round outcome resolver"
```

---

### Task 11: Crash interactive screen

Wires the tested math to a live `rich` display. The multiplier rises in real time; pressing `C` cashes out, any other key during the round is ignored. Input is polled non-blocking so the multiplier keeps animating. Because this is interactive, it is verified by a manual smoke test, but ALL outcome logic is delegated to `resolve_round` (already tested).

**Files:**
- Create: `gambs/games/crash_screen.py`
- Test: manual smoke test (documented below)

- [ ] **Step 1: Implement the interactive screen**

Create `gambs/games/crash_screen.py`:
```python
"""Interactive Crash screen. All outcome math lives in games/crash.py."""

from __future__ import annotations

import random
import time

import readchar
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.games import crash
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text


def _read_key_nonblocking() -> str | None:
    """Return a pressed key if one is waiting, else None (Windows + POSIX)."""
    try:
        import msvcrt  # Windows
        if msvcrt.kbhit():
            return msvcrt.getwch()
        return None
    except ImportError:
        import select
        import sys
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            return sys.stdin.read(1)
        return None


def _rocket_panel(multiplier: float, status: str, color: str) -> Panel:
    art = Text()
    art.append(f"\n   {multiplier:.2f}x\n\n", style=f"bold {color}")
    art.append("   🚀\n\n", style=color)
    art.append(status, style=config.COLORS["gold"])
    return Panel(Align.center(art), title="CRASH", style=color)


def play_crash(console: Console, save: SaveData, bet: float) -> crash.CrashResult:
    """Run one crash round against the player's balance and return the result.

    The caller is responsible for having already validated `bet` against the
    balance and for persisting `save` afterward.
    """
    rng = random.Random()
    crash_point = crash.generate_crash_point(rng)
    start = time.monotonic()
    cashout: float | None = None

    with Live(console=console, refresh_per_second=30, screen=False) as live:
        while True:
            elapsed = time.monotonic() - start
            current = crash.multiplier_at(elapsed)
            if current >= crash_point:
                break
            key = _read_key_nonblocking()
            if key and key.lower() == "c":
                cashout = current
                break
            live.update(
                _rocket_panel(current, "[C] CASH OUT", config.COLORS["success"])
            )
            time.sleep(config.CRASH_TICK_SECONDS)

    result = crash.resolve_round(bet, crash_point, cashout)

    # Apply result to balance and stats.
    save.balance = round(save.balance + result.net, 2)
    save.stats.total_wagered += bet
    save.stats.games_played += 1
    if result.won:
        save.stats.total_won += result.winnings
        save.stats.best_crash_multiplier = max(
            save.stats.best_crash_multiplier, result.cashout_multiplier or 0.0
        )

    if result.won:
        msg = Text(
            f"CASHED OUT at {result.cashout_multiplier:.2f}x  +${result.winnings:,.2f}",
            style=f"bold {config.COLORS['success']}",
        )
    else:
        msg = Text(
            f"💥 CRASHED at {crash_point:.2f}x  -${bet:,.2f}",
            style=f"bold {config.COLORS['danger']}",
        )
    console.print(Panel(Align.center(msg), style=config.COLORS["gold"]))
    console.print(balance_bar_text(save))
    return result
```

- [ ] **Step 2: Manual smoke test**

Create a temporary throwaway script `D:/gambs/_smoke_crash.py`:
```python
from rich.console import Console
from gambs.save import default_save
from gambs.games.crash_screen import play_crash

console = Console()
save = default_save()
console.print("Starting balance:", save.balance)
play_crash(console, save, bet=100.0)
console.print("Ending balance:", save.balance)
```

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" "D:/gambs/_smoke_crash.py"
```
Expected: The multiplier animates upward. Pressing `C` shows a green "CASHED OUT" panel and balance increases; doing nothing until it crashes shows a red "CRASHED" panel and balance drops by 100. Run it twice to see both outcomes.

- [ ] **Step 3: Delete the smoke script**

Run:
```powershell
Remove-Item "D:/gambs/_smoke_crash.py"
```

- [ ] **Step 4: Commit**

```bash
git -C "D:/gambs" add gambs/games/crash_screen.py
git -C "D:/gambs" commit -m "feat: add interactive crash screen"
```

---

### Task 12: main.py — splash, menu loop, dispatch

Ties everything together: plays the splash animation, then loops the main menu, dispatching to the Crash game (other routes show a "coming soon" placeholder for now). Saves on quit.

**Files:**
- Create: `gambs/main.py`
- Test: manual smoke test

- [ ] **Step 1: Implement main.py**

Create `gambs/main.py`:
```python
"""GAMBS entry point: splash -> main menu loop -> game dispatch."""

from __future__ import annotations

import random
import time

import readchar
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.games.crash_screen import play_crash
from gambs.games import crash
from gambs.save import SaveData, load_save, write_save
from gambs.ui import splash
from gambs.ui.components import balance_bar_text
from gambs.ui.menu import menu_panel, resolve_route
from gambs.ui.tutorial import should_show_tutorial, mark_tutorial_seen, tutorial_panel

CRASH_TUTORIAL = [
    "Enter a bet amount.",
    "Watch the multiplier rise from 1.00x.",
    "Press [C] to cash out before the rocket crashes.",
    "If it crashes first, you lose your bet.",
]


def _play_splash(console: Console) -> None:
    rng = random.Random()
    console.clear()
    for locked in range(6):
        frame = splash.reel_frame(locked, rng)
        console.clear()
        console.print(Align.center(Text(frame, style=config.COLORS["success"])))
        console.print(Align.center(Text("[ Terminal Game Station ]", style=config.COLORS["gold"])))
        time.sleep(0.35)
    console.print(Align.center(Text("Press any key to start...", style="dim")))
    readchar.readkey()


def _bet_prompt(console: Console, save: SaveData) -> float | None:
    """Ask for a bet; return a valid amount or None to cancel."""
    console.print(f"Balance: ${save.balance:,.2f}. Enter bet (blank to cancel): ", end="")
    raw = input().strip()
    if not raw:
        return None
    try:
        bet = float(raw)
    except ValueError:
        console.print(Text("Invalid amount.", style=config.COLORS["danger"]))
        return None
    if bet <= 0 or bet > save.balance:
        console.print(Text("Bet must be positive and within your balance.", style=config.COLORS["danger"]))
        return None
    return round(bet, 2)


def _run_crash(console: Console, save: SaveData) -> None:
    if should_show_tutorial(save, "crash"):
        console.clear()
        console.print(tutorial_panel("CRASH", CRASH_TUTORIAL))
        choice = readchar.readkey().lower()
        if choice == "d":
            mark_tutorial_seen(save, "crash")
    bet = _bet_prompt(console, save)
    if bet is None:
        return
    play_crash(console, save, bet)
    console.print(Text("Press any key to return to menu...", style="dim"))
    readchar.readkey()


def _coming_soon(console: Console, name: str) -> None:
    console.clear()
    console.print(Panel(Align.center(Text(f"{name} — coming soon", style=config.COLORS['info'])), style=config.COLORS["gold"]))
    console.print(Text("Press any key...", style="dim"))
    readchar.readkey()


def main() -> None:
    console = Console()
    save = load_save(config.SAVE_PATH)
    _play_splash(console)

    while True:
        console.clear()
        console.print(balance_bar_text(save))
        console.print(menu_panel(save))
        console.print("Select: ", end="")
        key = readchar.readkey()
        route = resolve_route(key)

        if route == "quit":
            write_save(config.SAVE_PATH, save)
            console.print(Text("Saved. See you next time. ♠", style=config.COLORS["gold"]))
            break
        elif route == "gamble":
            _run_crash(console, save)  # Plan 2 adds a game selector here
        elif route in ("earn", "shop", "vip", "stats"):
            _coming_soon(console, route.upper())
        # unknown key: loop again

        write_save(config.SAVE_PATH, save)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full test suite**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"
```
Expected: PASS — all tests from Tasks 1–10 green (33 passed).

- [ ] **Step 3: Manual smoke test of the whole app**

Run:
```powershell
& "D:/gambs/.venv/Scripts/python.exe" -m gambs.main
```
Expected:
1. Splash: reels scramble, then lock left→right into `GAMBS`.
2. Press a key → main menu with balance bar (`$1,000.00`, `VIP 1`).
3. Press `G` → Crash tutorial (first time) → press a key → bet prompt.
4. Enter `100` → multiplier animates → press `C` to cash out or wait for crash.
5. Return to menu, balance updated.
6. Press `Q` → "Saved." and exit.
7. Confirm `gambs/data/save.json` exists with the updated balance.

- [ ] **Step 4: Commit**

```bash
git -C "D:/gambs" add gambs/main.py
git -C "D:/gambs" commit -m "feat: add main entry point with splash, menu, crash dispatch"
```

---

## Definition of Done (Plan 1)

- [ ] `python -m gambs.main` runs the full splash → menu → Crash → save loop.
- [ ] `pytest` passes (all unit tests for save, crash math, components, splash, menu, tutorial).
- [ ] `gambs/data/save.json` persists balance, stats, and tutorial state across runs.
- [ ] Crash is fully playable with working win/lose outcomes and a tutorial.
- [ ] All other menu routes show a "coming soon" placeholder (filled by Plans 2–4).

---

## Roadmap (subsequent plans)

- **Plan 2 — Remaining gamble games:** blackjack, slots, poker, roulette, dice, coinflip, baccarat. Adds a game selector under the `gamble` route. Each game: pure logic module + tests + interactive screen + tutorial entry.
- **Plan 3 — Earn Mode:** typing_heist, trading, bounty (with `data/bounty_jobs.json`). Adds the `earn` route selector.
- **Plan 4 — Economy:** shop, items (`data/items.json`), VIP leveling/prestige, cosmetics (`data/cosmetics.json`), and global difficulty scaling. Fills the `shop` and `vip` routes and wires XP gain into every game.
