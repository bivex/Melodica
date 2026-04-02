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
generators/guitar_strumming.py — Advanced guitar strumming generator.

Layer: Application / Domain

Produces guitar strum patterns with dynamics, palm mutes, and dead strums.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, build_guitar_voicing


STRUM_PATTERNS = {"folk", "pop", "reggae", "funk", "ballad"}

_PATTERN_DIRS: dict[str, list[int]] = {
    "folk": [1, -1, 1, -1, 1, -1, 1, -1],
    "pop": [1, 0, -1, 1, -1, 0, 1, -1],
    "reggae": [0, -1, 0, 1, 0, -1, 0, 1],
    "funk": [1, 2, -1, 1, 2, -1, 1, 2],
    "ballad": [1, 0, 0, -1, 0, 0, 1, 0],
}


@dataclass
class GuitarStrummingGenerator(PhraseGenerator):
    name: str = "Guitar Strumming"
    strum_pattern: str = "folk"
    palm_mute_ratio: float = 0.2
    accent_velocity: float = 1.2
    dead_strums: bool = True
    strum_delay: float = 0.015
    string_count: int = 6
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        strum_pattern: str = "folk",
        palm_mute_ratio: float = 0.2,
        accent_velocity: float = 1.2,
        dead_strums: bool = True,
        strum_delay: float = 0.015,
        string_count: int = 6,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if strum_pattern not in STRUM_PATTERNS:
            raise ValueError(
                f"strum_pattern must be one of {STRUM_PATTERNS}; got {strum_pattern!r}"
            )
        self.strum_pattern = strum_pattern
        self.palm_mute_ratio = max(0.0, min(1.0, palm_mute_ratio))
        self.accent_velocity = max(0.5, min(2.0, accent_velocity))
        self.dead_strums = dead_strums
        self.strum_delay = max(0.0, strum_delay)
        self.string_count = max(1, min(6, string_count))
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
        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        last_chord: ChordLabel | None = None
        directions = _PATTERN_DIRS.get(self.strum_pattern, _PATTERN_DIRS["folk"])
        seq_idx = 0

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord
            direction = directions[seq_idx % len(directions)]
            seq_idx += 1
            if direction == 0:
                continue

            base_vel = int(self._velocity() * event.velocity_factor)

            if direction == 2:
                if self.dead_strums:
                    dead_vel = int(base_vel * 0.5)
                    for s in range(min(3, self.string_count)):
                        p = nearest_pitch(chord.root, self.params.key_range_low + 12)
                        notes.append(
                            NoteInfo(
                                pitch=max(
                                    self.params.key_range_low, min(self.params.key_range_high, p)
                                ),
                                start=round(event.onset + s * 0.005, 6),
                                duration=0.03,
                                velocity=max(1, min(MIDI_MAX, dead_vel)),
                                articulation="staccato",
                            )
                        )
                continue

            voicing = build_guitar_voicing(chord, anchor=max(40, self.params.key_range_low))
            voicing = voicing[: self.string_count]
            if direction < 0:
                voicing = list(reversed(voicing))

            is_muted = random.random() < self.palm_mute_ratio
            is_accent = (seq_idx - 1) % len(directions) == 0
            vel = int(base_vel * (self.accent_velocity if is_accent else 1.0))

            for i, pitch in enumerate(voicing):
                delay = i * self.strum_delay
                strum_dur = 0.25 if is_muted else event.duration - delay
                notes.append(
                    NoteInfo(
                        pitch=max(
                            self.params.key_range_low, min(self.params.key_range_high, pitch)
                        ),
                        start=round(event.onset + delay, 6),
                        duration=round(max(0.04, strum_dur), 6),
                        velocity=max(0, min(MIDI_MAX, vel)),
                        articulation="staccato" if is_muted else None,
                    )
                )

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
            is_downbeat = (t % 4.0) < 0.01
            events.append(
                RhythmEvent(
                    onset=round(t, 6),
                    duration=round(0.45, 6),
                    velocity_factor=1.0 if is_downbeat else 0.8,
                )
            )
            t += 0.5
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 40)
