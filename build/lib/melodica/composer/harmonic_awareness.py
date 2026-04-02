# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
composer/harmonic_awareness.py — Harmonic awareness for melody generators.

Layer: Domain
Style: Jazz / Classical / All tonal music.

Provides:
  - Avoid note detection per chord quality
  - Guide tone identification (3rd, 7th)
  - Weighted pitch class scoring for melody generators
  - Tension note identification (9th, 11th, 13th)

Usage:
    weights = pitch_class_weights(root=0, quality=Quality.MAJOR7)
    # weights = {0: 1.2, 4: 1.5, 7: 1.0, 11: 1.5, ...}
    # avoid note (4th degree = 5 semitones) gets low weight

    guide = guide_tones(root=5, quality=Quality.DOMINANT7)
    # guide = {3rd: 4, 7th: 10}  — these resolve to next chord
"""

from __future__ import annotations

from melodica.types import Quality, ChordLabel


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OCTAVE = 12

# Weight multipliers for chord tone roles
_WEIGHT_ROOT = 1.2
_WEIGHT_THIRD = 1.5
_WEIGHT_FIFTH = 1.0
_WEIGHT_SEVENTH = 1.5
_WEIGHT_EXTENSION = 0.8
_WEIGHT_AVOID = 0.15
_WEIGHT_SCALE_TONE = 0.5

# Avoid notes per quality: interval from root (semitones)
# The "avoid" note is the one that clashes with chord tones
_AVOID_NOTES: dict[Quality, list[int]] = {
    Quality.MAJOR: [5],  # 4th (F over C major) clashes with 3rd
    Quality.MINOR: [],  # no avoid notes in minor triad
    Quality.MAJOR7: [5],  # 4th clashes with maj7
    Quality.DOMINANT7: [],  # dom7 is flexible
    Quality.MINOR7: [],  # minor 7th is flexible
    Quality.DIMINISHED: [],
    Quality.HALF_DIM7: [],
    Quality.FULL_DIM7: [],
    Quality.SUS2: [],  # sus2 replaces 3rd, so no clash
    Quality.SUS4: [],  # sus4 replaces 3rd, so no clash
    Quality.AUGMENTED: [],
    Quality.POWER: [],
}

# Guide tone intervals: (3rd, 7th) relative to root
_GUIDE_TONES: dict[Quality, tuple[int, int | None]] = {
    Quality.MAJOR: (4, None),  # maj3, no 7th
    Quality.MINOR: (3, None),  # min3, no 7th
    Quality.MAJOR7: (4, 11),  # maj3, maj7
    Quality.DOMINANT7: (4, 10),  # maj3, min7
    Quality.MINOR7: (3, 10),  # min3, min7
    Quality.HALF_DIM7: (3, 10),  # min3, min7
    Quality.FULL_DIM7: (3, 9),  # min3, dim7
    Quality.DIMINISHED: (3, None),  # min3, no 7th
    Quality.SUS2: (2, None),  # sus2 replaces 3rd
    Quality.SUS4: (5, None),  # sus4 replaces 3rd
    Quality.AUGMENTED: (4, None),  # maj3, aug5
    Quality.POWER: (7, None),  # 5th only, no 3rd
}

# Chord tone intervals from root (always present)
_CHORD_TONE_INTERVALS: dict[Quality, list[int]] = {
    Quality.MAJOR: [0, 4, 7],
    Quality.MINOR: [0, 3, 7],
    Quality.DIMINISHED: [0, 3, 6],
    Quality.AUGMENTED: [0, 4, 8],
    Quality.MAJOR7: [0, 4, 7, 11],
    Quality.DOMINANT7: [0, 4, 7, 10],
    Quality.MINOR7: [0, 3, 7, 10],
    Quality.HALF_DIM7: [0, 3, 6, 10],
    Quality.FULL_DIM7: [0, 3, 6, 9],
    Quality.SUS2: [0, 2, 7],
    Quality.SUS4: [0, 5, 7],
    Quality.POWER: [0, 7],
}

# Extension intervals (9th, 11th, 13th)
_EXTENSION_INTERVALS: dict[Quality, list[int]] = {
    Quality.MAJOR: [2, 9, 11],  # 9, #11, 13
    Quality.MINOR: [2, 5, 9],  # 9, 11, b13
    Quality.MAJOR7: [2, 9, 11],
    Quality.DOMINANT7: [2, 5, 9],  # 9, 11, 13
    Quality.MINOR7: [2, 5, 9],
    Quality.DIMINISHED: [],
    Quality.HALF_DIM7: [2, 5],
    Quality.FULL_DIM7: [],
    Quality.SUS2: [5, 9],
    Quality.SUS4: [2, 9],
    Quality.AUGMENTED: [2, 9],
    Quality.POWER: [],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def pitch_class_weights(
    root: int,
    quality: Quality,
    beat_strength: float = 1.0,
) -> dict[int, float]:
    """
    Return weights for each pitch class (0-11) based on harmonic function.

    root:          Chord root pitch class (0-11)
    quality:       Chord quality
    beat_strength: 0.0-1.0, how strong the beat is (stronger = more
                   emphasis on chord tones, weaker = more dissonance allowed)

    Returns dict: pitch_class → weight (higher = better choice)
    """
    weights: dict[int, float] = {}

    chord_tones = _CHORD_TONE_INTERVALS.get(quality, [0, 4, 7])
    avoid = _AVOID_NOTES.get(quality, [])
    extensions = _EXTENSION_INTERVALS.get(quality, [])
    thirds, sevenths = _guide_tone_intervals(quality)

    for i in range(_OCTAVE):
        interval = (i - root) % _OCTAVE

        if interval == 0:
            weights[i] = _WEIGHT_ROOT
        elif interval in (thirds, sevenths) and sevenths is not None:
            weights[i] = _WEIGHT_SEVENTH if interval == sevenths else _WEIGHT_THIRD
        elif interval == thirds:
            weights[i] = _WEIGHT_THIRD
        elif interval in chord_tones:
            weights[i] = _WEIGHT_FIFTH
        elif interval in avoid:
            # Avoid notes get penalised more on strong beats
            penalty = _WEIGHT_AVOID * (1.0 + (1.0 - beat_strength) * 2.0)
            weights[i] = max(0.05, penalty)
        elif interval in extensions:
            weights[i] = _WEIGHT_EXTENSION
        else:
            weights[i] = _WEIGHT_SCALE_TONE

    return weights


def guide_tones(root: int, quality: Quality) -> dict[str, int]:
    """Return guide tone pitch classes: {3rd: pc, 7th: pc or None}."""
    thirds, sevenths = _guide_tone_intervals(quality)
    result: dict[str, int] = {}
    if thirds is not None:
        result["3rd"] = (root + thirds) % _OCTAVE
    if sevenths is not None:
        result["7th"] = (root + sevenths) % _OCTAVE
    return result


def avoid_notes(root: int, quality: Quality) -> list[int]:
    """Return pitch classes to avoid for this chord."""
    intervals = _AVOID_NOTES.get(quality, [])
    return [(root + iv) % _OCTAVE for iv in intervals]


def chord_tone_pcs(root: int, quality: Quality) -> list[int]:
    """Return all chord tone pitch classes."""
    intervals = _CHORD_TONE_INTERVALS.get(quality, [0, 4, 7])
    return [(root + iv) % _OCTAVE for iv in intervals]


def weight_pitch(
    pitch: int,
    root: int,
    quality: Quality,
    beat_strength: float = 1.0,
) -> float:
    """
    Score a single pitch for harmonic fit.

    Combines pitch class weight with register preference.
    """
    pc = pitch % _OCTAVE
    weights = pitch_class_weights(root, quality, beat_strength)
    return weights.get(pc, 0.5)


def best_chord_tone(
    prev_pitch: int,
    root: int,
    quality: Quality,
    low: int = 36,
    high: int = 96,
) -> int:
    """
    Find the nearest chord tone to prev_pitch within range.
    """
    from melodica.utils import nearest_pitch

    pcs = chord_tone_pcs(root, quality)
    if not pcs:
        return prev_pitch

    candidates = []
    for pc in pcs:
        for octave in range(low // _OCTAVE, high // _OCTAVE + 1):
            p = octave * _OCTAVE + pc
            if low <= p <= high:
                candidates.append(p)

    if not candidates:
        return prev_pitch

    return min(candidates, key=lambda p: abs(p - prev_pitch))


def guide_tone_resolution(
    current_pc: int,
    current_root: int,
    next_root: int,
    next_quality: Quality,
) -> int:
    """
    Resolve a guide tone from current chord to next chord.
    Guide tones (3rd, 7th) move by step to nearest chord tone.
    """
    from melodica.utils import nearest_pitch

    next_chord_pcs = chord_tone_pcs(next_root, next_quality)
    if not next_chord_pcs:
        return current_pc

    # Find nearest next-chord pitch class
    best_pc = min(next_chord_pcs, key=lambda p: abs(p - current_pc))
    # Wrap around octave
    if abs(((best_pc - current_pc) % _OCTAVE)) < abs(best_pc - current_pc):
        best_pc = best_pc if abs(((best_pc - current_pc) % _OCTAVE)) <= 6 else best_pc

    return best_pc


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _guide_tone_intervals(quality: Quality) -> tuple[int | None, int | None]:
    pair = _GUIDE_TONES.get(quality, (4, None))
    return pair
