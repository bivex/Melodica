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
    """
    if len(prev) == len(current):
        return float(sum(abs(p - c) for p, c in zip(prev, current)))

    cost = 0.0
    for p in prev:
        cost += min(abs(p - c) for c in current)
    for c in current:
        cost += min(abs(p - c) for p in prev)
    return cost

def voice_lead(prev: ChordLabel, next_chord: ChordLabel) -> list[int]:
    """
    Voice-lead next_chord to minimize voice movement from prev.
    """
    prev_notes = chord_to_notes(prev)
    next_notes = chord_to_notes(next_chord)

    best = min(
        inversions(next_notes),
        key=lambda inv: voice_motion_cost(prev_notes, inv)
    )
    return best
