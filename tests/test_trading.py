import random

from gambs import config
from gambs.earn.trading import (
    volatility_for_balance,
    initial_prices,
    step_price,
    step_prices,
)


def test_volatility_rises_with_balance():
    assert volatility_for_balance(500) < volatility_for_balance(3000)
    assert volatility_for_balance(3000) < volatility_for_balance(10000)
    assert volatility_for_balance(10000) < volatility_for_balance(50000)


def test_initial_prices_cover_all_stocks_at_start_price():
    prices = initial_prices()
    assert set(prices) == set(config.TRADING_STOCKS)
    assert all(p == config.TRADING_START_PRICE for p in prices.values())


def test_step_price_is_deterministic_for_a_seed():
    a = step_price(random.Random(7), 100.0, 0.1)
    b = step_price(random.Random(7), 100.0, 0.1)
    assert a == b


def test_step_price_never_below_min():
    rng = random.Random(1)
    price = 100.0
    for _ in range(500):
        price = step_price(rng, price, 0.5)
        assert price >= config.TRADING_MIN_PRICE


def test_step_prices_steps_every_stock():
    prices = initial_prices()
    stepped = step_prices(random.Random(0), prices, 0.1)
    assert set(stepped) == set(prices)
    assert stepped is not prices  # returns a new dict
