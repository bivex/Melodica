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
generators/call_response.py — CallResponseGenerator.

Blues/jazz/funk question-answer phrasing.
Call phrase ascends or builds tension, response resolves.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class CallResponseGenerator(PhraseGenerator):
    """
    Generates call-and-response phrases.

    call_length:    beats for the call phrase
    response_length: beats for the response phrase
    call_direction:  "up" | "down" | "random"
    response_direction: "up" | "down" | "random" (usually opposite of call)
    """

    name: str = "Call Response Generator"
    call_length: float = 2.0
    response_length: float = 2.0
    call_direction: str = "up"
    response_direction: str = "down"
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        call_length: float = 2.0,
        response_length: float = 2.0,
        call_direction: str = "up",
        response_direction: str = "down",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.call_length = max(0.5, call_length)
        self.response_length = max(0.5, response_length)
        self.call_direction = call_direction
        self.response_direction = response_direction
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

        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        mid = (low + high) // 2

        last_chord = chords[0]
        t = 0.0
        prev_pitch = mid
        if context and context.prev_pitch is not None:
            prev_pitch = context.prev_pitch

        while t < duration_beats:
            chord = chord_at(chords, t) or last_chord
            last_chord = chord

            # Call phrase
            call_notes = self._generate_phrase(
                chords,
                key,
                t,
                min(self.call_length, duration_beats - t),
                prev_pitch,
                self.call_direction,
            )
            notes.extend(call_notes)
            t += self.call_length
            if call_notes:
                prev_pitch = call_notes[-1].pitch

            if t >= duration_beats:
                break

            # Response phrase
            resp_notes = self._generate_phrase(
                chords,
                key,
                t,
                min(self.response_length, duration_beats - t),
                prev_pitch,
                self.response_direction,
            )
            notes.extend(resp_notes)
            t += self.response_length
            if resp_notes:
                prev_pitch = resp_notes[-1].pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    def _generate_phrase(
        self,
        chords: list[ChordLabel],
        key: Scale,
        start: float,
        length: float,
        anchor_pitch: int,
        direction: str,
    ) -> list[NoteInfo]:
        """Generate a single call or response phrase."""
        if length <= 0:
            return []

        events = self._build_events(length)
        notes: list[NoteInfo] = []
        prev = anchor_pitch
        low = self.params.key_range_low
        high = self.params.key_range_high

        for i, event in enumerate(events):
            onset = start + event.onset
            chord = chord_at(chords, onset)
            if chord is None:
                continue

            if direction == "up":
                step = random.choice([1, 1, 2, 2, 3])
            elif direction == "down":
                step = random.choice([-1, -1, -2, -2, -3])
            else:
                step = random.choice([-2, -1, 1, 2])

            pitch = prev + step

            # Snap to key
            if not key.contains(pitch % 12):
                pitch = nearest_pitch(chord.root, pitch)

            # Clamp
            pitch = max(low, min(high, pitch))

            # Call = building tension (crescendo), response = release
            if direction == "up":
                vel = int(60 + (i / max(1, len(events))) * 40)
            else:
                vel = int(90 - (i / max(1, len(events))) * 30)
            vel = int(vel * event.velocity_factor)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, vel)),
                )
            )
            prev = pitch

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
