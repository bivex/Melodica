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
generators/motive.py — MotiveGenerator.

Short motive (4-8 notes) that can be repeated, transposed, and developed.
Like Melodica's Motive Generator — wraps melody editing concepts.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at

DEVELOPMENT_OPTIONS = {"repeat", "transpose", "invert", "retrograde", "augment"}


@dataclass
class MotiveGenerator(PhraseGenerator):
    """
    Generates a short motive and develops it.

    motive_length:  number of notes in the motive (4-8)
    development:    how to develop: "repeat", "transpose", "invert", "retrograde", "augment"
    scale_steps:    if True, use scale degrees; False = chord tones
    interval_seed:  seed for reproducible motive generation
    """

    name: str = "Motive Generator"
    motive_length: int = 4
    development: str = "transpose"
    scale_steps: bool = False
    interval_seed: int | None = None
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        motive_length: int = 4,
        development: str = "transpose",
        scale_steps: bool = False,
        interval_seed: int | None = None,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.motive_length = max(2, min(16, motive_length))
        if development not in DEVELOPMENT_OPTIONS:
            raise ValueError(f"development must be one of {sorted(DEVELOPMENT_OPTIONS)}")
        self.development = development
        self.scale_steps = scale_steps
        self.interval_seed = interval_seed
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

        rng = random.Random(self.interval_seed)
        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        last_chord = chords[0]

        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        # 1. Generate the motive (short interval sequence)
        motive_intervals = [rng.choice([-3, -2, -1, 0, 1, 2, 3]) for _ in range(self.motive_length)]

        # 2. Build motive pitches
        chord = chords[0]
        if self.scale_steps:
            pool = [p for p in range(low, high + 1) if key.contains(p % 12)]
        else:
            pcs = chord.pitch_classes()
            pool = (
                [p for p in range(low, high + 1) if p % 12 in pcs]
                if pcs
                else list(range(low, high + 1))
            )

        if not pool:
            return []

        start_pitch = nearest_pitch(chord.root, anchor)
        start_pitch = max(low, min(high, start_pitch))

        motive_pitches = [start_pitch]
        for ivl in motive_intervals:
            p = motive_pitches[-1] + ivl
            if not key.contains(p % 12):
                p = nearest_pitch(chord.root, p)
            p = max(low, min(high, p))
            motive_pitches.append(p)

        # 3. Apply development and repeat across events
        note_idx = 0
        for event in events:
            chord = chord_at(chords, event.onset) or last_chord
            last_chord = chord

            base_idx = note_idx % len(motive_pitches)
            pitch = motive_pitches[base_idx]

            # Development
            if self.development == "transpose" and note_idx >= len(motive_pitches):
                # Transpose up by a step each repetition
                rep = note_idx // len(motive_pitches)
                pitch = pitch + rep * 2
                pitch = max(low, min(high, pitch))
            elif self.development == "invert" and note_idx >= len(motive_pitches):
                # Mirror each interval around the first note: inverted[i] = 2*P[0] - P[i]
                pitch = 2 * motive_pitches[0] - motive_pitches[base_idx]
                pitch = max(low, min(high, pitch))
            elif self.development == "retrograde":
                rev_idx = (len(motive_pitches) - 1) - base_idx
                pitch = motive_pitches[rev_idx]

            vel = int((65 + self.params.density * 30) * event.velocity_factor)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, vel)),
                )
            )
            note_idx += 1

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
            events.append(RhythmEvent(onset=round(t, 6), duration=0.45))
            t += 0.5
        return events

    def _velocity(self) -> int:
        return int(65 + self.params.density * 30)
