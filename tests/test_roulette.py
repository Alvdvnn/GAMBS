import random

from gambs.games.roulette import (
    spin, color, settle,
    BET_STRAIGHT, BET_RED, BET_BLACK, BET_ODD, BET_EVEN, BET_LOW, BET_HIGH,
)


def test_spin_in_range():
    for seed in range(100):
        assert 0 <= spin(random.Random(seed)) <= 36


def test_color_mapping():
    assert color(0) == "green"
    assert color(1) == "red"
    assert color(2) == "black"


def test_straight_hit_pays_35():
    assert settle(BET_STRAIGHT, 17, 17, 10.0) == 350.0


def test_straight_miss_loses():
    assert settle(BET_STRAIGHT, 17, 18, 10.0) == -10.0


def test_straight_on_zero_wins():
    assert settle(BET_STRAIGHT, 0, 0, 10.0) == 350.0  # straight beats the zero short-circuit


def test_red_wins_on_red():
    assert settle(BET_RED, None, 1, 10.0) == 10.0


def test_red_loses_on_black():
    assert settle(BET_RED, None, 2, 10.0) == -10.0


def test_outside_bet_loses_on_zero():
    assert settle(BET_RED, None, 0, 10.0) == -10.0
    assert settle(BET_EVEN, None, 0, 10.0) == -10.0
    assert settle(BET_LOW, None, 0, 10.0) == -10.0


def test_even_and_odd():
    assert settle(BET_EVEN, None, 4, 10.0) == 10.0
    assert settle(BET_ODD, None, 4, 10.0) == -10.0


def test_low_and_high():
    assert settle(BET_LOW, None, 10, 10.0) == 10.0
    assert settle(BET_HIGH, None, 10, 10.0) == -10.0
    assert settle(BET_HIGH, None, 25, 10.0) == 10.0
