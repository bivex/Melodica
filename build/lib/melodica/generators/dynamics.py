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
generators/dynamics.py — Dynamics curve generator.

Creates velocity/dynamics envelopes across phrases. Unlike post-processing
modifiers, this is a standalone generator that outputs notes with a
contoured velocity pattern, useful for pads, drones, and textural layers.

Curve types:
    "crescendo"    — gradual increase
    "decrescendo"  — gradual decrease
    "swell"        — increase then decrease (arch)
    "sforzando"    — sudden accent then drop
    "terraced"     — alternating forte/piano
    "exponential"  — exponential crescendo
    "sawtooth"     — sawtooth up/down pattern
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


def _curve_value(curve: str, position: float, strength: float = 1.0) -> float:
    """Return velocity factor (0.0-1.0) at position (0.0-1.0)."""
    p = max(0.0, min(1.0, position))
    s = max(0.1, min(2.0, strength))

    if curve == "crescendo":
        return 0.4 + 0.6 * (p ** (1.0 / s))
    elif curve == "decrescendo":
        return 1.0 - 0.6 * (p ** (1.0 / s))
    elif curve == "swell":
        return 0.4 + 0.6 * math.sin(p * math.pi) ** s
    elif curve == "sforzando":
        if p < 0.1:
            return 1.0
        return 0.4 + 0.2 * math.exp(-p * 3)
    elif curve == "terraced":
        return 1.0 if int(p * 4) % 2 == 0 else 0.5
    elif curve == "exponential":
        return 0.3 + 0.7 * (p**3)
    elif curve == "sawtooth":
        return 0.4 + 0.6 * (1.0 - (p * 3 % 1.0))
    return 0.7


@dataclass
class DynamicsCurveGenerator(PhraseGenerator):
    """
    Dynamics curve generator.

    Outputs notes with velocity shaped by a contoured envelope.

    curve_type:
        Shape of the velocity envelope.
    note_duration:
        Duration of each note in beats.
    pitch_strategy:
        "chord_tone", "scale_tone", "root", "fifth".
    strength:
        Curvature intensity (0.1 = subtle, 2.0 = extreme).
    velocity_range:
        Tuple of (min, max) velocity.
    """

    name: str = "Dynamics Curve Generator"
    curve_type: str = "crescendo"
    note_duration: float = 1.0
    pitch_strategy: str = "chord_tone"
    strength: float = 1.0
    velocity_range: tuple[int, int] = (30, 110)
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        curve_type: str = "crescendo",
        note_duration: float = 1.0,
        pitch_strategy: str = "chord_tone",
        strength: float = 1.0,
        velocity_range: tuple[int, int] = (30, 110),
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if curve_type not in (
            "crescendo",
            "decrescendo",
            "swell",
            "sforzando",
            "terraced",
            "exponential",
            "sawtooth",
        ):
            raise ValueError(f"Unknown curve_type: {curve_type!r}")
        self.curve_type = curve_type
        self.note_duration = max(0.125, note_duration)
        self.pitch_strategy = pitch_strategy
        self.strength = max(0.1, min(2.0, strength))
        self.velocity_range = velocity_range
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
        t = 0.0

        while t < duration_beats:
            chord = chord_at(chords, t)
            position = t / max(0.1, duration_beats)
            factor = _curve_value(self.curve_type, position, self.strength)
            vel_min, vel_max = self.velocity_range
            vel = max(1, min(127, int(vel_min + (vel_max - vel_min) * factor)))

            pitch = self._pick_pitch(chord, key)
            dur = min(self.note_duration, duration_beats - t)
            notes.append(NoteInfo(pitch=pitch, start=round(t, 6), duration=dur, velocity=vel))
            t += self.note_duration

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes

    def _pick_pitch(self, chord: ChordLabel, key: Scale) -> int:
        pcs = chord.pitch_classes()
        if not pcs:
            return key.root * 12 + 60
        if self.pitch_strategy == "root":
            return nearest_pitch(pcs[0], 60)
        if self.pitch_strategy == "fifth":
            return nearest_pitch((pcs[0] + 7) % 12, 60)
        if self.pitch_strategy == "scale_tone":
            degrees = key.degrees()
            if degrees:
                return nearest_pitch(int(random.choice(degrees)) % 12, 60)
        return nearest_pitch(random.choice(pcs), 60)
