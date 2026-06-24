from gambs.games.cards import Card
from gambs.games.baccarat import (
    card_value, hand_total, play_round, settle, settle_all,
    BET_PLAYER, BET_BANKER, BET_TIE,
)


def test_settle_all_returns_per_bet_nets():
    player = [Card("9", "♠"), Card("7", "♥")]  # total 6
    banker = [Card("5", "♠"), Card("9", "♥")]  # total 4 -> player wins
    nets = settle_all([(BET_PLAYER, 10.0), (BET_TIE, 5.0)], player, banker)
    assert nets == [10.0, -5.0]


def test_card_value_face_and_ten_are_zero():
    assert card_value(Card("10", "♠")) == 0
    assert card_value(Card("K", "♥")) == 0
    assert card_value(Card("Q", "♦")) == 0


def test_card_value_ace_is_one():
    assert card_value(Card("A", "♣")) == 1


def test_card_value_number_is_face():
    assert card_value(Card("7", "♠")) == 7


def test_hand_total_is_mod_ten():
    assert hand_total([Card("7", "♠"), Card("8", "♥")]) == 5  # 15 -> 5
    assert hand_total([Card("K", "♠"), Card("9", "♥")]) == 9


def test_settle_player_win_pays_even_money():
    player = [Card("9", "♠"), Card("K", "♥")]  # 9
    banker = [Card("7", "♦"), Card("K", "♣")]  # 7
    assert settle(BET_PLAYER, player, banker, 100.0) == 100.0


def test_settle_banker_win_pays_commission():
    player = [Card("7", "♠"), Card("K", "♥")]  # 7
    banker = [Card("9", "♦"), Card("K", "♣")]  # 9
    assert settle(BET_BANKER, player, banker, 100.0) == 95.0


def test_settle_tie_bet_pays_8_to_1():
    player = [Card("5", "♠"), Card("K", "♥")]  # 5
    banker = [Card("5", "♦"), Card("K", "♣")]  # 5
    assert settle(BET_TIE, player, banker, 100.0) == 800.0


def test_settle_player_bet_pushes_on_tie():
    player = [Card("5", "♠"), Card("K", "♥")]  # 5
    banker = [Card("5", "♦"), Card("K", "♣")]  # 5
    assert settle(BET_PLAYER, player, banker, 100.0) == 0.0


def test_settle_player_bet_loses_on_banker_win():
    player = [Card("3", "♠"), Card("K", "♥")]  # 3
    banker = [Card("9", "♦"), Card("K", "♣")]  # 9
    assert settle(BET_PLAYER, player, banker, 100.0) == -100.0


def test_settle_tie_bet_loses_when_not_tie():
    player = [Card("9", "♠"), Card("K", "♥")]  # 9
    banker = [Card("7", "♦"), Card("K", "♣")]  # 7
    assert settle(BET_TIE, player, banker, 100.0) == -100.0


def test_play_round_natural_stops_at_two_cards():
    # deck.pop() draws from the end: player gets the last two, banker the next two.
    # player = 4 + 5 = 9 (natural) -> no third cards drawn.
    deck = [Card("3", "♣"), Card("2", "♦"), Card("5", "♥"), Card("4", "♠")]
    player, banker = play_round(deck)
    assert len(player) == 2 and len(banker) == 2
    assert hand_total(player) == 9


def test_play_round_player_draws_third_on_low_total():
    # player = 2 + 3 = 5 -> draws a third card. banker = 7 -> stands (no player natural).
    deck = [
        Card("9", "♠"),   # player third (drawn last)
        Card("K", "♣"),   # banker[1]
        Card("7", "♦"),   # banker[0]
        Card("3", "♥"),   # player[1]
        Card("2", "♠"),   # player[0]
    ]
    player, banker = play_round(deck)
    assert len(player) == 3
    assert hand_total(player) == 4  # 2 + 3 + 9 = 14 -> 4
    assert len(banker) == 2  # banker total 7 stands
