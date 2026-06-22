import random

from gambs.games.slots import SYMBOLS, spin, settle


def test_spin_returns_three_valid_symbols():
    for seed in range(50):
        reels = spin(random.Random(seed))
        assert len(reels) == 3
        for s in reels:
            assert s in SYMBOLS


def test_three_sevens_pays_50x():
    assert settle(("7", "7", "7"), 10.0) == 500.0


def test_three_bars_pays_20x():
    assert settle(("BAR", "BAR", "BAR"), 10.0) == 200.0


def test_three_of_a_kind_pays_5x():
    assert settle(("♥", "♥", "♥"), 10.0) == 50.0


def test_two_sevens_pays_2x():
    assert settle(("7", "7", "♠"), 10.0) == 20.0


def test_no_match_loses():
    assert settle(("♦", "♣", "♥"), 10.0) == -10.0
