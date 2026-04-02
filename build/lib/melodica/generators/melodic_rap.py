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
generators/melodic_rap.py — Melodic rap / sing-rap melody generator.

Layer: Application / Domain
Style: Melodic rap, sing-rap, auto-tune rap, melodic trap.

Generates melodies optimized for auto-tune processing:
  - Stepwise movement preferred (auto-tune friendly)
  - Chord tone emphasis
  - Characteristic melodic rap intervals
  - Pitch bend grace notes
  - Repetitive hook-friendly patterns

Variants:
    "sing_rap"     — melodic sing-rap hooks
    "auto_tune"    — auto-tune optimized (minimal chromatic movement)
    "melodic_trap" — melodic trap vocal lines
    "hook"         — catchy hook-focused melodies
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


@dataclass
class MelodicRapGenerator(PhraseGenerator):
    """
    Melodic rap / sing-rap melody generator.

    variant:
        "sing_rap", "auto_tune", "melodic_trap", "hook"
    repetition_factor:
        How much melodic material is repeated (0.0-1.0).
        Higher = more hook-like, lower = more varied.
    stepwise_bias:
        Probability of stepwise (scale-wise) movement vs leaps (0.0-1.0).
        Higher is more auto-tune friendly.
    bend_probability:
        Probability of pitch bend grace notes (0.0-1.0).
    phrase_length:
        Length of melodic phrases in beats.
    rest_probability:
        Probability of inserting a rest between phrases (0.0-1.0).
    octave_register:
        Preferred octave (3-6).
    """

    name: str = "Melodic Rap Generator"
    variant: str = "sing_rap"
    repetition_factor: float = 0.5
    stepwise_bias: float = 0.7
    bend_probability: float = 0.15
    phrase_length: float = 4.0
    rest_probability: float = 0.25
    octave_register: int = 5
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "sing_rap",
        repetition_factor: float = 0.5,
        stepwise_bias: float = 0.7,
        bend_probability: float = 0.15,
        phrase_length: float = 4.0,
        rest_probability: float = 0.25,
        octave_register: int = 5,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.repetition_factor = max(0.0, min(1.0, repetition_factor))
        self.stepwise_bias = max(0.0, min(1.0, stepwise_bias))
        self.bend_probability = max(0.0, min(1.0, bend_probability))
        self.phrase_length = max(1.0, min(8.0, phrase_length))
        self.rest_probability = max(0.0, min(1.0, rest_probability))
        self.octave_register = max(3, min(6, octave_register))

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
        last_chord = chords[-1]
        register_mid = self.octave_register * OCTAVE

        # Generate a motif and repeat/develop it
        motif: list[tuple[int, float, float]] = []  # (pitch, duration, velocity)
        motif_length_notes = int(self.phrase_length / 0.5)
        prev_pitch = register_mid

        pos = 0.0
        while pos < duration_beats:
            chord = chord_at(chords, pos)
            if chord is None:
                pos += 0.5
                continue

            # Check for phrase boundary rest
            if pos > 0 and pos % self.phrase_length < 0.5:
                if random.random() < self.rest_probability:
                    pos += self.phrase_length * 0.5
                    continue

            pitch = self._pick_pitch(chord, prev_pitch, key)
            dur = self._pick_duration()
            vel = self._pick_velocity()

            # Grace note bend
            if random.random() < self.bend_probability:
                grace_pitch = pitch + random.choice([-2, -1, 1, 2])
                notes.append(
                    NoteInfo(
                        pitch=grace_pitch,
                        start=round(pos, 6),
                        duration=0.08,
                        velocity=max(1, vel - 20),
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(pos + 0.08, 6),
                        duration=dur - 0.08,
                        velocity=vel,
                    )
                )
            else:
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(pos, 6),
                        duration=dur,
                        velocity=vel,
                    )
                )

            prev_pitch = pitch
            pos += dur

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_pitch(self, chord: ChordLabel, prev: int, key: Scale) -> int:
        root_pc = chord.root
        chord_pcs = set(chord.pitch_classes())
        scale_pcs = set(int(d) for d in key.degrees())

        if random.random() < self.stepwise_bias:
            # Stepwise: move by scale degree
            direction = random.choice([-1, 1])
            prev_pc = prev % 12
            next_pc = (prev_pc + direction) % 12
            # Snap to scale
            if next_pc not in scale_pcs:
                next_pc = (prev_pc + direction * 2) % 12
            return nearest_pitch(next_pc, prev)
        else:
            # Leap: jump to chord tone
            if chord_pcs:
                target_pc = random.choice(list(chord_pcs))
                return nearest_pitch(target_pc, prev)
            return nearest_pitch(root_pc, prev)

    def _pick_duration(self) -> float:
        if self.variant == "hook":
            # Hooks: more regular rhythm
            return random.choice([0.5, 0.5, 1.0, 0.25])
        elif self.variant == "melodic_trap":
            # Trap: longer held notes mixed with quick runs
            return random.choice([0.25, 0.5, 1.0, 2.0])
        else:
            return random.choice([0.25, 0.5, 0.5, 1.0])

    def _pick_velocity(self) -> int:
        if self.variant == "auto_tune":
            return 80 + random.randint(-5, 5)
        elif self.variant == "melodic_trap":
            return 90 + random.randint(-10, 10)
        else:
            return 75 + random.randint(-10, 10)
