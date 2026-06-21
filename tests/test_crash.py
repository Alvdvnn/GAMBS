import random

from gambs.games.crash import generate_crash_point


def test_crash_point_is_deterministic_with_seed():
    rng = random.Random(42)
    assert generate_crash_point(rng) == 2.69


def test_crash_point_never_below_one():
    for seed in range(200):
        rng = random.Random(seed)
        assert generate_crash_point(rng) >= 1.0


def test_higher_house_edge_lowers_average_crash():
    low = [generate_crash_point(random.Random(s), house_edge=0.01) for s in range(500)]
    high = [generate_crash_point(random.Random(s), house_edge=0.10) for s in range(500)]
    assert sum(low) / len(low) > sum(high) / len(high)


from gambs.games.crash import multiplier_at, payout


def test_multiplier_starts_at_one():
    assert multiplier_at(0.0) == 1.0


def test_multiplier_grows_over_time():
    assert multiplier_at(10.0, growth=0.15) == 4.48


def test_multiplier_is_monotonic_increasing():
    prev = 0.0
    for t in range(0, 50):
        m = multiplier_at(t * 0.5)
        assert m >= prev
        prev = m


def test_payout_multiplies_bet_by_multiplier():
    assert payout(100.0, 2.5) == 250.0


def test_payout_rounds_to_cents():
    assert payout(33.33, 1.5) == 50.0
