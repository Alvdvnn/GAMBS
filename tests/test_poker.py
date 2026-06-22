from gambs.games.cards import Card
from gambs.games.poker import PAYTABLE, evaluate, deal, redraw, settle


def test_royal_flush():
    hand = [Card("10", "♠"), Card("J", "♠"), Card("Q", "♠"), Card("K", "♠"), Card("A", "♠")]
    assert evaluate(hand) == "royal_flush"


def test_straight_flush():
    hand = [Card("5", "♥"), Card("6", "♥"), Card("7", "♥"), Card("8", "♥"), Card("9", "♥")]
    assert evaluate(hand) == "straight_flush"


def test_four_of_a_kind():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("9", "♦"), Card("9", "♣"), Card("2", "♠")]
    assert evaluate(hand) == "four_kind"


def test_full_house():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("9", "♦"), Card("2", "♣"), Card("2", "♠")]
    assert evaluate(hand) == "full_house"


def test_flush():
    hand = [Card("2", "♠"), Card("5", "♠"), Card("8", "♠"), Card("J", "♠"), Card("K", "♠")]
    assert evaluate(hand) == "flush"


def test_straight():
    hand = [Card("4", "♠"), Card("5", "♥"), Card("6", "♦"), Card("7", "♣"), Card("8", "♠")]
    assert evaluate(hand) == "straight"


def test_wheel_straight_ace_low():
    hand = [Card("A", "♠"), Card("2", "♥"), Card("3", "♦"), Card("4", "♣"), Card("5", "♠")]
    assert evaluate(hand) == "straight"


def test_three_of_a_kind():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("9", "♦"), Card("2", "♣"), Card("5", "♠")]
    assert evaluate(hand) == "three_kind"


def test_two_pair():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("2", "♦"), Card("2", "♣"), Card("5", "♠")]
    assert evaluate(hand) == "two_pair"


def test_jacks_or_better():
    hand = [Card("J", "♠"), Card("J", "♥"), Card("2", "♦"), Card("5", "♣"), Card("8", "♠")]
    assert evaluate(hand) == "jacks_or_better"


def test_low_pair_is_nothing():
    hand = [Card("9", "♠"), Card("9", "♥"), Card("2", "♦"), Card("5", "♣"), Card("8", "♠")]
    assert evaluate(hand) == "nothing"


def test_high_card_is_nothing():
    hand = [Card("2", "♠"), Card("5", "♥"), Card("8", "♦"), Card("J", "♣"), Card("K", "♠")]
    assert evaluate(hand) == "nothing"


def test_settle_royal_flush_pays_800x():
    assert settle("royal_flush", 5.0) == 4000.0


def test_settle_jacks_or_better_is_even_money():
    assert settle("jacks_or_better", 10.0) == 10.0


def test_settle_nothing_loses_bet():
    assert settle("nothing", 10.0) == -10.0


def test_deal_takes_five_cards_off_the_deck():
    deck = [Card(r, "♠") for r in ["2", "3", "4", "5", "6", "7"]]
    hand = deal(deck)
    assert len(hand) == 5
    assert len(deck) == 1


def test_redraw_keeps_held_replaces_rest():
    hand = [Card("A", "♠"), Card("2", "♥"), Card("3", "♦"), Card("4", "♣"), Card("5", "♠")]
    deck = [Card("K", "♦"), Card("Q", "♦")]  # two replacements (popped from end)
    result = redraw(hand, {0, 1, 2}, deck)
    assert result[0] == Card("A", "♠")
    assert result[1] == Card("2", "♥")
    assert result[2] == Card("3", "♦")
    assert result[3] == Card("Q", "♦")  # first pop
    assert result[4] == Card("K", "♦")  # second pop


def test_paytable_has_all_categories():
    expected = {
        "royal_flush", "straight_flush", "four_kind", "full_house", "flush",
        "straight", "three_kind", "two_pair", "jacks_or_better", "nothing",
    }
    assert set(PAYTABLE) == expected
