# GAMBS Plan 3 — Card Games Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three card games — Blackjack, Baccarat, Video Poker — to the GAMBLE selector, all sharing one tested playing-card model (`gambs/games/cards.py`).

**Architecture:** A shared `cards.py` provides a `Card` dataclass, deck building, RNG-injected shuffle, and string rendering. Each game keeps pure outcome math (RNG injected as a shuffled deck list) in its own logic module with unit tests, plus an interactive `*_screen.py` exposing `run_<game>(console, save)`. Each new game registers in `gambs/games/registry.py`. Settle functions follow the established **net** convention (win positive, loss negative, push 0.0) and update state through `gambs/games/outcome.py:apply_net`.

**Tech Stack:** Python 3.11+, `rich`, `readchar`, `pytest`. Run python via `& "D:/gambs/.venv/Scripts/python.exe"`. Run pytest from `D:\gambs`.

**Spec:** `docs/superpowers/specs/2026-06-21-gambs-design.md` section 7 (Blackjack, Poker/Video Poker, Baccarat).

**Commit messages:** Do NOT include any `Co-Authored-By` trailer (user preference).

**Out of scope for this plan (deferred):** Blackjack split and insurance; multi-bet Baccarat; progressive/variable bet video poker. These are noted so the engineer does not build them. Hit/Stand/Double is the full Blackjack scope here.

---

## Existing patterns to follow (from Plans 1 & 2)

- Pure logic modules: RNG injected, return plain values/dataclasses, no I/O. See `gambs/games/dice.py`, `gambs/games/roulette.py`.
- `*_screen.py`: interactive only (manual smoke), call shared helpers. See `gambs/games/dice_screen.py`.
- Shared helpers already exist:
  - `gambs/games/outcome.py:apply_net(save, bet, net)` — updates balance + stats.
  - `gambs/ui/prompts.py` — `bet_prompt(console, save) -> float | None`, `tutorial_gate(console, save, game_id, game_name, steps)`, `result_banner(console, won, message)`, `pause(console)`.
  - `gambs/ui/components.py:balance_bar_text(save)`.
- Net convention: `settle(...)` returns net profit/loss (win → positive, loss → negative, push → 0.0).
- Registry: `gambs/games/registry.py:all_games()` lazily imports each screen's `run_*` inside the function and returns `GameEntry(id, label, run)` items.

The registry currently (after Plan 2) reads:
```python
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
This plan appends three entries: blackjack, baccarat, poker (final order: crash, coinflip, dice, slots, roulette, blackjack, baccarat, poker — selector keys 1-8).

## File Structure (this plan)

```
gambs/games/
├── cards.py             # NEW: Card, RANKS, SUITS, make_deck, shuffle, card_str, hand_str
├── blackjack.py         # NEW: hand_value, is_blackjack, dealer_play, settle, BlackjackResult
├── blackjack_screen.py  # NEW: run_blackjack
├── baccarat.py          # NEW: card_value, hand_total, play_round, settle + bet-type constants
├── baccarat_screen.py   # NEW: run_baccarat
├── poker.py             # NEW: PAYTABLE, evaluate, deal, redraw, settle
├── poker_screen.py      # NEW: run_poker
└── registry.py          # MODIFY: register blackjack, baccarat, poker
tests/
├── test_cards.py
├── test_blackjack.py
├── test_baccarat.py
└── test_poker.py
```

**Deck convention:** A deck is a `list[Card]`. Cards are drawn with `deck.pop()` (from the end). Because `shuffle` randomizes order, popping from the end is uniformly random. Tests that need determinism build a small explicit deck list (the LAST element is drawn first).

---

### Task 1: Shared playing-card model

**Files:**
- Create: `gambs/games/cards.py`
- Test: `tests/test_cards.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cards.py`:
```python
import random

from gambs.games.cards import (
    Card, RANKS, SUITS, make_deck, shuffle, card_str, hand_str,
)


def test_make_deck_has_52_unique_cards():
    deck = make_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52


def test_make_deck_covers_all_rank_suit_pairs():
    deck = make_deck()
    for r in RANKS:
        for s in SUITS:
            assert Card(r, s) in deck


def test_shuffle_returns_full_deck():
    deck = shuffle(random.Random(0))
    assert len(deck) == 52
    assert len(set(deck)) == 52


def test_shuffle_is_deterministic_for_a_seed():
    assert shuffle(random.Random(7)) == shuffle(random.Random(7))


def test_shuffle_changes_order():
    assert shuffle(random.Random(1)) != make_deck()


def test_card_str_and_hand_str():
    assert card_str(Card("A", "♠")) == "A♠"
    assert card_str(Card("10", "♥")) == "10♥"
    assert hand_str([Card("A", "♠"), Card("10", "♥")]) == "A♠ 10♥"
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_cards.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.cards'`

