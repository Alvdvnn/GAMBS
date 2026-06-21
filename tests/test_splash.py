import random

from gambs.ui.splash import LETTERS, render_logo, reel_frame


def test_every_letter_has_six_equal_width_lines():
    for ch in "GAMBS":
        rows = LETTERS[ch]
        assert len(rows) == 6
        assert len({len(r) for r in rows}) == 1  # all rows same width


def test_render_logo_is_six_lines():
    logo = render_logo()
    assert logo.count("\n") == 5  # 6 lines => 5 newlines


def test_reel_frame_with_all_locked_equals_logo():
    # When all 5 reels are locked, the frame is the final logo.
    frame = reel_frame(locked=5, rng=random.Random(0))
    assert frame == render_logo()


def test_reel_frame_is_six_lines_when_spinning():
    frame = reel_frame(locked=2, rng=random.Random(0))
    assert frame.count("\n") == 5
