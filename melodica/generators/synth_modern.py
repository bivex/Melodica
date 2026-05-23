# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/synth_modern.py — Modern Electronic Synth Leads and Pads.
Implements highly professional, register-aware generators for Synth Lead and Synth Pad.
"""

from __future__ import annotations

import random
import math
from abc import ABC
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


class _SynthModernBase(PhraseGenerator, ABC):
    """Abstract base class for all modern synth generators."""
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
        return max(1, min(127, base_val + random.randint(-8, 8)))


class SynthLeadGenerator(_SynthModernBase):
    """
    Solo Synth Lead generator (GM 80-87).
    Supports portamento monophonic glides.
    """
    name: str = "Synth Lead Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        lead_type: str = "sawtooth",  # square, sawtooth, calliope, chiff
        glide_speed: float = 0.1,  # slide duration in beats
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.lead_type = lead_type
        self.glide_speed = glide_speed
        self.note_density = note_density

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

            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            vel = self._velocity(90)
            dur = chord.duration * 0.95

            # Expressive filter sweeps (CC 74) and monophonic pitch portamento sweeps (CC 5)
            expression = {}
            if self.glide_speed > 0 and pitch != prev_pitch:
                # Add slide / glide effect
                expression[5] = [(0.0, 40), (self.glide_speed, 90)]
                
            # Filter sweeps
            expression[74] = [(0.0, 50), (dur * 0.5, 110), (dur, 60)]

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=vel,
            )
            note.expression = expression
            notes.append(note)

            prev_pitch = pitch

        return sorted(notes, key=lambda x: x.start)


class SynthPadGenerator(_SynthModernBase):
    """
    Synth Pad generator (GM 88-95).
    Generates thick ambient structures and rich octaves.
    """
    name: str = "Synth Pad Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pad_type: str = "warm",  # new_age, warm, polysynth, halo
        swell: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.pad_type = pad_type
        self.swell = swell
        self.note_density = note_density

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

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            vel = self._velocity(70)
            dur = chord.duration * 0.98

            # Build thick ambient chord voicing (Root, 5th, Octave, 10th)
            voicing = []
            voicing.append(max(self.params.key_range_low, min(self.params.key_range_high, nearest_pitch(pcs[0], mid - 12))))
            if len(pcs) > 1:
                voicing.append(max(self.params.key_range_low, min(self.params.key_range_high, nearest_pitch(pcs[1], mid))))
            voicing.append(max(self.params.key_range_low, min(self.params.key_range_high, nearest_pitch(pcs[0], mid + 12))))

            # Expression CC 11 representing slow volume pad swells
            expression = {}
            if self.swell:
                expression[11] = [(0.0, 30), (dur * 0.4, 90), (dur * 0.8, 60), (dur, 20)]

            for pitch in voicing:
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                )
                if expression:
                    note.expression = expression.copy()
                notes.append(note)

        return sorted(notes, key=lambda x: x.start)