- [ ] **Step 3: Implement cards.py**

Create `gambs/games/cards.py`:
```python
"""Shared playing-card model for card games. Pure, RNG injected."""

from __future__ import annotations

import random
from dataclasses import dataclass

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str


def make_deck() -> list[Card]:
    """A fresh ordered 52-card deck."""
    return [Card(rank, suit) for suit in SUITS for rank in RANKS]


def shuffle(rng: random.Random) -> list[Card]:
    """Return a new shuffled 52-card deck. Draw cards with deck.pop()."""
    deck = make_deck()
    rng.shuffle(deck)
    return deck


def card_str(card: Card) -> str:
    """Compact display like 'A♠' or '10♥'."""
    return f"{card.rank}{card.suit}"


def hand_str(cards: list[Card]) -> str:
    """Space-joined cards, e.g. 'A♠ 10♥'."""
    return " ".join(card_str(card) for card in cards)
```

- [ ] **Step 4: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_cards.py`
Expected: PASS (6 passed)

- [ ] **Step 5: Verify full suite still green**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all prior tests + 6 new pass.

- [ ] **Step 6: Commit**

```bash
git -C "D:/gambs" add gambs/games/cards.py tests/test_cards.py
git -C "D:/gambs" commit -m "feat: add shared playing-card model"
```

---

### Task 2: Blackjack

**Files:**
- Create: `gambs/games/blackjack.py`, Test `tests/test_blackjack.py`
- Create: `gambs/games/blackjack_screen.py`
- Modify: `gambs/games/registry.py`

Game design: Player vs Dealer. Hit/Stand/Double (split & insurance deferred). Dealer hits until reaching 17 (stands on 17+). Blackjack (2-card 21) pays 3:2. Aces count 11, reduced to 1 as needed to avoid bust.

- [ ] **Step 1: Write the failing test**

Create `tests/test_blackjack.py`:
```python
from gambs.games.cards import Card
from gambs.games.blackjack import (
    hand_value, is_blackjack, dealer_play, settle, BlackjackResult,
)


def test_hand_value_no_ace():
    assert hand_value([Card("10", "♠"), Card("7", "♥")]) == 17


def test_face_cards_are_ten():
    assert hand_value([Card("K", "♠"), Card("Q", "♥")]) == 20


def test_ace_counts_eleven_when_safe():
    assert hand_value([Card("A", "♠"), Card("9", "♥")]) == 20


def test_ace_reduces_to_one_to_avoid_bust():
    assert hand_value([Card("A", "♠"), Card("9", "♥"), Card("5", "♣")]) == 15


def test_two_aces_one_stays_eleven():
    assert hand_value([Card("A", "♠"), Card("A", "♥")]) == 12


def test_is_blackjack_true_for_two_card_21():
    assert is_blackjack([Card("A", "♠"), Card("K", "♥")]) is True


def test_is_blackjack_false_for_three_card_21():
    assert is_blackjack([Card("7", "♠"), Card("7", "♥"), Card("7", "♣")]) is False


def test_dealer_hits_until_17():
    dealer = [Card("6", "♠"), Card("6", "♥")]  # 12
    deck = [Card("5", "♣")]  # drawn -> 17, then stands
    dealer_play(dealer, deck)
    assert hand_value(dealer) == 17
    assert len(dealer) == 3


def test_dealer_stands_on_17():
    dealer = [Card("10", "♠"), Card("7", "♥")]  # 17
    deck = [Card("9", "♣")]  # must NOT be drawn
    dealer_play(dealer, deck)
    assert len(dealer) == 2
    assert len(deck) == 1


def test_settle_player_bust_loses():
    player = [Card("10", "♠"), Card("9", "♥"), Card("5", "♣")]  # 24
    dealer = [Card("10", "♦"), Card("8", "♣")]
    result = settle(player, dealer, 100.0)
    assert result.net == -100.0
    assert result.outcome == "lose"


def test_settle_dealer_bust_player_wins():
    player = [Card("10", "♠"), Card("9", "♥")]  # 19
    dealer = [Card("10", "♦"), Card("6", "♣"), Card("9", "♠")]  # 25
    assert settle(player, dealer, 100.0).net == 100.0


def test_settle_higher_total_wins():
    player = [Card("10", "♠"), Card("9", "♥")]  # 19
    dealer = [Card("10", "♦"), Card("7", "♣")]  # 17
    assert settle(player, dealer, 100.0).net == 100.0


def test_settle_equal_total_pushes():
    player = [Card("10", "♠"), Card("8", "♥")]  # 18
    dealer = [Card("10", "♦"), Card("8", "♣")]  # 18
    result = settle(player, dealer, 100.0)
    assert result.net == 0.0
    assert result.outcome == "push"


