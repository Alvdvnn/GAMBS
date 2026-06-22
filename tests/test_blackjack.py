from gambs.games.cards import Card
from gambs.games.blackjack import (
    hand_value, is_blackjack, dealer_play, settle, BlackjackResult,
)


def test_hand_value_no_ace():
    assert hand_value([Card("10", "♠"), Card("7", "♥")]) == 17


def test_face_cards_are_ten():
    assert hand_value([Card("K", "♠"), Card("Q", "♥")]) == 20


def test_ace_counts_eleven_when_safe():
    assert hand_value([Card("A", "♠"), Card("9", "♥")]) == 20


def test_ace_reduces_to_one_to_avoid_bust():
    assert hand_value([Card("A", "♠"), Card("9", "♥"), Card("5", "♣")]) == 15


def test_two_aces_one_stays_eleven():
    assert hand_value([Card("A", "♠"), Card("A", "♥")]) == 12


def test_is_blackjack_true_for_two_card_21():
    assert is_blackjack([Card("A", "♠"), Card("K", "♥")]) is True


def test_is_blackjack_false_for_three_card_21():
    assert is_blackjack([Card("7", "♠"), Card("7", "♥"), Card("7", "♣")]) is False


def test_dealer_hits_until_17():
    dealer = [Card("6", "♠"), Card("6", "♥")]  # 12
    deck = [Card("5", "♣")]  # drawn -> 17, then stands
    dealer_play(dealer, deck)
    assert hand_value(dealer) == 17
    assert len(dealer) == 3


def test_dealer_stands_on_17():
    dealer = [Card("10", "♠"), Card("7", "♥")]  # 17
    deck = [Card("9", "♣")]  # must NOT be drawn
    dealer_play(dealer, deck)
    assert len(dealer) == 2
    assert len(deck) == 1


def test_settle_player_bust_loses():
    player = [Card("10", "♠"), Card("9", "♥"), Card("5", "♣")]  # 24
    dealer = [Card("10", "♦"), Card("8", "♣")]
    result = settle(player, dealer, 100.0)
    assert result.net == -100.0
    assert result.outcome == "lose"


def test_settle_dealer_bust_player_wins():
    player = [Card("10", "♠"), Card("9", "♥")]  # 19
    dealer = [Card("10", "♦"), Card("6", "♣"), Card("9", "♠")]  # 25
    assert settle(player, dealer, 100.0).net == 100.0


def test_settle_higher_total_wins():
    player = [Card("10", "♠"), Card("9", "♥")]  # 19
    dealer = [Card("10", "♦"), Card("7", "♣")]  # 17
    assert settle(player, dealer, 100.0).net == 100.0


def test_settle_equal_total_pushes():
    player = [Card("10", "♠"), Card("8", "♥")]  # 18
    dealer = [Card("10", "♦"), Card("8", "♣")]  # 18
    result = settle(player, dealer, 100.0)
    assert result.net == 0.0
    assert result.outcome == "push"


def test_settle_player_blackjack_pays_3_to_2():
    player = [Card("A", "♠"), Card("K", "♥")]
    dealer = [Card("10", "♦"), Card("7", "♣")]
    result = settle(player, dealer, 100.0)
    assert result.net == 150.0
    assert result.outcome == "blackjack"


def test_settle_both_blackjack_pushes():
    player = [Card("A", "♠"), Card("K", "♥")]
    dealer = [Card("A", "♦"), Card("Q", "♣")]
    assert settle(player, dealer, 100.0).net == 0.0


def test_settle_dealer_blackjack_player_loses():
    player = [Card("10", "♠"), Card("9", "♥")]  # 19, not blackjack
    dealer = [Card("A", "♦"), Card("K", "♣")]
    assert settle(player, dealer, 100.0).net == -100.0
