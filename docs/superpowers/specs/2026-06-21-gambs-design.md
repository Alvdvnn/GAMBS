# GAMBS — Terminal Game Station Design Spec
**Date:** 2026-06-21  
**Stack:** Python + Rich library  
**Status:** Approved

---

## Overview

GAMBS is an addictive terminal-based gambling game station with clean ASCII UI/UX. Players gamble in **Gamble Mode** and recover/earn money through skill-based **Earn Mode** mini-games. Money is spent in an **Item Shop**, drives a **VIP Level** progression, and buys **Cosmetics**. Balance and progression persist across sessions via local JSON save file. The whole system is balanced so the house edge stays constant and items help without guaranteeing wins.

---

## 1. Architecture

### File Structure

```
gambs/
├── main.py                  # entry point, boots splash screen
├── config.py                # constants, color theme, settings
├── save.py                  # persistent balance read/write (JSON)
├── ui/
│   ├── splash.py            # slot machine ASCII intro animation
│   ├── menu.py              # main menu & navigation
│   └── components.py        # shared UI blocks (balance bar, headers)
├── games/
│   ├── crash.py
│   ├── blackjack.py
│   ├── slots.py
│   ├── poker.py
│   ├── roulette.py
│   ├── dice.py
│   ├── coinflip.py
│   └── baccarat.py
├── earn/
│   ├── typing_heist.py
│   ├── trading.py
│   └── bounty.py
├── economy/
│   ├── shop.py              # item shop UI + purchase logic
│   ├── items.py             # item definitions + active-effect engine
│   ├── vip.py               # XP, level-up, privileges & challenges
│   └── cosmetics.py         # theme/skin unlocks (vanity only)
└── data/
    ├── save.json            # balance + stats + tutorial + economy state
    ├── bounty_jobs.json     # job definitions for Bounty Jobs
    ├── items.json           # item catalog (price, effect, charges)
    └── cosmetics.json       # cosmetic catalog (price, theme data)
```

### Tech Stack

- **Python 3.10+**
- **rich** — panels, tables, colors, Live display, progress bars
- **readchar** — raw keyboard input (no Enter required)
- **time / threading** — animation timers for Crash Game and demos

---

## 2. Navigation Flow

```
python main.py
    ↓
SPLASH SCREEN — slot reels spin one by one → G A M B S revealed
    ↓ press any key
MAIN MENU
    ├── [G] GAMBLE MODE → Game Selector → Game Screen → [ESC] back
    ├── [E] EARN MODE   → Earn Selector → Mini-game  → reward → wallet
    ├── [P] SHOP        → Item Shop + Cosmetics → purchase → save
    ├── [V] VIP         → Level, XP progress, privileges, prestige
    ├── [S] STATS       → win/loss record, net P/L, best multiplier
    └── [Q] QUIT
```

Always-visible balance bar across all screens:
```
♠ GAMBS   💰 $1,250.00   ⭐ VIP 4 (320/500 XP)   [G]amble [E]arn sho[P] [V]IP [S]tats [Q]uit
```

---

## 3. Splash Screen

- **Style:** Slot machine with 5 reels (G, A, M, B, S)
- **Animation:** Each reel spins (random characters scrolling) then "clicks" into position one by one, left to right
- **Colors:** Each letter different neon color (G=green, A=magenta, M=cyan, B=yellow, S=orange)
- **Font:** Big block ASCII (figlet-style)
- **After reveal:** Subtitle fades in → "Press any key to start"

---

## 4. Visual Theme

- **Background:** Near-black (`#0a0a0f`)
- **Primary accent:** Gold (`#ffd700`)
- **Gamble mode color:** Orange (`#ff6600`)
- **Earn mode color:** Magenta (`#ff00ff`)
- **Success:** Green (`#00ff41`)
- **Danger/loss:** Red (`#ff4444`)
- **Info:** Cyan (`#00ffff`)
- **Border style:** Rich panel boxes + box-drawing characters (`╔═╗║╚╝`)

---

## 5. Persistent Save

**File:** `data/save.json`

```json
{
  "balance": 1250.00,
  "tutorial_seen": ["crash", "blackjack", "slots"],
  "vip": {
    "level": 4,
    "xp": 320,
    "prestige": 0,
    "luck_buff": 0.0
  },
  "inventory": [
    { "item_id": "lucky_charm", "charges": 2 },
    { "item_id": "insurance_card", "charges": 1 }
  ],
  "cosmetics": {
    "owned": ["default", "neon_cyber"],
    "active": "neon_cyber"
  },
  "stats": {
    "total_wagered": 5000,
    "total_won": 3750,
    "games_played": 42,
    "best_crash_multiplier": 14.2,
    "bounty_jobs_completed": 7
  },
  "created_at": "2026-06-21",
  "last_played": "2026-06-21"
}
```

- Starting balance: **$1,000**
- Bankruptcy = balance reaches $0 → game over screen → balance resets to $1,000, all stats preserved
- No safety net — hitting $0 is a meaningful event, not a soft reset

---

## 6. Tutorial System

Shown automatically before entering a game for the first time per save file.

**Flow:**
1. **Phase 1 — Explanation** (typewriter effect, ~2s): Brief how-to-play text
2. **Phase 2 — Animated Demo** (~3–5s): Auto-plays a demo round highlighting key actions
3. **Phase 3 — Prompt:** `[P] Play   [R] Replay demo   [D] Don't show again`

**`[D]` disables tutorial permanently** for that game — stored in `tutorial_seen` array in `save.json`.

