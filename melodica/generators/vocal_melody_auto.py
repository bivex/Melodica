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
generators/vocal_melody_auto.py — Vocal melody generator optimized for auto-tune.

Layer: Application / Domain
Style: Auto-tune pop, melodic rap, Travis Scott style, T-Pain style.

Generates melodies specifically designed for auto-tune processing:
  - Minimizes chromatic passing tones
  - Prefers chord tones and scale degrees
  - Characteristic melodic intervals (octave jumps, 5ths)
  - Pitch bend grace notes for expression
  - Sustained notes for auto-tune lock-on

Variants:
    "travis"    — Travis Scott style (dark, atmospheric, octave jumps)
    "tpain"     — T-Pain style (bright, major, catchy)
    "future"    — Future style (minor, melodic trap)
    "don_toliver" — Don Toliver style (smooth, R&B influenced)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


@dataclass
class VocalMelodyAutoGenerator(PhraseGenerator):
    """
    Vocal melody generator optimized for auto-tune processing.

    variant:
        "travis", "tpain", "future", "don_toliver"
    register:
        Preferred vocal register: "low" (C3-C4), "mid" (C4-C5), "high" (C5-C6).
    sustain_preference:
        Preference for longer sustained notes (0.0-1.0).
        Higher = more sustained, better for auto-tune lock-on.
    octave_jump_probability:
        Probability of characteristic octave jumps (0.0-1.0).
    grace_note_probability:
        Probability of pitch-bend grace notes (0.0-1.0).
    repetition_amount:
        How much melodic material is repeated (0.0-1.0).
    """

    name: str = "Vocal Melody Auto-Tune Generator"
    variant: str = "travis"
    register: str = "mid"
    sustain_preference: float = 0.5
    octave_jump_probability: float = 0.15
    grace_note_probability: float = 0.2
    repetition_amount: float = 0.4
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "travis",
        register: str = "mid",
        sustain_preference: float = 0.5,
        octave_jump_probability: float = 0.15,
        grace_note_probability: float = 0.2,
        repetition_amount: float = 0.4,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.register = register
        self.sustain_preference = max(0.0, min(1.0, sustain_preference))
        self.octave_jump_probability = max(0.0, min(1.0, octave_jump_probability))
        self.grace_note_probability = max(0.0, min(1.0, grace_note_probability))
        self.repetition_amount = max(0.0, min(1.0, repetition_amount))

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
        register_mid = self._get_register_mid()

        # Generate motif
        motif: list[tuple[int, float, int]] = []  # (pitch, duration, velocity)
        motif_bars = 2
        motif_beats = motif_bars * 4

        pos = 0.0
        prev_pitch = register_mid

        while pos < duration_beats:
            chord = chord_at(chords, pos)
            if chord is None:
                pos += 0.5
                continue

            # Check for motif repetition
            motif_pos = pos % motif_beats
            if motif and motif_pos < len(motif) * 0.5 and random.random() < self.repetition_amount:
                # Repeat motif element
                idx = int(motif_pos / 0.5) % len(motif)
                m_pitch, m_dur, m_vel = motif[idx]
                pitch = m_pitch
                dur = m_dur
                vel = m_vel
            else:
                pitch = self._pick_pitch(chord, prev_pitch, key)
                dur = self._pick_duration()
                vel = self._pick_velocity()

            # Octave jump
            if random.random() < self.octave_jump_probability:
                pitch += random.choice([-OCTAVE, OCTAVE])
                pitch = max(48, min(84, pitch))

            # Grace note
            if random.random() < self.grace_note_probability:
                grace_interval = random.choice([-2, -1, 1, 2])
                grace_pitch = pitch + grace_interval
                notes.append(
                    NoteInfo(
                        pitch=max(48, min(84, grace_pitch)),
                        start=round(pos, 6),
                        duration=0.06,
                        velocity=max(1, vel - 15),
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(pos + 0.06, 6),
                        duration=dur - 0.06,
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

            # Store in motif
            if pos < motif_beats:
                motif.append((pitch, dur, vel))

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

    def _get_register_mid(self) -> int:
        return {
            "low": 48,  # C3
            "mid": 60,  # C4
            "high": 72,  # C5
        }.get(self.register, 60)

    def _pick_pitch(self, chord: ChordLabel, prev: int, key: Scale) -> int:
        chord_pcs = set(chord.pitch_classes())
        scale_pcs = set(int(d) for d in key.degrees())

        # Auto-tune optimization: prefer chord tones
        if random.random() < 0.65:
            # Chord tone
            target_pc = random.choice(list(chord_pcs)) if chord_pcs else chord.root
            return nearest_pitch(target_pc, prev)
        elif random.random() < 0.85:
            # Scale tone (non-chord)
            available = scale_pcs - chord_pcs
            if available:
                target_pc = random.choice(list(available))
                return nearest_pitch(target_pc, prev)
            return nearest_pitch(chord.root, prev)
        else:
            # Stepwise from previous
            direction = random.choice([-1, 1])
            prev_pc = prev % 12
            next_pc = (prev_pc + direction) % 12
            if next_pc not in scale_pcs:
                next_pc = (prev_pc + direction * 2) % 12
            return nearest_pitch(next_pc, prev)

    def _pick_duration(self) -> float:
        if self.variant == "travis":
            # Travis: long sustained notes mixed with quick runs
            if random.random() < self.sustain_preference:
                return random.choice([1.0, 1.5, 2.0])
            return random.choice([0.25, 0.5])
        elif self.variant == "tpain":
            # T-Pain: rhythmic, medium duration
            return random.choice([0.5, 0.5, 1.0])
        elif self.variant == "future":
            # Future: short runs and sustained notes
            if random.random() < self.sustain_preference:
                return random.choice([1.0, 2.0])
            return random.choice([0.25, 0.5, 0.5])
        else:  # don_toliver
            # Don Toliver: smooth, longer notes
            return random.choice([0.5, 1.0, 1.0, 1.5])

    def _pick_velocity(self) -> int:
        if self.variant == "travis":
            return 85 + random.randint(-8, 8)
        elif self.variant == "tpain":
            return 90 + random.randint(-5, 5)
        elif self.variant == "future":
            return 80 + random.randint(-10, 10)
        else:
            return 75 + random.randint(-5, 5)
