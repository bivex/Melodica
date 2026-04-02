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
generators/hemiola.py — Hemiola (cross-rhythm) generator.

Style: Baroque, Latin, African, contemporary classical.

Hemiola creates a rhythmic illusion that reinterprets the meter.
For example, in 3/4 time, grouping 2 bars as 3 equal units (3 half-notes
across 2 bars of 3/4) creates a 3:2 hemiola. In 6/8, playing 2 groups of
3 eighth notes against the native 3 groups of 2 creates the classic hemiola.

Supported patterns:
    "3_over_2"  — 3 notes across 2 beats (triplet feel, classic hemiola)
    "2_over_3"  — 2 notes across 3 beats (dotted feel in triple meter)
    "3_over_4"  — 3 notes across 4 beats (quarter-note triplets in 4/4)
    "4_over_3"  — 4 notes across 3 beats (quadruplets in 3/4)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


_PATTERNS = {
    # pattern_name: (numerator_notes, denominator_beats)
    "3_over_2": (3, 2.0),
    "2_over_3": (2, 3.0),
    "3_over_4": (3, 4.0),
    "4_over_3": (4, 3.0),
}


@dataclass
class HemiolaGenerator(PhraseGenerator):
    """
    Hemiola (cross-rhythm) generator.

    Places notes in a grouping that conflicts with the prevailing meter,
    creating rhythmic tension and the illusion of metric modulation.

    pattern:
        Hemiola pattern name. See _PATTERNS.
    pitch_strategy:
        How to choose pitches: "chord_tone", "scale_tone", "root_fifth".
    velocity_accent:
        Velocity multiplier for the first note of each hemiola group.
    note_duration:
        Duration of each note in beats. None = auto (fill the cycle evenly).
    cycles_per_chord:
        How many hemiola cycles per chord.
    """

    name: str = "Hemiola Generator"
    pattern: str = "3_over_2"
    pitch_strategy: str = "chord_tone"
    velocity_accent: float = 1.15
    note_duration: float | None = None
    cycles_per_chord: int = 1
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "3_over_2",
        pitch_strategy: str = "chord_tone",
        velocity_accent: float = 1.15,
        note_duration: float | None = None,
        cycles_per_chord: int = 1,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if pattern not in _PATTERNS:
            raise ValueError(
                f"Unknown hemiola pattern: {pattern!r}; expected one of {sorted(_PATTERNS)}"
            )
        self.pattern = pattern
        self.pitch_strategy = pitch_strategy
        self.velocity_accent = max(0.5, min(1.5, velocity_accent))
        self.note_duration = note_duration
        self.cycles_per_chord = max(1, cycles_per_chord)
        self.rhythm = rhythm

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        notes: list[NoteInfo] = []
        n_notes, cycle_beats = _PATTERNS[self.pattern]
        dur = self.note_duration if self.note_duration else cycle_beats / n_notes

        t = 0.0
        while t < duration_beats:
            chord = chord_at(chords, t)
            for cycle_idx in range(self.cycles_per_chord):
                cycle_start = t + cycle_idx * cycle_beats
                if cycle_start >= duration_beats:
                    break
                for i in range(n_notes):
                    onset = cycle_start + i * dur
                    if onset >= duration_beats:
                        break
                    pitch = self._pick_pitch(chord, key, i, n_notes)
                    vel = self._velocity(i, n_notes)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=min(dur, duration_beats - onset),
                            velocity=vel,
                        )
                    )
            t += cycle_beats * self.cycles_per_chord

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes

    def _pick_pitch(self, chord: ChordLabel, key: Scale, idx: int, total: int) -> int:
        pcs = chord.pitch_classes()
        if not pcs:
            return key.root * 12 + 60
        base_pc = pcs[idx % len(pcs)]
        if self.pitch_strategy == "root_fifth":
            base_pc = pcs[0] if idx % 2 == 0 else (pcs[0] + 7) % 12
        elif self.pitch_strategy == "scale_tone":
            degrees = key.degrees()
            if degrees:
                base_pc = int(degrees[idx % len(degrees)]) % 12
        return nearest_pitch(base_pc, 60)

    def _velocity(self, idx: int, total: int) -> int:
        base = int(self.params.density * 100)
        if idx == 0:
            return min(127, int(base * self.velocity_accent))
        return max(20, int(base * 0.85))