**Demo rules:**
- Slots demo always shows jackpot (777) for maximum first impression
- Crash demo shows cashout at 3.5x then a subsequent crash at 1.2x
- Blackjack demo plays one full hand from deal to result
- Typing Heist demo auto-types with a visible cursor

---

## 7. Gamble Mode — Game Specs

### 🚀 Crash Game
- Multiplier starts at 1.00x, rises continuously
- Crash point determined by RNG seed before round starts
- Player presses `[C]` to cashout anytime
- Animated: multiplier counter updates every 100ms, ASCII rocket moves right
- No cashout before crash = bet lost entirely
- Min bet: $1 | Max: all-in

### 🃏 Blackjack
- Standard rules: Player vs Dealer
- Actions: `[H]`it / `[S]`tand / `[D]`ouble / `[P]`split
- Dealer hits until 17
- Blackjack pays 3:2
- ASCII card display with suit symbols

### 🎰 Slots
- 3-reel slot machine
- Symbols: 7 BAR ♦ ♣ ♥ ♠ WILD
- Reel spin animation (characters flash) → stop one by one
- Win table displayed on side panel

### ♠ Poker (Video Poker)
- 5-card draw format
- Player selects cards to hold (`[1]`-`[5]` toggle), draws rest
- Paytable: Royal Flush down to Jacks or Better

### 🎡 Roulette
- European single-zero (0–36)
- Bet types: single number, red/black, odd/even, dozen, column
- Multiple bets per round allowed
- ASCII wheel spin animation before reveal

### 🎲 Dice
- Roll 2 dice
- Bet on: total value, over/under 7, specific combo
- ASCII dice face display

### 🪙 Coin Flip
- Heads or Tails, 50/50
- ASCII coin flip animation
- Streak counter shown for added tension

### 🎴 Baccarat
- Bet: Player / Banker / Tie
- Cards dealt automatically after bet
- Banker pays 0.95:1 (5% commission), Tie pays 8:1

---

## 8. Earn Mode — Mini-game Specs

### ⌨ Typing Heist
- Words/codes appear on screen, player types them within a timer
- Reward = base pay × accuracy multiplier × speed bonus
- Difficulty scales with player balance (higher balance = harder words = higher pay)
- Reward range: $50–$500 per session

### 📈 Terminal Trading
- 4 virtual stocks: LUCK, CHIP, DICE, RISK
- Prices update every 3 seconds via random walk algorithm
- Session max: 5 minutes, then market closes — must cashout
- Player can profit or lose depending on buy/sell timing
- Loss capped at amount invested in that session — balance cannot go negative from trading
- Reward: unlimited upside, downside capped at session buy-in

### 🎯 Bounty Jobs
- Job board with 3 tiers: LOW ($100–300), MEDIUM ($400–800), HIGH ($1,000–2,000)
- Each job: 2–4 decision points with branching outcomes
- Failure = 2-minute cooldown, no money lost
- Job content defined in `data/bounty_jobs.json` for easy content expansion

---

## 9. Economy — Spending Money

### 🛒 Item Shop

Consumable items that improve odds without guaranteeing wins. Defined in `data/items.json`.

| Item | Effect | Charges | Indicative Price |
|------|--------|---------|------------------|
| Lucky Charm | +10% win chance on Coin Flip / Dice for next N rounds | 3 | $400 |
| Insurance Card | If Crash busts, refund 50% of bet | 1 | $600 |
| Vault Key | Unlock a HIGH-tier Bounty Job, skip cooldown once | 1 | $800 |
| Market Intel | Reveal next price tick trend in Terminal Trading | 2 | $500 |

**Fairness rules:**
- All items are **consumable** (1–3 charges), never permanent buffs
- Max odds improvement from any item: **+10%** — no guaranteed wins
- Only **one item effect active at a time** — effects do not stack
- Items priced high relative to earn rate, so acquiring them takes real effort
- House edge on base games is **never** modified by items

### ⭐ VIP Level System

XP earned from every gamble and earn activity. Higher level = new privileges balanced by new challenges.

| Level | Privilege | Balancing Challenge |
|-------|-----------|---------------------|
| 1–2 | Access all base games | Normal |
| 3–4 | Unlock HIGH Bounty, higher bet limit | Minimum bet rises — no more $1 bets |
| 5–6 | VIP Room access (higher-payout variants) | VIP Crash is more volatile (busts earlier more often) |
| 7–9 | Cosmetic themes unlock | Bounty Jobs gain more decision points |
| 10 | Prestige: reset to Level 1 | Gain permanent +2% luck buff, but progression restarts |

- Prestige is repeatable; each prestige adds a small stacking `luck_buff` (cap defined in `config.py`, e.g. +10% max)
- Privileges and challenges always introduced together so power gain is offset

### 🎨 Cosmetics

- Purchasable terminal themes: colors, border styles, ASCII font variants
- **Zero gameplay impact** — pure vanity
- Owned cosmetics stored in save; one active at a time

### ⚖️ Global Difficulty Scaling

- Higher player balance → Typing Heist words get harder (and pay more)
- Higher VIP level → Terminal Trading market gets more volatile
- **House edge stays constant** across all levels and balances — casino advantage never shifts
- Result: every reward is matched by added challenge, keeping the game fair and replayable

---

## 10. Stats Screen

Displays:
- Current balance
- Total wagered / total won / net P/L
- Games played (per game breakdown)
- Best Crash multiplier ever
- Bounty jobs completed / success rate
- VIP level / prestige count
- Current session duration (runtime, not persisted)

---

## 11. Out of Scope (v1)

- Multiplayer / leaderboards
- Sound effects
- Real money integration
- Mobile / web port
- Achievements / badges
- Underground Bank (deposit interest + loans/debt) — deferred to v2
