"""Global difficulty scaling and VIP privilege gates (pure helpers).

Every reward is matched by added challenge: minimum bets rise with VIP level,
the HIGH bounty tier unlocks with VIP rank, and Terminal Trading grows more
volatile as the player levels up. The base-game house edge is never touched.
"""

from __future__ import annotations

# (min VIP level, minimum bet) bands — the floor rises as the player ranks up.
_MIN_BET_BANDS: list[tuple[int, float]] = [
    (1, 1.0),
    (3, 10.0),
    (5, 25.0),
    (7, 50.0),
    (10, 100.0),
]

# HIGH-tier bounties unlock at this VIP level (privilege at the 3-4 band).
HIGH_BOUNTY_MIN_VIP: int = 3

# Per-level volatility added to Terminal Trading on top of the balance band.
VIP_VOLATILITY_STEP: float = 0.005


def min_bet_for(vip_level: int) -> float:
    """The minimum allowed bet at this VIP level."""
    floor = _MIN_BET_BANDS[0][1]
    for level, value in _MIN_BET_BANDS:
        if vip_level >= level:
            floor = value
    return floor


def bounty_tier_unlocked(tier: str, vip_level: int) -> bool:
    """Whether a bounty tier is available at this VIP level."""
    if tier == "HIGH":
        return vip_level >= HIGH_BOUNTY_MIN_VIP
    return True


def vip_volatility_bonus(vip_level: int) -> float:
    """Extra Terminal Trading volatility granted by VIP rank."""
    return (vip_level - 1) * VIP_VOLATILITY_STEP
