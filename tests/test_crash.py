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
