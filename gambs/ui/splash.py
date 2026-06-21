"""Slot-machine splash: ASCII logo assembly and reel animation frames.

The logo is built from five 6-line letter blocks (G A M B S). During the
intro, reels lock left-to-right; unlocked reels show scrambled glyphs.
"""

from __future__ import annotations

import random

# Each letter: exactly 6 rows, each row the same width for that letter.
LETTERS: dict[str, list[str]] = {
    "G": [
        " ██████╗ ",
        "██╔════╝ ",
        "██║  ███╗",
        "██║   ██║",
        "╚██████╔╝",
        " ╚═════╝ ",
    ],
    "A": [
        " █████╗ ",
        "██╔══██╗",
        "███████║",
        "██╔══██║",
        "██║  ██║",
        "╚═╝  ╚═╝",
    ],
    "M": [
        "███╗   ███╗",
        "████╗ ████║",
        "██╔████╔██║",
        "██║╚██╔╝██║",
        "██║ ╚═╝ ██║",
        "╚═╝     ╚═╝",
    ],
    "B": [
        "██████╗ ",
        "██╔══██╗",
        "██████╔╝",
        "██╔══██╗",
        "██████╔╝",
        "╚═════╝ ",
    ],
    "S": [
        "███████╗",
        "██╔════╝",
        "███████╗",
        "╚════██║",
        "███████║",
        "╚══════╝",
    ],
}

WORD = "GAMBS"
_SCRAMBLE = "▓▒░#@$%&*0123456789ABCDEF"


def render_logo() -> str:
    """Join all five letter blocks column-wise into a 6-line string."""
    rows = []
    for line_idx in range(6):
        rows.append("  ".join(LETTERS[ch][line_idx] for ch in WORD))
    return "\n".join(rows)


def _scrambled_block(width: int, rng: random.Random) -> list[str]:
    """A 6-line block of random glyphs at the given width."""
    return [
        "".join(rng.choice(_SCRAMBLE) for _ in range(width)) for _ in range(6)
    ]


def reel_frame(locked: int, rng: random.Random) -> str:
    """Build one animation frame.

    The first `locked` reels show their final letter; the rest show scrambled
    glyphs of the same width. `locked == 5` yields the final logo exactly.
    """
    blocks: list[list[str]] = []
    for i, ch in enumerate(WORD):
        width = len(LETTERS[ch][0])
        if i < locked:
            blocks.append(LETTERS[ch])
        else:
            blocks.append(_scrambled_block(width, rng))
    rows = []
    for line_idx in range(6):
        rows.append("  ".join(block[line_idx] for block in blocks))
    return "\n".join(rows)
