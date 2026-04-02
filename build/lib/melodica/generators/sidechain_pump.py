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
generators/sidechain_pump.py — Sidechain compression pump effect generator.

Layer: Application / Domain
Style: EDM, house, future bass, pop production.

Simulates the "pumping" effect of sidechain compression by producing
notes with a velocity envelope that ducks on each beat subdivision.
The effect creates a rhythmic breathing quality in pads, synths,
and bass lines.

Rates:
    "1/4"  — pump on quarter notes
    "1/8"  — pump on eighth notes

The depth parameter controls how much velocity is reduced at the
low point of each pump cycle. Attack and release shape the
envelope curve.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class SidechainPumpGenerator(PhraseGenerator):
    """
    Sidechain compression pump effect generator.

    rate:
        Pump rate: "1/4" (quarter notes) or "1/8" (eighth notes).
    depth:
        How much velocity is ducked (0.0 = none, 1.0 = full mute).
    attack:
        Envelope attack time in beats for velocity recovery.
    release:
        Envelope release time in beats for velocity ducking.
    """

    name: str = "Sidechain Pump Generator"
    rate: str = "1/4"
    depth: float = 0.7
    attack: float = 0.01
    release: float = 0.2
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        rate: str = "1/4",
        depth: float = 0.7,
        attack: float = 0.01,
        release: float = 0.2,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if rate not in ("1/4", "1/8"):
            raise ValueError(f"rate must be '1/4' or '1/8'; got {rate!r}")
        self.rate = rate
        self.depth = max(0.0, min(1.0, depth))
        self.attack = max(0.001, min(1.0, attack))
        self.release = max(0.01, min(2.0, release))
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
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None
        pump_interval = 1.0 if self.rate == "1/4" else 0.5

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pcs = chord.pitch_classes()
            if not pcs:
                continue
            pc = random.choice(pcs)
            pitch = nearest_pitch(int(pc), prev_pitch)
            pitch = max(low, min(high, pitch))

            phase = event.onset % pump_interval
            vel_mod = self._pump_envelope(phase, pump_interval)
            vel = self._velocity(vel_mod)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, vel)),
                )
            )
            prev_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pump_envelope(self, phase: float, interval: float) -> float:
        if phase < self.release:
            return 1.0 - self.depth * (phase / self.release)
        recovery_start = interval - self.attack
        if phase >= recovery_start:
            t = (phase - recovery_start) / self.attack
            return 1.0 - self.depth * (1.0 - min(1.0, t))
        return 1.0 - self.depth

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        step = 1.0 if self.rate == "1/4" else 0.5
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=step * 0.9))
            t += step
        return events

    def _velocity(self, vel_mod: float) -> int:
        base = int(60 + self.params.density * 35)
        return max(1, min(127, int(base * vel_mod)))