def test_settle_player_blackjack_pays_3_to_2():
    player = [Card("A", "♠"), Card("K", "♥")]
    dealer = [Card("10", "♦"), Card("7", "♣")]
    result = settle(player, dealer, 100.0)
    assert result.net == 150.0
    assert result.outcome == "blackjack"


def test_settle_both_blackjack_pushes():
    player = [Card("A", "♠"), Card("K", "♥")]
    dealer = [Card("A", "♦"), Card("Q", "♣")]
    assert settle(player, dealer, 100.0).net == 0.0


def test_settle_dealer_blackjack_player_loses():
    player = [Card("10", "♠"), Card("9", "♥")]  # 19, not blackjack
    dealer = [Card("A", "♦"), Card("K", "♣")]
    assert settle(player, dealer, 100.0).net == -100.0
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_blackjack.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.blackjack'`

- [ ] **Step 3: Implement blackjack.py**

Create `gambs/games/blackjack.py`:
```python
"""Blackjack: pure hand math + dealer policy + settlement. RNG via deck list."""

from __future__ import annotations

from dataclasses import dataclass

from gambs.games.cards import Card

_TENS = {"10", "J", "Q", "K"}


def hand_value(cards: list[Card]) -> int:
    """Best blackjack total: aces are 11, reduced to 1 as needed to avoid bust."""
    total = 0
    aces = 0
    for card in cards:
        if card.rank == "A":
            aces += 1
            total += 11
        elif card.rank in _TENS:
            total += 10
        else:
            total += int(card.rank)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_blackjack(cards: list[Card]) -> bool:
    """A natural: exactly two cards totalling 21."""
    return len(cards) == 2 and hand_value(cards) == 21


def dealer_play(dealer: list[Card], deck: list[Card]) -> list[Card]:
    """Dealer draws (in place) until reaching 17 or more. Returns the hand."""
    while hand_value(dealer) < 17:
        dealer.append(deck.pop())
    return dealer


@dataclass
class BlackjackResult:
    outcome: str  # "blackjack" | "win" | "lose" | "push"
    net: float


def settle(player: list[Card], dealer: list[Card], bet: float) -> BlackjackResult:
    """Decide a finished hand. `bet` is the effective wager (already doubled if
    the player doubled). Net follows the win-positive/loss-negative convention.
    """
    player_bj = is_blackjack(player)
    dealer_bj = is_blackjack(dealer)
    if player_bj and dealer_bj:
        return BlackjackResult("push", 0.0)
    if player_bj:
        return BlackjackResult("blackjack", round(bet * 1.5, 2))
    if dealer_bj:
        return BlackjackResult("lose", round(-bet, 2))

    pv = hand_value(player)
    dv = hand_value(dealer)
    if pv > 21:
        return BlackjackResult("lose", round(-bet, 2))
    if dv > 21 or pv > dv:
        return BlackjackResult("win", round(bet, 2))
    if pv < dv:
        return BlackjackResult("lose", round(-bet, 2))
    return BlackjackResult("push", 0.0)
```

- [ ] **Step 4: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_blackjack.py`
Expected: PASS (15 passed)

- [ ] **Step 5: Implement blackjack_screen.py**

Create `gambs/games/blackjack_screen.py`:
```python
"""Interactive Blackjack screen."""

from __future__ import annotations

import random

import readchar
from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import blackjack, cards
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

BLACKJACK_TUTORIAL = [
    "Enter a bet amount.",
    "Beat the dealer by getting closer to 21 without going over.",
    "[H]it draws a card, [S]tand holds, [D]ouble doubles your bet for one card.",
    "Dealer hits until 17. A two-card 21 (blackjack) pays 3:2.",
]


def _show_table(console: Console, player, dealer, hide_hole: bool) -> None:
    console.clear()
    if hide_hole:
        dealer_text = f"{cards.card_str(dealer[0])} ??"
    else:
        dealer_text = f"{cards.hand_str(dealer)}  ({blackjack.hand_value(dealer)})"
    console.print(Text(f"Dealer: {dealer_text}", style=config.COLORS["info"]))
    console.print(
        Text(
            f"You:    {cards.hand_str(player)}  ({blackjack.hand_value(player)})",
            style=config.COLORS["gold"],
        )
    )


