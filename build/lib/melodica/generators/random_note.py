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
generators/random_note.py — RandomNoteGenerator.

Experimental: generates random single notes within a range.
Useful for triggering key-switches or creating texture.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import chord_at


@dataclass
class RandomNoteGenerator(PhraseGenerator):
    """
    Generates random single notes within a range.
    Useful for key-switch triggering or experimental textures.

    velocity_range: (min, max) velocity
    note_range:     (low, high) MIDI pitches to use
    """

    name: str = "Random Note Generator"
    velocity_range: tuple[int, int] = (40, 100)
    note_range: tuple[int, int] = (36, 84)
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        velocity_range: tuple[int, int] = (40, 100),
        note_range: tuple[int, int] = (36, 84),
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.velocity_range = velocity_range
        self.note_range = note_range
        self.rhythm = rhythm
        self._last_context: RenderContext | None = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []

        for event in events:
            pitch = random.randint(self.note_range[0], self.note_range[1])
            vel = random.randint(self.velocity_range[0], self.velocity_range[1])

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=vel,
                )
            )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1] if chords else None,
            )

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.1))
            t += 0.5
        return events
