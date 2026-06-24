from gambs.difficulty import (
    min_bet_for,
    bounty_tier_unlocked,
    vip_volatility_bonus,
)


def test_min_bet_rises_with_vip_level():
    assert min_bet_for(1) == 1.0
    assert min_bet_for(2) == 1.0
    assert min_bet_for(3) == 10.0
    assert min_bet_for(4) == 10.0
    assert min_bet_for(5) == 25.0
    assert min_bet_for(10) == 100.0


def test_min_bet_is_monotonic_non_decreasing():
    levels = [min_bet_for(l) for l in range(1, 11)]
    assert levels == sorted(levels)


def test_low_and_medium_bounty_always_unlocked():
    for level in (1, 5, 10):
        assert bounty_tier_unlocked("LOW", level) is True
        assert bounty_tier_unlocked("MEDIUM", level) is True


def test_high_bounty_unlocks_at_vip_3():
    assert bounty_tier_unlocked("HIGH", 1) is False
    assert bounty_tier_unlocked("HIGH", 2) is False
    assert bounty_tier_unlocked("HIGH", 3) is True
    assert bounty_tier_unlocked("HIGH", 9) is True


def test_vip_volatility_bonus_grows_with_level():
    assert vip_volatility_bonus(1) == 0.0
    assert vip_volatility_bonus(5) > vip_volatility_bonus(2)
    assert vip_volatility_bonus(10) > vip_volatility_bonus(5)