def run_blackjack(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "blackjack", "BLACKJACK", BLACKJACK_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    rng = random.Random()
    deck = cards.shuffle(rng)
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    effective_bet = bet
    player_bust = False

    if not blackjack.is_blackjack(player) and not blackjack.is_blackjack(dealer):
        while True:
            _show_table(console, player, dealer, hide_hole=True)
            can_double = len(player) == 2 and effective_bet * 2 <= save.balance
            prompt = "[H]it  [S]tand" + ("  [D]ouble" if can_double else "")
            console.print(prompt + ": ", end="")
            key = readchar.readkey().lower()
            if key == "h":
                player.append(deck.pop())
                if blackjack.hand_value(player) > 21:
                    player_bust = True
                    break
            elif key == "d" and can_double:
                effective_bet = bet * 2
                player.append(deck.pop())
                player_bust = blackjack.hand_value(player) > 21
                break
            elif key == "s":
                break
        if not player_bust:
            blackjack.dealer_play(dealer, deck)

    result = blackjack.settle(player, dealer, effective_bet)
    apply_net(save, effective_bet, result.net)
    _show_table(console, player, dealer, hide_hole=False)
    labels = {
        "blackjack": "BLACKJACK! ",
        "win": "YOU WIN ",
        "lose": "YOU LOSE ",
        "push": "PUSH ",
    }
    if result.net > 0:
        amount = f"+${result.net:,.2f}"
    elif result.net < 0:
        amount = f"-${abs(result.net):,.2f}"
    else:
        amount = "bet returned"
    result_banner(console, result.net > 0, labels[result.outcome] + amount)
    console.print(balance_bar_text(save))
    pause(console)
```

- [ ] **Step 6: Register blackjack in registry.py**

In `gambs/games/registry.py`, inside `all_games()`, add `from gambs.games.blackjack_screen import run_blackjack` next to the other lazy imports, and append `GameEntry("blackjack", "🃏 Blackjack", run_blackjack),` AFTER the roulette entry.

- [ ] **Step 7: Verify**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "import gambs.games.blackjack_screen; from gambs.games.registry import all_games; print([g.id for g in all_games()])"`
Expected: `['crash', 'coinflip', 'dice', 'slots', 'roulette', 'blackjack']`
Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all green.

- [ ] **Step 8: Commit**

```bash
git -C "D:/gambs" add gambs/games/blackjack.py gambs/games/blackjack_screen.py gambs/games/registry.py tests/test_blackjack.py
git -C "D:/gambs" commit -m "feat: add blackjack game"
```

---

### Task 3: Baccarat

**Files:**
- Create: `gambs/games/baccarat.py`, Test `tests/test_baccarat.py`
- Create: `gambs/games/baccarat_screen.py`
- Modify: `gambs/games/registry.py`

Game design: Punto banco. Card values: A=1, 2-9 face value, 10/J/Q/K=0; a hand total is the sum mod 10. Player and Banker each get two cards, then standard third-card drawing rules apply automatically. Bet PLAYER (1:1), BANKER (0.95:1, 5% commission), or TIE (8:1). On a tie, Player/Banker bets push.

- [ ] **Step 1: Write the failing test**

Create `tests/test_baccarat.py`:
```python
from gambs.games.cards import Card
from gambs.games.baccarat import (
    card_value, hand_total, play_round, settle,
    BET_PLAYER, BET_BANKER, BET_TIE,
)


def test_card_value_face_and_ten_are_zero():
    assert card_value(Card("10", "♠")) == 0
    assert card_value(Card("K", "♥")) == 0
    assert card_value(Card("Q", "♦")) == 0


def test_card_value_ace_is_one():
    assert card_value(Card("A", "♣")) == 1


def test_card_value_number_is_face():
    assert card_value(Card("7", "♠")) == 7


def test_hand_total_is_mod_ten():
    assert hand_total([Card("7", "♠"), Card("8", "♥")]) == 5  # 15 -> 5
    assert hand_total([Card("K", "♠"), Card("9", "♥")]) == 9


def test_settle_player_win_pays_even_money():
    player = [Card("9", "♠"), Card("K", "♥")]  # 9
    banker = [Card("7", "♦"), Card("K", "♣")]  # 7
    assert settle(BET_PLAYER, player, banker, 100.0) == 100.0


def test_settle_banker_win_pays_commission():
    player = [Card("7", "♠"), Card("K", "♥")]  # 7
    banker = [Card("9", "♦"), Card("K", "♣")]  # 9
    assert settle(BET_BANKER, player, banker, 100.0) == 95.0


def test_settle_tie_bet_pays_8_to_1():
    player = [Card("5", "♠"), Card("K", "♥")]  # 5
    banker = [Card("5", "♦"), Card("K", "♣")]  # 5
    assert settle(BET_TIE, player, banker, 100.0) == 800.0


def test_settle_player_bet_pushes_on_tie():
    player = [Card("5", "♠"), Card("K", "♥")]  # 5
    banker = [Card("5", "♦"), Card("K", "♣")]  # 5
    assert settle(BET_PLAYER, player, banker, 100.0) == 0.0


def test_settle_player_bet_loses_on_banker_win():
    player = [Card("3", "♠"), Card("K", "♥")]  # 3
    banker = [Card("9", "♦"), Card("K", "♣")]  # 9
    assert settle(BET_PLAYER, player, banker, 100.0) == -100.0


def test_settle_tie_bet_loses_when_not_tie():
    player = [Card("9", "♠"), Card("K", "♥")]  # 9
    banker = [Card("7", "♦"), Card("K", "♣")]  # 7
    assert settle(BET_TIE, player, banker, 100.0) == -100.0


def test_play_round_natural_stops_at_two_cards():
    # deck.pop() draws from the end: player gets the last two, banker the next two.
    # player = 4 + 5 = 9 (natural) -> no third cards drawn.
    deck = [Card("3", "♣"), Card("2", "♦"), Card("5", "♥"), Card("4", "♠")]
    player, banker = play_round(deck)
    assert len(player) == 2 and len(banker) == 2
    assert hand_total(player) == 9


def test_play_round_player_draws_third_on_low_total():
    # player = 2 + 3 = 5 -> draws a third card. banker = 7 -> stands (no player natural).
    # draw order (pop from end): player[0]=2♠, player[1]=3♥, banker[0]=7♦, banker[1]=K♣,
    # then player's third = 9♠.
    deck = [
        Card("9", "♠"),   # player third (drawn last)
        Card("K", "♣"),   # banker[1]
        Card("7", "♦"),   # banker[0]
        Card("3", "♥"),   # player[1]
        Card("2", "♠"),   # player[0]
    ]
    player, banker = play_round(deck)
    assert len(player) == 3
    assert hand_total(player) == 4  # 2 + 3 + 9 = 14 -> 4
    assert len(banker) == 2  # banker total 7 stands
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_baccarat.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.baccarat'`

- [ ] **Step 3: Implement baccarat.py**

Create `gambs/games/baccarat.py`:
```python
"""Baccarat (punto banco): card values, third-card rules, settlement."""

from __future__ import annotations

from gambs.games.cards import Card

BET_PLAYER = "player"
BET_BANKER = "banker"
BET_TIE = "tie"

_ZERO = {"10", "J", "Q", "K"}


def card_value(card: Card) -> int:
    """A=1, 2-9 face value, 10/J/Q/K=0."""
    if card.rank in _ZERO:
        return 0
    if card.rank == "A":
        return 1
    return int(card.rank)


def hand_total(cards: list[Card]) -> int:
    """Baccarat hand total: sum of card values mod 10."""
    return sum(card_value(c) for c in cards) % 10


def play_round(deck: list[Card]) -> tuple[list[Card], list[Card]]:
    """Deal a round per punto banco rules; draw cards with deck.pop().

    Returns (player_cards, banker_cards).
    """
    player = [deck.pop(), deck.pop()]
    banker = [deck.pop(), deck.pop()]
    pt = hand_total(player)
    bt = hand_total(banker)

    # Natural: either side showing 8 or 9 ends the round immediately.
    if pt >= 8 or bt >= 8:
        return player, banker

    player_third: int | None = None
    if pt <= 5:
        third = deck.pop()
        player.append(third)
        player_third = card_value(third)

    if player_third is None:
        # Player stood (6 or 7): banker draws on 0-5, stands on 6-7.
        if bt <= 5:
            banker.append(deck.pop())
    else:
        if bt <= 2:
            banker.append(deck.pop())
        elif bt == 3 and player_third != 8:
            banker.append(deck.pop())
        elif bt == 4 and player_third in (2, 3, 4, 5, 6, 7):
            banker.append(deck.pop())
        elif bt == 5 and player_third in (4, 5, 6, 7):
            banker.append(deck.pop())
        elif bt == 6 and player_third in (6, 7):
            banker.append(deck.pop())
        # bt == 7: banker stands.

    return player, banker


def settle(bet_type: str, player: list[Card], banker: list[Card], bet: float) -> float:
    """Net result. PLAYER 1:1, BANKER 0.95:1 (commission), TIE 8:1.

    Player/Banker bets push on a tie; a Tie bet loses when it is not a tie.
    """
    pt = hand_total(player)
    bt = hand_total(banker)
    if pt == bt:
        if bet_type == BET_TIE:
            return round(bet * 8, 2)
        return 0.0
    if bet_type == BET_TIE:
        return round(-bet, 2)
    winner = BET_PLAYER if pt > bt else BET_BANKER
    if bet_type != winner:
        return round(-bet, 2)
    if winner == BET_BANKER:
        return round(bet * 0.95, 2)
    return round(bet, 2)
```

- [ ] **Step 4: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_baccarat.py`
Expected: PASS (12 passed)

- [ ] **Step 5: Implement baccarat_screen.py**

Create `gambs/games/baccarat_screen.py`:
```python
"""Interactive Baccarat screen."""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import baccarat, cards
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

BACCARAT_TUTORIAL = [
    "Enter a bet amount.",
    "Bet on PLAYER, BANKER, or TIE — closest to 9 wins.",
    "Player pays 1:1, Banker 0.95:1 (5% commission), Tie 8:1.",
    "Third cards are dealt automatically by the rules.",
]

_CHOICES = {"p": baccarat.BET_PLAYER, "b": baccarat.BET_BANKER, "t": baccarat.BET_TIE}


def run_baccarat(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "baccarat", "BACCARAT", BACCARAT_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    console.print("Bet [P]layer  [B]anker  [T]ie: ", end="")
    key = readchar.readkey().lower()
    bet_type = _CHOICES.get(key)
    if bet_type is None:
        return
    console.print(Text("  dealing...", style=config.COLORS["gold"]))
    time.sleep(0.4)
    rng = random.Random()
    deck = cards.shuffle(rng)
    player, banker = baccarat.play_round(deck)
    net = baccarat.settle(bet_type, player, banker, bet)
    apply_net(save, bet, net)
    console.clear()
    console.print(
        Text(
            f"Player: {cards.hand_str(player)}  ({baccarat.hand_total(player)})",
            style=config.COLORS["gold"],
        )
    )
    console.print(
        Text(
            f"Banker: {cards.hand_str(banker)}  ({baccarat.hand_total(banker)})",
            style=config.COLORS["info"],
        )
    )
    if net > 0:
        result_banner(console, True, f"WIN +${net:,.2f}")
    elif net == 0:
        result_banner(console, False, "TIE — bet returned")
    else:
        result_banner(console, False, f"LOSE -${abs(net):,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
```

- [ ] **Step 6: Register baccarat in registry.py**

In `all_games()`, add `from gambs.games.baccarat_screen import run_baccarat` and append `GameEntry("baccarat", "🎴 Baccarat", run_baccarat),` AFTER the blackjack entry.

- [ ] **Step 7: Verify**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "from gambs.games.registry import all_games; print([g.id for g in all_games()])"`
Expected: `['crash', 'coinflip', 'dice', 'slots', 'roulette', 'blackjack', 'baccarat']`
Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all green.

- [ ] **Step 8: Commit**

```bash
git -C "D:/gambs" add gambs/games/baccarat.py gambs/games/baccarat_screen.py gambs/games/registry.py tests/test_baccarat.py
git -C "D:/gambs" commit -m "feat: add baccarat game"
```

---

### Task 4: Video Poker (Jacks or Better)

**Files:**
- Create: `gambs/games/poker.py`, Test `tests/test_poker.py`
- Create: `gambs/games/poker_screen.py`
- Modify: `gambs/games/registry.py`

Game design: 5-card draw. Deal 5, player holds any subset, redraws the rest, then the final hand is paid per a Jacks-or-Better paytable. `settle` returns net profit: a paying hand returns `bet * mult` (e.g. Jacks or Better = even money, net +bet), a non-paying hand loses the bet.

- [ ] **Step 1: Write the failing test**

Create `tests/test_poker.py`:
```python
from gambs.games.cards import Card
from gambs.games.poker import PAYTABLE, evaluate, deal, redraw, settle


def test_royal_flush():
    hand = [Card("10", "♠"), Card("J", "♠"), Card("Q", "♠"), Card("K", "♠"), Card("A", "♠")]
    assert evaluate(hand) == "royal_flush"


def test_straight_flush():
    hand = [Card("5", "♥"), Card("6", "♥"), Card("7", "♥"), Card("8", "♥"), Card("9", "♥")]
    assert evaluate(hand) == "straight_flush"


def test_four_of_a_kind():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("9", "♦"), Card("9", "♣"), Card("2", "♠")]
    assert evaluate(hand) == "four_kind"


def test_full_house():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("9", "♦"), Card("2", "♣"), Card("2", "♠")]
    assert evaluate(hand) == "full_house"


def test_flush():
    hand = [Card("2", "♠"), Card("5", "♠"), Card("8", "♠"), Card("J", "♠"), Card("K", "♠")]
    assert evaluate(hand) == "flush"


def test_straight():
    hand = [Card("4", "♠"), Card("5", "♥"), Card("6", "♦"), Card("7", "♣"), Card("8", "♠")]
    assert evaluate(hand) == "straight"


def test_wheel_straight_ace_low():
    hand = [Card("A", "♠"), Card("2", "♥"), Card("3", "♦"), Card("4", "♣"), Card("5", "♠")]
    assert evaluate(hand) == "straight"


def test_three_of_a_kind():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("9", "♦"), Card("2", "♣"), Card("5", "♠")]
    assert evaluate(hand) == "three_kind"


def test_two_pair():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("2", "♦"), Card("2", "♣"), Card("5", "♠")]
    assert evaluate(hand) == "two_pair"


def test_jacks_or_better():
    hand = [Card("J", "♠"), Card("J", "♥"), Card("2", "♦"), Card("5", "♣"), Card("8", "♠")]
    assert evaluate(hand) == "jacks_or_better"


def test_low_pair_is_nothing():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("2", "♦"), Card("5", "♣"), Card("8", "♠")]
    assert evaluate(hand) == "nothing"


def test_high_card_is_nothing():
    hand = [Card("2", "♠"), Card("5", "♥"), Card("8", "♦"), Card("J", "♣"), Card("K", "♠")]
    assert evaluate(hand) == "nothing"


def test_settle_royal_flush_pays_800x():
    assert settle("royal_flush", 5.0) == 4000.0


def test_settle_jacks_or_better_is_even_money():
    assert settle("jacks_or_better", 10.0) == 10.0


def test_settle_nothing_loses_bet():
    assert settle("nothing", 10.0) == -10.0


def test_deal_takes_five_cards_off_the_deck():
    deck = [Card(r, "♠") for r in ["2", "3", "4", "5", "6", "7"]]
    hand = deal(deck)
    assert len(hand) == 5
    assert len(deck) == 1


def test_redraw_keeps_held_replaces_rest():
    hand = [Card("A", "♠"), Card("2", "♥"), Card("3", "♦"), Card("4", "♣"), Card("5", "♠")]
    deck = [Card("K", "♦"), Card("Q", "♦")]  # two replacements (popped from end)
    result = redraw(hand, {0, 1, 2}, deck)
    assert result[0] == Card("A", "♠")
    assert result[1] == Card("2", "♥")
    assert result[2] == Card("3", "♦")
    assert result[3] == Card("Q", "♦")  # first pop
    assert result[4] == Card("K", "♦")  # second pop


def test_paytable_has_all_categories():
    expected = {
        "royal_flush", "straight_flush", "four_kind", "full_house", "flush",
        "straight", "three_kind", "two_pair", "jacks_or_better", "nothing",
    }
    assert set(PAYTABLE) == expected
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_poker.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gambs.games.poker'`

- [ ] **Step 3: Implement poker.py**

Create `gambs/games/poker.py`:
```python
"""Video Poker (Jacks or Better): hand evaluation, draw, paytable, settlement."""

from __future__ import annotations

from collections import Counter

from gambs.games.cards import Card

# Net-profit multipliers per unit bet. "nothing" loses the bet.
PAYTABLE = {
    "royal_flush": 800,
    "straight_flush": 50,
    "four_kind": 25,
    "full_house": 9,
    "flush": 6,
    "straight": 4,
    "three_kind": 3,
    "two_pair": 2,
    "jacks_or_better": 1,
    "nothing": 0,
}

_ORDER = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14,
}


def _is_straight(values: list[int]) -> bool:
    """True if five distinct ranks form a run (ace high or the A-2-3-4-5 wheel)."""
    unique = sorted(set(values))
    if len(unique) != 5:
        return False
    if unique[-1] - unique[0] == 4:
        return True
    return unique == [2, 3, 4, 5, 14]


def evaluate(cards: list[Card]) -> str:
    """Return the paytable category for a 5-card hand."""
    counts = Counter(card.rank for card in cards)
    count_pattern = sorted(counts.values(), reverse=True)
    values = sorted(_ORDER[card.rank] for card in cards)
    is_flush = len({card.suit for card in cards}) == 1
    is_straight = _is_straight(values)

    if is_straight and is_flush:
        if set(values) == {10, 11, 12, 13, 14}:
            return "royal_flush"
        return "straight_flush"
    if count_pattern == [4, 1]:
        return "four_kind"
    if count_pattern == [3, 2]:
        return "full_house"
    if is_flush:
        return "flush"
    if is_straight:
        return "straight"
    if count_pattern == [3, 1, 1]:
        return "three_kind"
    if count_pattern == [2, 2, 1]:
        return "two_pair"
    if count_pattern[0] == 2:
        pair_rank = next(rank for rank, ct in counts.items() if ct == 2)
        if _ORDER[pair_rank] >= 11:  # J, Q, K, A
            return "jacks_or_better"
    return "nothing"


def deal(deck: list[Card]) -> list[Card]:
    """Draw the opening five cards from the deck."""
    return [deck.pop() for _ in range(5)]


def redraw(hand: list[Card], holds: set[int], deck: list[Card]) -> list[Card]:
    """Return a new hand keeping held indices, replacing the rest from the deck."""
    return [card if i in holds else deck.pop() for i, card in enumerate(hand)]


def settle(rank: str, bet: float) -> float:
    """Net profit for a final hand: bet * paytable multiplier, or -bet if it pays 0."""
    mult = PAYTABLE[rank]
    if mult == 0:
        return round(-bet, 2)
    return round(bet * mult, 2)
```

- [ ] **Step 4: Run it — expect PASS**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest tests/test_poker.py`
Expected: PASS (18 passed)

- [ ] **Step 5: Implement poker_screen.py**

Create `gambs/games/poker_screen.py`:
```python
"""Interactive Video Poker screen."""

from __future__ import annotations

import random

from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import cards, poker
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

POKER_TUTORIAL = [
    "Enter a bet amount.",
    "You are dealt five cards. Choose which to keep, then redraw the rest.",
    "Type the positions to HOLD (e.g. 135) and press Enter.",
    "A pair of Jacks or better pays; a Royal Flush pays 800x.",
]

_RANK_LABELS = {
    "royal_flush": "ROYAL FLUSH",
    "straight_flush": "STRAIGHT FLUSH",
    "four_kind": "FOUR OF A KIND",
    "full_house": "FULL HOUSE",
    "flush": "FLUSH",
    "straight": "STRAIGHT",
    "three_kind": "THREE OF A KIND",
    "two_pair": "TWO PAIR",
    "jacks_or_better": "JACKS OR BETTER",
    "nothing": "NO WIN",
}


def _show_hand(console: Console, hand) -> None:
    positions = "   ".join(f"[{i + 1}]" for i in range(5))
    cards_line = "    ".join(cards.card_str(card) for card in hand)
    console.print(Text(f"  {positions}", style="dim"))
    console.print(Text(f"   {cards_line}", style=config.COLORS["gold"]))


def run_poker(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "poker", "VIDEO POKER", POKER_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    rng = random.Random()
    deck = cards.shuffle(rng)
    hand = poker.deal(deck)
    console.clear()
    _show_hand(console, hand)
    console.print("Hold which positions? (e.g. 135, blank = none): ", end="")
    raw = input().strip()
    holds = {int(ch) - 1 for ch in raw if ch in "12345"}
    hand = poker.redraw(hand, holds, deck)
    rank = poker.evaluate(hand)
    net = poker.settle(rank, bet)
    apply_net(save, bet, net)
    console.clear()
    _show_hand(console, hand)
    label = _RANK_LABELS[rank]
    if net > 0:
        result_banner(console, True, f"{label}  +${net:,.2f}")
    else:
        result_banner(console, False, f"{label}  -${abs(net):,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
```

- [ ] **Step 6: Register poker in registry.py**

In `all_games()`, add `from gambs.games.poker_screen import run_poker` and append `GameEntry("poker", "♠ Video Poker", run_poker),` AFTER the baccarat entry. The final list must be exactly eight entries in order: crash, coinflip, dice, slots, roulette, blackjack, baccarat, poker.

- [ ] **Step 7: Verify full suite**

Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "from gambs.games.registry import all_games; print([g.id for g in all_games()])"`
Expected: `['crash', 'coinflip', 'dice', 'slots', 'roulette', 'blackjack', 'baccarat', 'poker']`
Run: `& "D:/gambs/.venv/Scripts/python.exe" -c "import gambs.main; print('ok')"`
Expected: `ok`
Run: `& "D:/gambs/.venv/Scripts/python.exe" -m pytest "D:/gambs"`
Expected: all green, no skips.

- [ ] **Step 8: Commit**

```bash
git -C "D:/gambs" add gambs/games/poker.py gambs/games/poker_screen.py gambs/games/registry.py tests/test_poker.py
git -C "D:/gambs" commit -m "feat: add video poker game"
```

---

## Definition of Done (Plan 3)

- [ ] GAMBLE selector lists all eight games (keys 1-8), including Blackjack, Baccarat, Video Poker.
- [ ] Each new game is playable: tutorial (first time) → bet → play → result → balance updated → back to selector.
- [ ] All pure logic (`cards`, `blackjack`, `baccarat`, `poker`) is unit-tested; full suite green with no skips.
- [ ] Save persists after each game round (handled by the existing selector loop).
- [ ] No `Co-Authored-By` trailer in any commit.

## Manual smoke test (human, real terminal)

```powershell
cd D:\gambs
& "D:/gambs/.venv/Scripts/python.exe" -m gambs.main
```
Press `G` → selector. Play `6` (Blackjack: try Hit/Stand/Double), `7` (Baccarat: Player/Banker/Tie), `8` (Video Poker: hold + redraw). Confirm bet/result/balance work and ESC returns to the main menu.

## Roadmap (remaining)

- **Plan 4 — Earn Mode:** Typing Heist, Terminal Trading, Bounty Jobs.
- **Plan 5 — Economy:** Item Shop, VIP leveling/prestige, Cosmetics, global difficulty scaling.
- **Deferred polish:** Blackjack split & insurance; multi-bet Roulette/Baccarat.
