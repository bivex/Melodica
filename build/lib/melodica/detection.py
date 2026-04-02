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
detection.py — Chord detection and scale detection pipelines.

Layer: Domain / Application (pure algorithms, no I/O).
Derived from common chord/scale detection concepts:
  - Basic chord detection pipeline
  - Scale and chord identification step using Krumhansl-Schmuckler

Rules:
  - No imports from engines, generators, or infrastructure.
  - numpy used only for KS profile dot-products (§3.3).
"""

from __future__ import annotations

import numpy as np

from melodica.types import (
    CHORD_TEMPLATES,
    ChordLabel,
    HarmonicFunction,
    Mode,
    Note,
    Quality,
    Scale,
)
from melodica.utils import pitch_class


# ---------------------------------------------------------------------------
# §3.1  Template-matching chord detection
# ---------------------------------------------------------------------------


def _match_score(
    pitch_classes: set[int],
    root: int,
    quality: Quality,
    prefer_simpler: bool,
) -> float:
    """
    Compute how well `pitch_classes` matches the chord (root, quality).

    full match:   all chord tones present → 1.0 base
    missing tone: −0.3 per missing chord tone
    foreign note: −0.1 per pitch class not in chord
    prefer_simpler: triads get +0.05 bonus when tied
    """
    template = CHORD_TEMPLATES.get(quality)
    if template is None:
        return 0.0

    chord_pcs = {(root + ivl) % 12 for ivl in template}
    present = chord_pcs & pitch_classes
    missing = chord_pcs - pitch_classes
    foreign = pitch_classes - chord_pcs

    score = len(present) / max(len(chord_pcs), 1)
    score -= 0.3 * len(missing)
    score -= 0.1 * len(foreign)

    if prefer_simpler and len(template) == 3:
        score += 0.05

    return max(0.0, score)


def detect_chord(
    notes: list[Note],
    *,
    min_score: float = 0.6,
    prefer_simpler: bool = True,
) -> ChordLabel | None:
    """
    Detect the chord from a simultaneous group of notes.

    Returns the best-matching ChordLabel or None if score < min_score.
    Inversion is resolved from the lowest sounding note.
    """
    if not notes:
        return None

    pcs = {pitch_class(n.pitch) for n in notes}
    lowest = min(notes, key=lambda n: n.pitch)
    lowest_pc = pitch_class(lowest.pitch)

    best_score = -1.0
    best: tuple[int, Quality] | None = None

    for root in range(12):
        for quality in CHORD_TEMPLATES:
            s = _match_score(pcs, root, quality, prefer_simpler)
            if s > best_score:
                best_score = s
                best = (root, quality)

    if best_score < min_score or best is None:
        return None

    root, quality = best
    template = CHORD_TEMPLATES[quality]
    chord_pcs = [(root + ivl) % 12 for ivl in template]

    # Resolve inversion from lowest note
    inversion = 0
    if lowest_pc in chord_pcs:
        inversion = chord_pcs.index(lowest_pc)

    return ChordLabel(
        root=root,
        quality=quality,
        bass=lowest_pc if lowest_pc != root else None,
        inversion=inversion,
    )


def detect_chords_from_midi(
    notes: list[Note],
    *,
    window: float = 1.0,
    stride: float = 0.5,
    key: Scale | None = None,
) -> list[ChordLabel]:
    """
    Sliding-window chord detection over a sequence of notes.

    window:  beat window width for grouping notes
    stride:  step between windows
    key:     if provided, annotate each ChordLabel with degree + function
    """
    if not notes:
        return []

    start_times = sorted({n.start for n in notes})
    timeline_end = max(n.start + n.duration for n in notes)

    results: list[ChordLabel] = []
    t = 0.0
    while t < timeline_end:
        window_notes = [
            n for n in notes
            if n.start < t + window and (n.start + n.duration) > t
        ]
        chord = detect_chord(window_notes)
        if chord is not None:
            chord.start = t
            chord.duration = window
            if key is not None:
                _annotate_degree(chord, key)
            results.append(chord)
        t += stride

    # Merge consecutive identical chords
    return _merge_consecutive(results)


def _annotate_degree(chord: ChordLabel, key: Scale) -> None:
    """Mutate chord in-place to set degree and harmonic function."""
    degs = key.degrees()
    if chord.root in degs:
        chord.degree = degs.index(chord.root) + 1
        chord.function = _degree_to_function(chord.degree, key.mode)


def _degree_to_function(degree: int, mode: Mode) -> HarmonicFunction:
    """Map scale degree to harmonic function (simplified, major/minor)."""
    tonic_degrees = {1, 3, 6}
    subdominant_degrees = {2, 4}
    dominant_degrees = {5, 7}
    if degree in tonic_degrees:
        return HarmonicFunction.TONIC
    if degree in subdominant_degrees:
        return HarmonicFunction.SUBDOMINANT
    return HarmonicFunction.DOMINANT


def _merge_consecutive(chords: list[ChordLabel]) -> list[ChordLabel]:
    """Merge adjacent ChordLabels with the same root+quality."""
    if not chords:
        return []
    merged = [chords[0]]
    for c in chords[1:]:
        prev = merged[-1]
        if prev.root == c.root and prev.quality == c.quality:
            prev.duration += c.duration
        else:
            merged.append(c)
    return merged


# ---------------------------------------------------------------------------
# §3.3  Krumhansl-Schmuckler scale detection
# ---------------------------------------------------------------------------

# Key profiles from Krumhansl & Schmuckler (1990)
_KS_MAJOR = np.array([
    6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
    2.52, 5.19, 2.39, 3.66, 2.29, 2.88,
])
_KS_MINOR = np.array([
    6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
    2.54, 4.75, 3.98, 2.69, 3.34, 3.17,
])


def detect_scale(notes: list[Note]) -> Scale:
    """
    Krumhansl-Schmuckler key-finding algorithm.

    Builds a pitch-class duration histogram and correlates it against
    the major and minor key profiles for all 12 transpositions.
    Returns the most likely Scale (major or natural minor).
    """
    if not notes:
        return Scale(root=0, mode=Mode.MAJOR)

    histogram = np.zeros(12)
    for n in notes:
        histogram[pitch_class(n.pitch)] += n.duration

    # Normalise
    total = histogram.sum()
    if total > 0:
        histogram /= total

    best_corr = -2.0
    best_root = 0
    best_mode = Mode.MAJOR

    for root in range(12):
        rotated = np.roll(histogram, -root)

        corr_major = float(np.corrcoef(rotated, _KS_MAJOR)[0, 1])
        corr_minor = float(np.corrcoef(rotated, _KS_MINOR)[0, 1])

        if corr_major > best_corr:
            best_corr = corr_major
            best_root = root
            best_mode = Mode.MAJOR

        if corr_minor > best_corr:
            best_corr = corr_minor
            best_root = root
            best_mode = Mode.NATURAL_MINOR

    return Scale(root=best_root, mode=best_mode)


# ---------------------------------------------------------------------------
# §3.4  Key detection from chord sequences
# ---------------------------------------------------------------------------


def detect_scale_from_chords(chords: list[ChordLabel]) -> Scale:
    """
    Determines the most likely Scale for a sequence of chords.
    Weights each pitch class by the duration of the chords it belongs to.
    """
    if not chords:
        return Scale(root=0, mode=Mode.MAJOR)

    # 1. Build a duration-weighted pitch class histogram
    histogram = np.zeros(12)
    for chord in chords:
        pcs = chord.pitch_classes()
        weight = chord.duration / len(pcs)
        for pc in pcs:
            histogram[pc] += weight

    # 2. Correlate against KS profiles (reusing the same logic as note-based)
    total = histogram.sum()
    if total > 0:
        histogram /= total

    best_corr = -2.0
    best_root = 0
    best_mode = Mode.MAJOR

    for root in range(12):
        rotated = np.roll(histogram, -root)
        corr_major = float(np.corrcoef(rotated, _KS_MAJOR)[0, 1])
        corr_minor = float(np.corrcoef(rotated, _KS_MINOR)[0, 1])

        if corr_major > best_corr:
            best_corr, best_root, best_mode = corr_major, root, Mode.MAJOR
        if corr_minor > best_corr:
            best_corr, best_root, best_mode = corr_minor, root, Mode.NATURAL_MINOR

    return Scale(root=best_root, mode=best_mode)

