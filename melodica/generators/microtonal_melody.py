# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/microtonal_melody.py — Melody generator with microtonal pitch bends.

Produces melodies that respect microtonal scales (quarter-tone, Arabic, etc.)
by attaching pitch_bend expression data to each NoteInfo for fine-tuning.
"""

from __future__ import annotations

import random

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.engines.microtuning import MicrotuningEngine
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale


class MicrotonalMelodyGenerator(PhraseGenerator):
    """Melody generator that outputs pitch_bend expression for microtonal tuning.

    Uses the standard MelodyGenerator approach but quantizes pitches through
    MicrotuningEngine to produce pitch_bend curves on each note.
    """

    name: str = "Microtonal Melody Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        phrase_length: float = 8.0,
        bend_range: int = 2,
        note_duration: float = 2.0,
        velocity_range: tuple[int, int] = (50, 80),
    ) -> None:
        super().__init__(params)
        self.phrase_length = phrase_length
        self.bend_range = bend_range
        self.note_duration = note_duration
        self.velocity_range = velocity_range
        self._tuning = MicrotuningEngine(bend_range=bend_range)

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords or duration_beats <= 0:
            return []

        density = self.params.density
        lo = self.params.key_range_low
        hi = self.params.key_range_high

        notes: list[NoteInfo] = []
        t = 0.0
        intervals = key.intervals()
        root = key.root

        while t < duration_beats:
            # Decide whether to place a note (density-gated)
            if random.random() > density:
                t += self.note_duration * 0.5
                continue

            # Pick a scale degree and compute microtonal pitch
            deg = random.randint(0, len(intervals) - 1)
            octave_offset = random.choice([0, 12, 12, 24])  # bias toward middle octaves
            raw_pitch = root + intervals[deg] + octave_offset + lo // 12 * 12

            # Clamp to requested range
            raw_pitch = max(float(lo), min(float(hi), raw_pitch))

            dur = self.note_duration * random.uniform(0.8, 1.5)
            vel = random.randint(self.velocity_range[0], self.velocity_range[1])

            note = self._tuning.render_microtonal_note(raw_pitch, t, dur, vel, key)
            notes.append(note)

            t += dur + random.uniform(0.0, self.phrase_length * 0.3)

        notes.sort(key=lambda n: n.start)
        return notes
