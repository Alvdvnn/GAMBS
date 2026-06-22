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
