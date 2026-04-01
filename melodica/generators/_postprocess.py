"""
generators/_postprocess.py — Shared post-processing for generator classes.

Contains apply_phrase_arch, extracted from PianoRunGenerator, MelodyGenerator,
and other generators to reduce duplication (Multifaceted Abstraction smell).
"""

from __future__ import annotations

import math


def apply_phrase_arch(
    notes: list,
    duration_beats: float,
    phrase_position: float = 0.0,
) -> list:
    """Apply a sinusoidal velocity arch over the phrase duration.

    arch_height grows with phrase_position (0.0→1.0), producing a
    crescendo-shaped velocity contour peaking mid-phrase.
    """
    if not notes or duration_beats <= 0:
        return notes
    arch_height = 0.3 + 0.2 * phrase_position
    for note in notes:
        progress = note.start / duration_beats
        arch = 1.0 - arch_height + arch_height * math.sin(progress * math.pi * 0.7)
        note.velocity = max(1, min(127, int(note.velocity * arch)))
    return notes
