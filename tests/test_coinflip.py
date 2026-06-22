import random

from gambs.games.coinflip import flip, settle


def test_flip_returns_only_heads_or_tails():
    for seed in range(50):
        assert flip(random.Random(seed)) in ("H", "T")


def test_flip_is_deterministic_for_a_seed():
    assert flip(random.Random(7)) == flip(random.Random(7))


def test_settle_win_pays_even_money():
    assert settle("H", "H", 100.0) == 100.0


def test_settle_loss_returns_negative_bet():
    assert settle("H", "T", 100.0) == -100.0
