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
generators/riff.py — RiffGenerator.

Rock/Metal riff generator using pentatonic scales, palm mute patterns,
and power chord rhythms.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE
from melodica.utils import nearest_pitch, chord_at, snap_to_scale

# Minor pentatonic intervals from root: 0, 3, 5, 7, 10
MINOR_PENT = [0, 3, 5, 7, 10]
# Blues scale: minor pentatonic + b5
BLUES = [0, 3, 5, 6, 7, 10]

# Built-in riff rhythm patterns (duration in 16ths)
RIFF_PATTERNS: dict[str, list[float]] = {
    "straight_8ths": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
    "gallop": [0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5],
    "palm_mute": [0.5, 0.5, 0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5, 1.0],
    "syncopated": [0.5, 0.75, 0.25, 0.5, 0.5, 0.75, 0.25, 0.5],
    "punk": [0.5, 0.5, 1.0, 0.5, 0.5, 1.0],
}


@dataclass
class RiffGenerator(PhraseGenerator):
    """
    Generates rock/metal riffs using pentatonic scales and power chord patterns.

    scale_type:     "minor_pent" | "blues"
    riff_pattern:   named rhythm pattern or custom durations
    palm_mute_prob: probability that a note is palm-muted (shorter, lower vel)
    power_chord:    if True, add octave doubling (root + octave)
    """

    name: str = "Riff Generator"
    scale_type: str = "minor_pent"
    riff_pattern: str | list[float] = "gallop"
    palm_mute_prob: float = 0.3
    power_chord: bool = True
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        scale_type: str = "minor_pent",
        riff_pattern: str | list[float] = "gallop",
        palm_mute_prob: float = 0.3,
        power_chord: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.scale_type = scale_type
        self.riff_pattern = riff_pattern
        self.palm_mute_prob = max(0.0, min(1.0, palm_mute_prob))
        self.power_chord = power_chord
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

        # Pentatonic scale degrees
        intervals = MINOR_PENT if self.scale_type == "minor_pent" else BLUES

        # Starting pitch — low register
        anchor = max(36, self.params.key_range_low)

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Pick a pentatonic note relative to chord root
            root_pc = chord.root
            interval = random.choice(intervals)
            pitch = nearest_pitch((root_pc + interval) % 12, anchor)

            # Clamp and snap to scale
            pitch = snap_to_scale(
                max(self.params.key_range_low, min(self.params.key_range_high, pitch)), key
            )

            # Palm mute check
            is_muted = random.random() < self.palm_mute_prob
            if is_muted:
                dur = event.duration * 0.4
                vel = int(50 + self.params.density * 20)
            else:
                dur = event.duration * 0.9
                vel = int(80 + self.params.density * 30)

            vel = int(vel * event.velocity_factor)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=round(dur, 6),
                    velocity=max(1, min(127, vel)),
                )
            )

            # Power chord doubling
            if self.power_chord and not is_muted:
                octave_pitch = pitch + OCTAVE
                if octave_pitch <= self.params.key_range_high:
                    notes.append(
                        NoteInfo(
                            pitch=octave_pitch,
                            start=round(event.onset, 6),
                            duration=round(dur, 6),
                            velocity=max(1, min(127, vel - 10)),
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
        # Build from riff pattern
        if isinstance(self.riff_pattern, str) and self.riff_pattern in RIFF_PATTERNS:
            durs = RIFF_PATTERNS[self.riff_pattern]
        elif isinstance(self.riff_pattern, list):
            durs = self.riff_pattern
        else:
            durs = RIFF_PATTERNS["straight_8ths"]

        t, events, idx = 0.0, [], 0
        while t < duration_beats:
            d = durs[idx % len(durs)]
            if t + d > duration_beats:
                break
            events.append(RhythmEvent(onset=round(t, 6), duration=round(d * 0.9, 6)))
            t += d
            idx += 1
        return events

    def _velocity(self) -> int:
        return int(75 + self.params.density * 30)
