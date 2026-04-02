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
engines/functional.py — Engine 0: FunctionalEngine (18th-century / Basic Functional).

Layer: Domain / Application

Philosophy (§4):
  - Maps every melody note to a diatonic chord by scale-degree analysis.
  - Prefers melody note as 3rd of chord (weight 1.0) or 5th (0.9).
  - Applies voice-leading rules post-selection.
  - Enforces T→S→D→T cadential pattern at phrase boundaries.
"""

from __future__ import annotations

from melodica import types
from melodica.utils import chord_pitches_closed, voice_leading_distance


# ---------------------------------------------------------------------------
# Tone-position weights (§4.3)
# ---------------------------------------------------------------------------

_POSITION_WEIGHTS: dict[int, float] = {
    0: 0.8,  # melody note is root
    1: 1.0,  # melody note is 3rd   ← preferred
    2: 0.9,  # melody note is 5th
    3: 0.5,  # melody note is 7th   (non-cadential only)
}

# Standard cadential function sequence
_T_S_D_T = [
    types.HarmonicFunction.TONIC,
    types.HarmonicFunction.SUBDOMINANT,
    types.HarmonicFunction.DOMINANT,
    types.HarmonicFunction.TONIC,
]

# Degree → function mapping for major key
_DEGREE_FUNCTION_MAJOR: dict[int, types.HarmonicFunction] = {
    1: types.HarmonicFunction.TONIC,
    2: types.HarmonicFunction.SUBDOMINANT,
    3: types.HarmonicFunction.TONIC,
    4: types.HarmonicFunction.SUBDOMINANT,
    5: types.HarmonicFunction.DOMINANT,
    6: types.HarmonicFunction.TONIC,
    7: types.HarmonicFunction.DOMINANT,
}


# ---------------------------------------------------------------------------
# Public engine class
# ---------------------------------------------------------------------------


class FunctionalEngine:
    """Engine 0 — 18th-century functional harmony."""

    def harmonize(self, req: types.HarmonizationRequest) -> list[types.ChordLabel]:
        melody = req.melody
        key = req.key
        rhythm = req.chord_rhythm

        windows = _segment_by_rhythm(melody, rhythm)
        chords: list[types.ChordLabel] = []
        prev_pitches: list[int] = []

        for i, (window_notes, start_beat, duration) in enumerate(windows):
            is_cadence = (i >= len(windows) - 2)
            chord = _select_chord(
                window_notes, key, is_cadence=is_cadence, allow_seventh=not is_cadence
            )
            chord.start = start_beat
            chord.duration = duration

            # Voice-leading refinement: choose inversion minimising movement
            if prev_pitches:
                chord = _best_inversion(chord, prev_pitches)

            prev_pitches = chord_pitches_closed(chord)
            chords.append(chord)

        return chords


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _segment_by_rhythm(
    melody: list[types.Note],
    rhythm: float,
) -> list[tuple[list[types.Note], float, float]]:
    """
    Split melody into windows of `rhythm` beats.
    Returns list of (notes_in_window, start_beat, duration).
    """
    if not melody:
        return []

    end_time = max(n.start + n.duration for n in melody)
    windows: list[tuple[list[Note], float, float]] = []
    t = 0.0
    while t < end_time:
        window_notes = [
            n for n in melody
            if n.start >= t and n.start < t + rhythm
        ]
        windows.append((window_notes, t, rhythm))
        t += rhythm
    return windows


def _select_chord(
    notes: list[types.Note],
    key: types.Scale,
    *,
    is_cadence: bool,
    allow_seventh: bool,
) -> types.ChordLabel:
    """
    Choose the diatonic chord that best fits the melody notes in this window.
    Priority follows §4.3 position weights.
    """
    if not notes:
        return key.diatonic_chord(1)

    # Determine the melodically strongest note (longest duration)
    primary = max(notes, key=lambda n: n.duration)
    pc = primary.pitch % types.OCTAVE
    scale_degs = key.degrees()

    best_chord: types.ChordLabel | None = None
    best_weight = -1.0

    for degree in range(1, 8):
        chord = key.diatonic_chord(degree, seventh=allow_seventh)
        chord_pcs = chord.pitch_classes()

        if pc not in chord_pcs:
            continue

        pos = chord_pcs.index(pc)
        weight = _POSITION_WEIGHTS.get(pos, 0.0)

        # Cadential bonus: prefer T/S/D at phrase end
        if is_cadence and degree in (1, 4, 5):
            weight += 0.3

        if weight > best_weight:
            best_weight = weight
            best_chord = chord

    if best_chord is None:
        best_chord = key.diatonic_chord(1)

    return best_chord


def _best_inversion(chord: types.ChordLabel, prev_pitches: list[int]) -> types.ChordLabel:
    """
    Try all inversions; return the one with smallest voice-leading distance
    from prev_pitches. Modeled after voice-leading rules §4.4.
    """
    n_tones = len(chord.pitch_classes())
    best = chord
    best_dist = float("inf")

    for inv in range(n_tones):
        candidate = types.ChordLabel(
            root=chord.root,
            quality=chord.quality,
            extensions=chord.extensions,
            bass=chord.bass,
            inversion=inv,
            start=chord.start,
            duration=chord.duration,
            degree=chord.degree,
            function=chord.function,
        )
        pitches = chord_pitches_closed(candidate)
        dist = voice_leading_distance(prev_pitches, pitches)
        if dist < best_dist:
            best_dist = dist
            best = candidate

    return best
