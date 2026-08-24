# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/density.py — Composable chord density and instrument profile strategies.

Layer: Application / Domain

Provides reusable strategy classes for chord-rate subdivision, thinning, and instrument profiles.
Replaces duplicate template logic across instrument solo generator base classes.
"""

from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass
from melodica.types import ChordLabel


class DensityStrategy:
    """
    Applies musical note/chord density scaling (thinning or subdivision) to a chord sequence.
    """

    @staticmethod
    def apply(chords: list[ChordLabel], note_density: float = 1.0) -> list[ChordLabel]:
        if not chords or note_density == 1.0:
            return chords

        if note_density <= 0.0:
            return []

        if note_density < 1.0:
            # Thinning: keep a subset of chords proportionally
            new_chords = []
            for i, chord in enumerate(chords):
                prev_val = int((i - 1) * note_density) if i > 0 else -1
                curr_val = int(i * note_density)
                if curr_val > prev_val:
                    new_chords.append(chord)
            return new_chords

        # Subdivision: split each chord into smaller rhythmic slices
        subdivisions = max(1, round(note_density))
        if subdivisions <= 1:
            return chords

        new_chords = []
        for chord in chords:
            sub_dur = chord.duration / subdivisions
            for s in range(subdivisions):
                new_chord = dataclasses.replace(
                    chord,
                    start=chord.start + s * sub_dur,
                    duration=sub_dur,
                )
                new_chords.append(new_chord)
        return new_chords


@dataclass
class InstrumentProfile:
    """
    Value object / configuration profile defining instrument tessitura, velocity, and density.
    """

    name: str
    min_pitch: int = 21  # A0
    max_pitch: int = 108  # C8
    default_velocity: int = 80
    note_density: float = 1.0

    def apply_density(self, chords: list[ChordLabel]) -> list[ChordLabel]:
        return DensityStrategy.apply(chords, self.note_density)

    def resolve_velocity(self, base_val: int | None = None, velocity_range: tuple[int, int] | None = None) -> int:
        if velocity_range:
            v_min, v_max = velocity_range
            return random.randint(v_min, v_max)
        val = base_val if base_val is not None else self.default_velocity
        return max(1, min(127, val + random.randint(-8, 8)))
