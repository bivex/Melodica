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
generators/generic_gen.py — GenericGenerator.

Melodica-matching: chord/other proportion, partial polyphony, repeat last/second last.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, chord_pitches_closed


@dataclass
class GenericGenerator(PhraseGenerator):
    """
    Generic Generator.

    chord_note_ratio:    0.0-1.0 proportion of chord vs other (scale) notes
    partial_polyphony:   0.0-1.0 probability of playing multiple chord notes
    max_polyphony:       max notes played simultaneously when polyphonic
    repeat_last:         0.0-1.0 probability of repeating the previous note
    chord_note_indices:  which chord tones to use (0=root, 1=3rd, ...)
    """

    name: str = "Generic Generator"
    chord_note_ratio: float = 0.7
    partial_polyphony: float = 0.2
    max_polyphony: int = 3
    repeat_last: float = 0.1
    chord_note_indices: list[int] = field(default_factory=lambda: [0, 1, 2])
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        chord_note_ratio: float = 0.7,
        partial_polyphony: float = 0.2,
        max_polyphony: int = 3,
        repeat_last: float = 0.1,
        chord_note_indices: list[int] | None = None,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.chord_note_ratio = max(0.0, min(1.0, chord_note_ratio))
        self.partial_polyphony = max(0.0, min(1.0, partial_polyphony))
        self.max_polyphony = max(1, max_polyphony)
        self.repeat_last = max(0.0, min(1.0, repeat_last))
        self.chord_note_indices = (
            chord_note_indices if chord_note_indices is not None else [0, 1, 2]
        )
        self.rhythm = rhythm
        self._last_context: RenderContext | None = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        last_chord = chords[0]
        last_pitch: int | None = context.prev_pitch if context else None

        anchor = (self.params.key_range_low + self.params.key_range_high) // 2

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Repeat last note?
            if last_pitch is not None and random.random() < self.repeat_last:
                notes.append(
                    NoteInfo(
                        pitch=last_pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(
                            1,
                            min(127, int((60 + self.params.density * 40) * event.velocity_factor)),
                        ),
                    )
                )
                continue

            # Chord note or scale note?
            if random.random() < self.chord_note_ratio:
                # Chord note
                pcs = chord.pitch_classes()
                pool = (
                    [pcs[i % len(pcs)] for i in self.chord_note_indices if i < len(pcs)]
                    if pcs
                    else []
                )
            else:
                # Scale note
                pool = key.degrees()

            if not pool:
                continue

            # Partial polyphony?
            if random.random() < self.partial_polyphony:
                count = min(random.randint(1, self.max_polyphony), len(pool))
                selected_pcs = random.sample(pool, count)
            else:
                selected_pcs = [random.choice(pool)]

            base_vel = int((60 + self.params.density * 40) * event.velocity_factor)

            for pc in selected_pcs:
                pitch = nearest_pitch(pc, anchor)
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, base_vel)),
                    )
                )
                last_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.9))
            t += 1.0
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 40)
