import random

from gambs.games.dice import roll, settle, BET_LOW, BET_HIGH, BET_SEVEN


def test_roll_returns_two_dice_in_range():
    for seed in range(50):
        d1, d2 = roll(random.Random(seed))
        assert 1 <= d1 <= 6 and 1 <= d2 <= 6


def test_low_wins_below_seven():
    assert settle(BET_LOW, (2, 3), 100.0) == 100.0   # total 5


def test_low_loses_above_seven():
    assert settle(BET_LOW, (5, 4), 100.0) == -100.0  # total 9


def test_low_pushes_on_seven():
    assert settle(BET_LOW, (3, 4), 100.0) == 0.0     # total 7


def test_high_wins_above_seven():
    assert settle(BET_HIGH, (6, 4), 100.0) == 100.0  # total 10


def test_high_loses_below_seven():
    assert settle(BET_HIGH, (2, 2), 100.0) == -100.0  # total 4


def test_high_pushes_on_seven():
    assert settle(BET_HIGH, (1, 6), 100.0) == 0.0    # total 7


def test_seven_bet_pays_four_to_one():
    assert settle(BET_SEVEN, (3, 4), 100.0) == 400.0


def test_seven_bet_loses_off_seven():
    assert settle(BET_SEVEN, (2, 2), 100.0) == -100.0


def test_unknown_bet_type_raises():
    import pytest
    with pytest.raises(ValueError):
        settle("nope", (1, 1), 100.0)
