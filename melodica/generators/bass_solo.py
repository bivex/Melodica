# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/bass_solo.py — Professional register-aware solo bass generators.
Implements dedicated generators for Acoustic Bass (32), Finger Bass (33), Pick Bass (34),
Fretless Bass (35), Slap Bass 1 & 2 (36-37), and Synth Bass 1 & 2 (38-39).
"""

from __future__ import annotations

import random
import math
from abc import ABC

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


class _BassSoloBase(PhraseGenerator, ABC):
    """Abstract base class for all solo bass generators."""
    note_density: float = 1.0

    def _apply_note_density(self, chords: list[ChordLabel]) -> list[ChordLabel]:
        note_density = getattr(self, "note_density", 1.0)
        if not chords or note_density == 1.0:
            return chords
        
        if note_density <= 0.0:
            return []
        
        if note_density < 1.0:
            new_chords = []
            for i, chord in enumerate(chords):
                prev_val = int((i - 1) * note_density) if i > 0 else -1
                curr_val = int(i * note_density)
                if curr_val > prev_val:
                    new_chords.append(chord)
            return new_chords
        
        subdivisions = max(1, round(note_density))
        if subdivisions <= 1:
            return chords
            
        import dataclasses
        new_chords = []
        for chord in chords:
            sub_dur = chord.duration / subdivisions
            for s in range(subdivisions):
                new_chord = dataclasses.replace(
                    chord,
                    start=chord.start + s * sub_dur,
                    duration=sub_dur
                )
                new_chords.append(new_chord)
        return new_chords

    def _velocity(self, base_val: int) -> int:
        if self.params.velocity_range:
            v_min, v_max = self.params.velocity_range
            return random.randint(v_min, v_max)
        return max(1, min(127, base_val + random.randint(-6, 6)))


class BassSoloGenerator(_BassSoloBase):
    """
    Unified solo Bass Generator covering all 8 GM Bass instruments.
    """
    name: str = "Bass Solo Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "finger",  # acoustic, finger, pick, fretless, slap_1, slap_2, synth_1, synth_2
        style: str = "groove",  # groove, sustained
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = instrument
        self.style = style
        self.note_density = note_density
        # Default key range for bass: C1 (24) to G3 (55)
        self.params.key_range_low = max(24, self.params.key_range_low)
        self.params.key_range_high = min(55, self.params.key_range_high)

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        prev_pitch = mid

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            # Base pitch: prioritize roots
            root_pc = pcs[0]
            pitch = nearest_pitch(root_pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            # Custom instrument properties:
            if self.instrument == "acoustic":
                vel = self._velocity(68)  # soft, deep woody attack
                dur = chord.duration * 0.9
            elif self.instrument == "finger":
                vel = self._velocity(74)  # round, solid round finger attack
                dur = chord.duration * 0.85
            elif self.instrument == "pick":
                vel = self._velocity(84)  # punchy pick attack
                dur = chord.duration * 0.8
            elif self.instrument == "fretless":
                vel = self._velocity(72)
                dur = chord.duration * 0.95
            elif self.instrument in ("slap_1", "slap_2"):
                vel = self._velocity(82)
                dur = chord.duration * 0.75
            elif self.instrument in ("synth_1", "synth_2"):
                vel = self._velocity(80)
                dur = chord.duration * 0.92
            else:
                vel = self._velocity(75)
                dur = chord.duration * 0.85

            if self.style == "sustained":
                dur = chord.duration * 0.98

            expression = {}

            # Fretless: Singing volume and "mwah" swells
            if self.instrument == "fretless":
                expression[11] = [(0.0, 55), (dur * 0.3, 95), (dur * 0.7, 75), (dur, 50)]
            # Synth 1: Analog filter sweep on CC 74
            elif self.instrument == "synth_1":
                expression[74] = [(0.0, 45), (dur * 0.5, 105), (dur, 60)]
            # Synth 2: Sub wobble LFO sweep on CC 11
            elif self.instrument == "synth_2":
                step = 0.05
                expr_points = []
                t = 0.0
                while t < dur:
                    val = int(80 + 20 * math.sin(t * 5.0 * 2.0 * math.pi))
                    expr_points.append((t, val))
                    t += step
                if expr_points:
                    expression[11] = expr_points

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=vel,
            )
            if expression:
                note.expression = expression
            notes.append(note)

            # Slap & Pop: Add high popped octave note on accented beats / randomly 35% of notes
            if self.instrument in ("slap_1", "slap_2") and random.random() < 0.35:
                pop_pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 12))
                pop_vel = max(1, min(127, vel + (30 if self.instrument == "slap_2" else 20)))
                notes.append(NoteInfo(
                    pitch=pop_pitch,
                    start=round(chord.start + dur * 0.5, 6),
                    duration=0.1,  # extremely short popped transient
                    velocity=pop_vel,
                ))

            # Pick click simulation: layer a tiny, very quiet high transient click
            if self.instrument == "pick" and random.random() < 0.5:
                click_pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 24))
                notes.append(NoteInfo(
                    pitch=click_pitch,
                    start=round(chord.start, 6),
                    duration=0.04,  # ultra short pick noise
                    velocity=max(1, vel - 35),
                ))

        return sorted(notes, key=lambda x: x.start)
