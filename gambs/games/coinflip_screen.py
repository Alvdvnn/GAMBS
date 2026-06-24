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
from gambs.items_effects import lucky_rescue
from gambs.save import SaveData
from gambs.shop import consume_charge, has_charges
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
    rescued = False
    if has_charges(save, "lucky_charm"):
        consume_charge(save, "lucky_charm")
        new_net = lucky_rescue(net, bet, rng, config.LUCKY_CHARM_BUFF)
        rescued = new_net > net
        net = new_net
    apply_net(save, bet, net)
    face = "HEADS" if result == coinflip.HEADS else "TAILS"
    won = net > 0
    sign = "+" if won else "-"
    suffix = "  🍀 Lucky Charm!" if rescued else ""
    result_banner(console, won, f"{face}  {sign}${abs(net):,.2f}{suffix}")
    console.print(balance_bar_text(save))
    pause(console)
