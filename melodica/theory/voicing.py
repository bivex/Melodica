# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18
# Last Updated: 2026-05-18
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

from __future__ import annotations
from typing import TYPE_CHECKING

from melodica.theory.chords import CHORD_TEMPLATES

if TYPE_CHECKING:
    from melodica.types import ChordLabel

def chord_to_notes(chord: ChordLabel, base_octave: int = 4) -> list[int]:
    """
    Convert a ChordLabel into absolute MIDI notes based on its template,
    extensions, and slash bass.
    """
    template = CHORD_TEMPLATES.get(chord.quality, [0])
    root_pitch = 12 * (base_octave + 1) + chord.root
    pitches = [root_pitch + ivl for ivl in template]

    # Add extensions
    for ext in chord.extensions:
        pitches.append(root_pitch + ext)

    pitches = sorted(list(set(pitches)))

    # Apply slash bass if specified
    if chord.bass is not None:
        bass_pitch = 12 * base_octave + chord.bass
        # Ensure the bass is strictly lower than the chord members
        while bass_pitch >= pitches[0]:
            bass_pitch -= 12
        pitches = [bass_pitch] + pitches

    return pitches

def inversions(pitches: list[int]) -> list[list[int]]:
    """
    Generate standard chord inversions by cyclic octave transposition
    of the lowest chord members.
    """
    results = [pitches]
    n = len(pitches)
    if n <= 1:
        return results

    current = list(pitches)
    for _ in range(n - 1):
        lowest = current.pop(0)
        current.append(lowest + 12)
        results.append(sorted(current))
    return results

def voice_motion_cost(prev: list[int], current: list[int]) -> float:
    """
    Calculate the total voice movement cost between two chord voicings.
    Optimized to completely eliminate nested generator expression overhead.
    """
    n_prev = len(prev)
    n_curr = len(current)
    if n_prev == n_curr:
        cost = 0
        for i in range(n_prev):
            diff = prev[i] - current[i]
            cost += diff if diff >= 0 else -diff
        return float(cost)

    cost = 0.0
    for p in prev:
        min_diff = 9999
        for c in current:
            diff = p - c
            abs_diff = diff if diff >= 0 else -diff
            if abs_diff < min_diff:
                min_diff = abs_diff
        cost += min_diff

    for c in current:
        min_diff = 9999
        for p in prev:
            diff = p - c
            abs_diff = diff if diff >= 0 else -diff
            if abs_diff < min_diff:
                min_diff = abs_diff
        cost += min_diff

    return cost

def voice_lead(prev: ChordLabel | list[int], next_chord: ChordLabel | list[int]) -> list[int]:
    """
    Voice-lead next_chord to minimize voice movement from prev.
    Supports passing pre-calculated pitch lists or ChordLabels.
    Optimized with early exit for cost == 0.0.
    """
    if isinstance(prev, list):
        prev_notes = prev
    else:
        prev_notes = chord_to_notes(prev)

    if isinstance(next_chord, list):
        next_notes = next_chord
    else:
        next_notes = chord_to_notes(next_chord)

    best_cost = 999999.0
    best_inv = next_notes

    for inv in inversions(next_notes):
        cost = voice_motion_cost(prev_notes, inv)
        if cost == 0.0:
            return inv
        if cost < best_cost:
            best_cost = cost
            best_inv = inv

    return best_inv
