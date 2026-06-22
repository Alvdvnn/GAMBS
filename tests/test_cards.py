import random

from gambs.games.cards import (
    Card, RANKS, SUITS, make_deck, shuffle, card_str, hand_str,
)


def test_make_deck_has_52_unique_cards():
    deck = make_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52


def test_make_deck_covers_all_rank_suit_pairs():
    deck = make_deck()
    for r in RANKS:
        for s in SUITS:
            assert Card(r, s) in deck


def test_shuffle_returns_full_deck():
    deck = shuffle(random.Random(0))
    assert len(deck) == 52
    assert len(set(deck)) == 52


def test_shuffle_is_deterministic_for_a_seed():
    assert shuffle(random.Random(7)) == shuffle(random.Random(7))


def test_shuffle_changes_order():
    assert shuffle(random.Random(1)) != make_deck()


def test_card_str_and_hand_str():
    assert card_str(Card("A", "♠")) == "A♠"
    assert card_str(Card("10", "♥")) == "10♥"
    assert hand_str([Card("A", "♠"), Card("10", "♥")]) == "A♠ 10♥"
