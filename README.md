<div align="center">

```
   ██████╗  █████╗ ███╗   ███╗██████╗ ███████╗
  ██╔════╝ ██╔══██╗████╗ ████║██╔══██╗██╔════╝
  ██║  ███╗███████║██╔████╔██║██████╔╝███████╗
  ██║   ██║██╔══██║██║╚██╔╝██║██╔══██╗╚════██║
  ╚██████╔╝██║  ██║██║ ╚═╝ ██║██████╔╝███████║
   ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚═════╝ ╚══════╝
```

### ♠ ♥ A Terminal Game Station for Gamblers ♦ ♣

*Spin the reels. Crack the codes. Chase the multiplier. Go bankrupt with style.*

![Python](https://img.shields.io/badge/python-3.11+-ffd700?style=flat-square&logo=python&logoColor=black)
![Rich](https://img.shields.io/badge/built%20with-rich-ff6600?style=flat-square)
![Tests](https://img.shields.io/badge/tests-251%20passing-00ff41?style=flat-square)
![Edge](https://img.shields.io/badge/house%20edge-balanced-00ffff?style=flat-square)

</div>

---

## 🎰 What is GAMBS?

GAMBS is an **addictive, fully terminal-based gambling arcade** built with Python and
[Rich](https://github.com/Textualize/rich). Eight casino games, three skill-based earn
jobs to claw your money back, an item shop, a VIP progression with prestige, unlockable
cosmetic themes, animated splash reels, per-game tutorials, and a save file that
remembers every win, loss, and bankruptcy.

Every game uses **honest casino math** — RNG is injected and unit-tested, payouts are
documented, and the house edge is deliberately tuned to be *fair but challenging*. No
fake wins, no rigged losses. Just you against the numbers.

---

## ✨ Features

| | |
|---|---|
| 🎲 **8 gamble games** | Crash · Coin Flip · Dice · Slots · Roulette · Blackjack · Baccarat · Video Poker |
| ⌨️ **3 earn jobs** | **Typing Heist** · **Terminal Trading** · **Bounty Jobs** — skill-based ways to claw money back |
| 🛒 **Item Shop** | Lucky Charm, Insurance, Vault Key, Market Intel — consumable buffs that help without rigging |
| ⭐ **VIP + prestige** | Earn XP from every play; level up for privileges matched by challenges, then prestige for luck |
| 🎨 **Cosmetic themes** | Buy and equip terminal palettes (Neon, Monochrome, Vaporwave) — pure vanity |
| 📊 **Stats screen** | Lifetime wagered/won, net P/L, best Crash, bounty success rate, session timer |
| 🪙 **Slot-machine splash** | Five reels spin and lock left-to-right to reveal `G A M B S` |
| 📚 **Built-in tutorials** | Every game explains itself the first time you play it |
| 💾 **Persistent save** | Balance, stats, inventory, VIP, and cosmetics survive across sessions |
| 🧮 **Tested math** | 251 passing tests; pure game logic separated from rendering |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/Alvdvnn/GAMBS.git
cd GAMBS

# 2. Create a virtual environment + install deps
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install rich readchar

# 3. Run it
python -m gambs.main
```

> **Windows note:** run from the project root (`D:\GAMBS` or wherever you cloned it) so the
> `gambs` package is importable.

---

## 🕹️ How to Play

The always-visible balance bar follows you everywhere:

```
♠ GAMBS   💰 $1,250.00   ⭐ VIP 4 (320/500 XP)
```

From the main menu:

```
[G] GAMBLE  →  pick a game (1-8)  →  bet  →  play  →  back with [ESC]
[E] EARN    →  Typing Heist · Terminal Trading · Bounty Jobs
[P] SHOP    →  buy consumable items; [C] for cosmetic themes
[V] VIP     →  level, XP bar, privileges, and prestige
[S] STATS   →  your lifetime record and current session
[Q] QUIT    →  saves and exits
```

---

## 🎲 The Games

| # | Game | How it pays | House edge |
|---|------|-------------|-----------|
| 1 | 🚀 **Crash** | Cash out before the rocket busts; multiplier grows `e^(0.15·t)` | ~3% |
| 2 | 🪙 **Coin Flip** | Heads or tails, even money | 0% (near-fair starter) |
| 3 | 🎲 **Dice** | LOW/HIGH push on 7 (fair); SEVEN pays 4:1 | SEVEN ~16.7% |
| 4 | 🎰 **Slots** | Triple 7s pay 50×, two 7s pay 2×, weighted reels | ~6% |
| 5 | 🎡 **Roulette** | European single-zero; straight 35:1, outside 1:1, **multi-bet** | ~2.7% |
| 6 | 🃏 **Blackjack** | Hit/Stand/Double/**Split**, **insurance** on dealer Ace, blackjack pays 3:2 | <1% |
| 7 | 🎴 **Baccarat** | Player 1:1 · Banker 0.95:1 · Tie 8:1, **multi-bet**, auto third-card rules | ~1.2% |
| 8 | ♠ **Video Poker** | 5-card draw, Jacks-or-Better 9/6 paytable, Royal pays 800× | ~0.5% |

### ⌨️ Earn Mode — three ways to recover

Down to your last chips? Earn jobs are skill-based and never cost you real balance —
you only ever walk away with cash (or nothing).

- **Typing Heist** — five code prompts flash; type each fast and accurately.
  `reward = base_pay(tier) × accuracy × speed_bonus` → clamped to $50–$500. Richer
  players face harder codes for bigger payouts.
- **Terminal Trading** — buy and sell four volatile stocks over 20 ticks with virtual
  session capital; keep the profit above your starting stake, floored at $0. Volatility
  rises with your balance and VIP level. (Spend **Market Intel** to peek the next tick.)
- **Bounty Jobs** — branching choose-your-path heists across LOW/MEDIUM/HIGH tiers.
  Failure costs only a cooldown, never money. HIGH unlocks at VIP 3 (or with a **Vault Key**).

---

## 🧱 Project Structure

```
gambs/
├── main.py              # entry point: splash → menu loop → dispatch
├── config.py            # constants, color palette, tunables
├── save.py              # JSON persistence (balance, stats, inventory, VIP, cosmetics)
├── shop.py              # item catalog load + purchase/charge logic (tested)
├── items_effects.py     # pure item-effect helpers: lucky rescue, insurance (tested)
├── vip.py               # XP accrual, leveling, prestige (tested)
├── cosmetics.py         # theme catalog + live palette application (tested)
├── difficulty.py        # VIP gates + difficulty scaling (tested)
├── ui/
│   ├── splash.py        # slot-reel intro animation
│   ├── menu.py          # main menu + routing
│   ├── game_select.py · earn_select.py   # selectors
│   ├── prompts.py       # shared bet/tutorial/result/pause helpers
│   ├── shop_screen.py · cosmetics_screen.py · vip_screen.py · stats_screen.py
│   ├── stats.py         # pure stats row model (tested)
│   └── components.py    # balance bar
├── games/
│   ├── cards.py         # shared Card model, deck, shuffle
│   ├── crash.py · coinflip.py · dice.py · slots.py · roulette.py
│   ├── blackjack.py · baccarat.py · poker.py     # pure logic (tested)
│   ├── outcome.py       # shared net→balance/stats/XP application
│   ├── *_screen.py      # interactive rendering per game
│   └── registry.py      # the single list of playable games
├── earn/
│   ├── typing_heist.py · trading.py · bounty.py        # pure logic (tested)
│   ├── *_screen.py                                     # interactive jobs
│   └── registry.py                                     # earn-job list
└── data/                # items.json · cosmetics.json · bounty_jobs.json · save.json
```

**Design principle:** every game splits **pure logic** (RNG injected, fully unit-tested)
from **interactive rendering** (manual-smoke). That's why the math is trustworthy and the
test suite is fast.

---

## 🧪 Tests

```bash
python -m pytest
```

```
251 passed
```

Pure logic for every game — hand values, payout math, third-card rules, poker hand
evaluation, slot EV, typing rewards — is locked down by tests. Slots even has an
**exact-EV regression test** that keeps the house edge inside a 3–10% band.

---

## 🗺️ Roadmap

- [x] Foundation + Crash game + persistent save
- [x] Game selector + Coin Flip, Dice, Slots, Roulette
- [x] Card games: Blackjack, Baccarat, Video Poker
- [x] **Earn Mode: Typing Heist, Terminal Trading, Bounty Jobs**
- [x] Economy: Item Shop + working item effects
- [x] VIP levels + prestige, with difficulty scaling & privilege gates
- [x] Cosmetic themes (buy + equip, live palette)
- [x] Stats screen
- [x] Blackjack split & insurance · multi-bet Roulette & Baccarat

**v1 feature-complete.** Out of scope (v2+): multiplayer/leaderboards, sound,
real-money, mobile/web port, achievements, Underground Bank.

---

## 🛠️ Built With

- **Python 3.11+**
- **[rich](https://github.com/Textualize/rich)** — panels, colors, live display
- **[readchar](https://github.com/magmax/python-readchar)** — raw single-key input
- **pytest** — the safety net

---

<div align="center">

*Made for the love of the gamble. Bet responsibly — it's only fake money.* ♠

</div>
