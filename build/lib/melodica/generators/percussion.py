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
generators/percussion.py — PercussionGenerator.

Multi-instrument drum patterns with independent rhythm per instrument.
Standard GM drum map (MIDI notes 35-81).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale

# GM Drum map key names
DRUM_NAMES: dict[str, int] = {
    "kick": 36,
    "snare": 38,
    "hihat_closed": 42,
    "hihat_open": 46,
    "tom_lo": 41,
    "tom_mid": 45,
    "tom_hi": 50,
    "crash": 49,
    "ride": 51,
    "clap": 39,
    "rim": 37,
    "cowbell": 56,
    "tambourine": 54,
    "shaker": 70,
    "conga_lo": 64,
    "conga_hi": 63,
}

# Preset patterns per instrument (16-step grid, 1=hit, 0=rest)
DRUM_PATTERNS: dict[str, dict[str, list[int]]] = {
    "rock": {
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "snare": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        "hihat_closed": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    "funk": {
        "kick": [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
        "snare": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0],
        "hihat_closed": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    },
    "hiphop": {
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat_closed": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1],
    },
    "bossa": {
        "kick": [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0],
        "rim": [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0],
        "hihat_closed": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
}


@dataclass
class PercussionGenerator(PhraseGenerator):
    """
    Multi-instrument percussion generator.

    pattern_name: preset name ("rock", "funk", "hiphop", "bossa")
    instruments:  list of drum names to include (None = use all from preset)
    velocity_humanize: random velocity jitter
    """

    name: str = "Percussion Generator"
    pattern_name: str = "rock"
    instruments: list[str] | None = None
    velocity_humanize: int = 10
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern_name: str = "rock",
        instruments: list[str] | None = None,
        velocity_humanize: int = 10,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern_name = pattern_name
        self.instruments = instruments
        self.velocity_humanize = max(0, velocity_humanize)
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

        pattern = DRUM_PATTERNS.get(self.pattern_name, DRUM_PATTERNS["rock"])
        notes: list[NoteInfo] = []
        step_dur = 0.25  # 16th notes

        # Select instruments
        if self.instruments:
            instruments = {k: v for k, v in pattern.items() if k in self.instruments}
        else:
            instruments = pattern

        t = 0.0
        while t < duration_beats:
            for drum_name, steps in instruments.items():
                midi_note = DRUM_NAMES.get(drum_name, 36)
                step_idx = int((t / step_dur)) % len(steps)

                if steps[step_idx] == 1:
                    base_vel = 90 if step_idx % 4 == 0 else 70  # downbeat accent
                    vel = base_vel + random.randint(-self.velocity_humanize, self.velocity_humanize)
                    notes.append(
                        NoteInfo(
                            pitch=midi_note,
                            start=round(t, 6),
                            duration=round(step_dur * 0.8, 6),
                            velocity=max(1, min(127, vel)),
                        )
                    )

            t += step_dur

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )

        return notes

    def _velocity(self) -> int:
        return int(75 + self.params.density * 25)
