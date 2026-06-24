import random

from gambs import config
from gambs.items_effects import lucky_rescue, insurance_refund


def test_lucky_rescue_converts_loss_when_roll_hits():
    rng = random.Random()
    rng.random = lambda: 0.0  # < buff -> rescue
    assert lucky_rescue(-50.0, 50.0, rng, config.LUCKY_CHARM_BUFF) == 50.0


def test_lucky_rescue_leaves_loss_when_roll_misses():
    rng = random.Random()
    rng.random = lambda: 0.99  # >= buff -> no rescue
    assert lucky_rescue(-50.0, 50.0, rng, config.LUCKY_CHARM_BUFF) == -50.0


def test_lucky_rescue_never_touches_a_win_or_push():
    rng = random.Random()
    rng.random = lambda: 0.0
    assert lucky_rescue(80.0, 50.0, rng, config.LUCKY_CHARM_BUFF) == 80.0
    assert lucky_rescue(0.0, 50.0, rng, config.LUCKY_CHARM_BUFF) == 0.0


def test_insurance_refund_is_half_the_bet():
    assert insurance_refund(200.0) == 100.0
    assert insurance_refund(0.0) == 0.0
