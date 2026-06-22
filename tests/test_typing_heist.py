import random
import string

from gambs.earn.typing_heist import (
    difficulty_for_balance,
    generate_prompt,
    generate_round,
    accuracy,
    speed_bonus,
    session_reward,
    TIER_BASE_PAY,
    PROMPTS_PER_SESSION,
    MIN_REWARD,
    MAX_REWARD,
)


def test_difficulty_scales_with_balance():
    assert difficulty_for_balance(500) == 1
    assert difficulty_for_balance(1000) == 2
    assert difficulty_for_balance(4999) == 2
    assert difficulty_for_balance(5000) == 3
    assert difficulty_for_balance(20000) == 4
    assert difficulty_for_balance(99999) == 4


def test_generate_prompt_is_deterministic_for_a_seed():
    assert generate_prompt(random.Random(3), 2) == generate_prompt(random.Random(3), 2)


def test_tier1_and_tier2_prompts_are_uppercase_words():
    p1 = generate_prompt(random.Random(1), 1)
    p2 = generate_prompt(random.Random(1), 2)
    assert p1.isalpha() and p1.isupper()
    assert p2.isalpha() and p2.isupper()


def test_tier3_prompt_has_code_suffix():
    p3 = generate_prompt(random.Random(1), 3)
    assert "-" in p3


def test_tier4_prompt_is_ten_char_alphanumeric_code():
    p4 = generate_prompt(random.Random(1), 4)
    assert len(p4) == 10
    allowed = set(string.ascii_uppercase + string.digits)
    assert all(ch in allowed for ch in p4)


def test_generate_round_has_requested_count():
    prompts = generate_round(random.Random(0), 1, 5)
    assert len(prompts) == 5


def test_accuracy_perfect_match():
    assert accuracy("VAULT", "VAULT") == 1.0


def test_accuracy_partial_match():
    assert accuracy("VAILT", "VAULT") == 0.8  # 4 of 5 chars


def test_accuracy_empty_typed_is_zero():
    assert accuracy("", "VAULT") == 0.0


def test_accuracy_penalizes_extra_characters():
    assert round(accuracy("VAULTX", "VAULT"), 4) == 0.8333  # 5 correct / 6 length


def test_speed_bonus_fast_is_capped():
    assert speed_bonus(10.0, 20.0) == 1.25


def test_speed_bonus_on_par_is_one():
    assert speed_bonus(20.0, 20.0) == 1.0


def test_speed_bonus_slow_has_floor():
    assert speed_bonus(100.0, 20.0) == 0.5


def test_session_reward_on_par_perfect_accuracy():
    par = PROMPTS_PER_SESSION * 4.0
    assert session_reward(2, [1.0] * PROMPTS_PER_SESSION, par) == TIER_BASE_PAY[2]


def test_session_reward_clamps_to_max():
    assert session_reward(4, [1.0] * PROMPTS_PER_SESSION, 1.0) == MAX_REWARD


def test_session_reward_clamps_to_min():
    par = PROMPTS_PER_SESSION * 4.0
    assert session_reward(1, [0.0] * PROMPTS_PER_SESSION, par) == MIN_REWARD


def test_session_reward_is_never_negative():
    assert session_reward(1, [], 5.0) >= MIN_REWARD
