"""Shared outcome application: update balance and stats from a net result."""

from __future__ import annotations

from gambs.save import SaveData
from gambs.vip import activity_xp, add_xp


def apply_net(save: SaveData, bet: float, net: float) -> None:
    """Apply one round's net result to the player's balance and stats.

    `net` is profit (positive), loss (negative), or push (0.0). On a win,
    `total_won` accumulates the gross return (stake + profit) to mirror the
    crash game's accounting. Every wager also grants VIP XP.
    """
    save.balance = round(save.balance + net, 2)
    save.stats.total_wagered += bet
    save.stats.games_played += 1
    if net > 0:
        save.stats.total_won += round(bet + net, 2)
    add_xp(save, activity_xp(bet))
