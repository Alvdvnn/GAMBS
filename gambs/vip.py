"""VIP progression pure logic: XP accrual, leveling, and prestige.

No RNG or rendering. Mutating helpers (`add_xp`, `do_prestige`) change only
the SaveData passed in. XP is awarded for every gamble and earn activity.
"""

from __future__ import annotations

from gambs import config
from gambs.save import SaveData

# Privilege / challenge text per level band, keyed by the band's lowest level.
_PRIVILEGE_BANDS: list[tuple[int, str, str]] = [
    (1, "Access all base games", "Normal play"),
    (3, "HIGH Bounty unlocked · higher bet limit", "Minimum bet rises"),
    (5, "VIP Room: higher-payout variants", "VIP Crash busts earlier"),
    (7, "Cosmetic themes unlock", "Bounty jobs gain decision points"),
    (10, "Prestige available", "Progression restarts on prestige"),
]


def activity_xp(amount: float) -> int:
    """XP granted for an activity that wagered or earned `amount` dollars."""
    return max(1, int(amount * config.XP_PER_DOLLAR))


def add_xp(save: SaveData, amount: int) -> None:
    """Add XP, rolling over level-ups; pin the bar full at the max level."""
    vip = save.vip
    vip.xp += amount
    threshold = config.VIP_XP_PER_LEVEL
    while vip.level < config.MAX_VIP_LEVEL and vip.xp >= threshold:
        vip.xp -= threshold
        vip.level += 1
    if vip.level >= config.MAX_VIP_LEVEL and vip.xp > threshold:
        vip.xp = threshold


def xp_to_next(save: SaveData) -> int:
    """XP remaining until the next level."""
    return max(0, config.VIP_XP_PER_LEVEL - save.vip.xp)


def can_prestige(save: SaveData) -> bool:
    """True once the player has reached the max VIP level."""
    return save.vip.level >= config.MAX_VIP_LEVEL


def do_prestige(save: SaveData) -> bool:
    """Reset to level 1, bump prestige, and add a capped luck buff.

    Returns False without mutating if the player is below the max level.
    """
    if not can_prestige(save):
        return False
    vip = save.vip
    vip.level = 1
    vip.xp = 0
    vip.prestige += 1
    vip.luck_buff = round(
        min(config.MAX_LUCK_BUFF, vip.luck_buff + config.PRESTIGE_LUCK_STEP), 4
    )
    return True


def privileges_for(level: int) -> tuple[str, str]:
    """Return the (privilege, challenge) text active at this level."""
    active = _PRIVILEGE_BANDS[0]
    for band in _PRIVILEGE_BANDS:
        if level >= band[0]:
            active = band
    return active[1], active[2]


def privilege_bands() -> list[tuple[int, str, str]]:
    """The full (min_level, privilege, challenge) table for display."""
    return list(_PRIVILEGE_BANDS)
