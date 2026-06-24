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
    "[P] splits a matching pair into two hands. If the dealer shows an Ace you",
    "may take Insurance. Dealer hits until 17. A two-card 21 pays 3:2.",
]


def _show_table(console: Console, hands, active_idx, dealer, hide_hole: bool) -> None:
    console.clear()
    if hide_hole:
        dealer_text = f"{cards.card_str(dealer[0])} ??"
    else:
        dealer_text = f"{cards.hand_str(dealer)}  ({blackjack.hand_value(dealer)})"
    console.print(Text(f"Dealer: {dealer_text}", style=config.COLORS["info"]))
    for i, hand in enumerate(hands):
        marker = "> " if (len(hands) > 1 and i == active_idx) else "  "
        label = f"Hand {i + 1}" if len(hands) > 1 else "You"
        console.print(
            Text(
                f"{marker}{label}: {cards.hand_str(hand)}  ({blackjack.hand_value(hand)})",
                style=config.COLORS["gold"],
            )
        )


def _maybe_insurance(console: Console, save: SaveData, dealer, bet: float) -> float:
    """Offer insurance when the dealer shows an Ace. Returns the net side result."""
    if not blackjack.dealer_upcard_is_ace(dealer):
        return 0.0
    ins_bet = round(bet / 2, 2)
    if ins_bet <= 0 or ins_bet > save.balance:
        return 0.0
    console.print(
        Text(f"Dealer shows an Ace. Insurance for ${ins_bet:,.2f}? [Y/N]: ", style=config.COLORS["info"]),
        end="",
    )
    if readchar.readkey().lower() != "y":
        return 0.0
    ins_net = blackjack.insurance_result(dealer, ins_bet)
    save.balance = round(save.balance + ins_net, 2)
    return ins_net


def _play_hand(console, hand, hands, idx, dealer, deck, bet, headroom) -> float:
    """Play one hand to a stand/bust/double. Returns the hand's effective bet.

    `headroom` is the balance still free for a double on this hand.
    """
    effective_bet = bet
    while True:
        _show_table(console, hands, idx, dealer, hide_hole=True)
        can_double = len(hand) == 2 and bet <= headroom
        prompt = "[H]it  [S]tand" + ("  [D]ouble" if can_double else "")
        console.print(prompt + ": ", end="")
        key = readchar.readkey().lower()
        if key == "h":
            hand.append(deck.pop())
            if blackjack.hand_value(hand) > 21:
                return effective_bet
        elif key == "d" and can_double:
            effective_bet = bet * 2
            hand.append(deck.pop())
            return effective_bet
        elif key == "s":
            return effective_bet


def run_blackjack(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "blackjack", "BLACKJACK", BLACKJACK_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    rng = random.Random()
    deck = cards.shuffle(rng)
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]

    ins_net = _maybe_insurance(console, save, dealer, bet)

    # Naturals end the round immediately (no hitting/splitting).
    if blackjack.is_blackjack(player) or blackjack.is_blackjack(dealer):
        result = blackjack.settle(player, dealer, bet)
        apply_net(save, bet, result.net)
        _finish(console, save, [player], dealer, [result], ins_net)
        return

    # Optional split into two hands, each with its own bet.
    hands = [player]
    split = False
    if blackjack.can_split(player) and bet * 2 <= save.balance:
        console.print(Text("Split this pair? [Y/N]: ", style=config.COLORS["info"]), end="")
        if readchar.readkey().lower() == "y":
            split = True
            hands = [[player[0], deck.pop()], [player[1], deck.pop()]]

    committed = bet * len(hands)
    bets = []
    for idx, hand in enumerate(hands):
        headroom = save.balance - committed
        eff = _play_hand(console, hand, hands, idx, dealer, deck, bet, headroom)
        committed += eff - bet  # extra exposure if doubled
        bets.append(eff)

    if any(blackjack.hand_value(h) <= 21 for h in hands):
        blackjack.dealer_play(dealer, deck)

    results = [
        blackjack.settle(hand, dealer, hand_bet, natural=not split)
        for hand, hand_bet in zip(hands, bets)
    ]
    for hand_bet, result in zip(bets, results):
        apply_net(save, hand_bet, result.net)
    _finish(console, save, hands, dealer, results, ins_net)


def _finish(console, save, hands, dealer, results, ins_net) -> None:
    _show_table(console, hands, -1, dealer, hide_hole=False)
    labels = {"blackjack": "BLACKJACK! ", "win": "WIN ", "lose": "LOSE ", "push": "PUSH "}
    total = sum(r.net for r in results) + ins_net
    for i, result in enumerate(results):
        tag = f"Hand {i + 1}: " if len(results) > 1 else ""
        console.print(
            Text(f"  {tag}{labels[result.outcome]}{result.net:+,.2f}", style=config.COLORS["gold"])
        )
    if ins_net:
        console.print(Text(f"  Insurance {ins_net:+,.2f}", style=config.COLORS["info"]))
    sign = f"+${total:,.2f}" if total >= 0 else f"-${abs(total):,.2f}"
    result_banner(console, total > 0, f"Net {sign}")
    console.print(balance_bar_text(save))
    pause(console)
