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
