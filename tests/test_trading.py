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


from gambs.earn.trading import (
    Portfolio,
    new_portfolio,
    buy,
    sell,
    portfolio_value,
    settle,
)


def test_new_portfolio_holds_capital_and_zero_shares():
    p = new_portfolio(1000.0)
    assert p.cash == 1000.0
    assert all(shares == 0 for shares in p.holdings.values())
    assert set(p.holdings) == set(config.TRADING_STOCKS)


def test_buy_deducts_cash_and_adds_shares():
    p = new_portfolio(1000.0)
    ok = buy(p, "LUCK", 3, {"LUCK": 100.0})
    assert ok is True
    assert p.cash == 700.0
    assert p.holdings["LUCK"] == 3


def test_buy_rejected_when_insufficient_cash():
    p = new_portfolio(100.0)
    ok = buy(p, "LUCK", 5, {"LUCK": 100.0})
    assert ok is False
    assert p.cash == 100.0
    assert p.holdings["LUCK"] == 0


def test_sell_adds_cash_and_removes_shares():
    p = new_portfolio(1000.0)
    buy(p, "LUCK", 3, {"LUCK": 100.0})
    ok = sell(p, "LUCK", 2, {"LUCK": 120.0})
    assert ok is True
    assert p.holdings["LUCK"] == 1
    assert p.cash == 700.0 + 240.0


def test_sell_rejected_when_not_enough_shares():
    p = new_portfolio(1000.0)
    ok = sell(p, "LUCK", 1, {"LUCK": 100.0})
    assert ok is False


def test_portfolio_value_is_cash_plus_holdings():
    p = new_portfolio(1000.0)
    buy(p, "LUCK", 2, {"LUCK": 100.0})  # cash 800, 2 shares
    assert portfolio_value(p, {"LUCK": 150.0}) == 800.0 + 300.0


def test_settle_returns_profit_above_capital():
    p = new_portfolio(1000.0)
    buy(p, "LUCK", 5, {"LUCK": 100.0})  # cash 500, 5 shares
    # 5 shares now worth 200 each = 1000, + 500 cash = 1500 value, capital 1000
    assert settle(p, {"LUCK": 200.0}, 1000.0) == 500.0


def test_settle_floors_at_zero_on_a_loss():
    p = new_portfolio(1000.0)
    buy(p, "LUCK", 5, {"LUCK": 100.0})  # cash 500, 5 shares
    # 5 shares now worth 10 each = 50, + 500 cash = 550 value < 1000 capital
    assert settle(p, {"LUCK": 10.0}, 1000.0) == 0.0
