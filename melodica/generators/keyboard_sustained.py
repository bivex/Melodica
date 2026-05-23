# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/keyboard_sustained.py — Keyboard, Reed, and wind organs.
Implements highly professional, register-aware generators for Church Organ, Accordion,
Tango Accordion, and Harmonica.
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


class _KeyboardSustainedBase(PhraseGenerator, ABC):
    """Abstract base class for all keyboard wind and reed generators."""
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


class ChurchOrganGenerator(_KeyboardSustainedBase):
    """
    Pipe/Church Organ generator (GM 19).
    Includes virtual stop configurations.
    """
    name: str = "Church Organ Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        stops: str = "diapason",  # diapason, principal, mixture, full
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.stops = stops
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

            vel = self._velocity(85)
            # Organ notes are held extremely long (perfect legato/sustained)
            duration = chord.duration * 0.98

            # Build full pipe organ stops:
            # Principal = root, Octave = root+12, Mixture = fifth+19
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, nearest_pitch(pcs[0], mid)))
            
            notes.append(NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(duration, 6),
                velocity=vel,
            ))

            if self.stops in ("principal", "full"):
                notes.append(NoteInfo(
                    pitch=pitch + 12,
                    start=round(chord.start, 6),
                    duration=round(duration, 6),
                    velocity=max(1, vel - 10),
                ))

            if self.stops in ("mixture", "full"):
                notes.append(NoteInfo(
                    pitch=pitch + 19,
                    start=round(chord.start, 6),
                    duration=round(duration, 6),
                    velocity=max(1, vel - 15),
                ))

        return sorted(notes, key=lambda x: x.start)


class AccordionGenerator(_KeyboardSustainedBase):
    """
    Accordion & Tango Accordion generator (GM 21, 23).
    Simulates accordion bellow sweeps.
    """
    name: str = "Accordion Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        register: str = "master",  # master, bassoon, clarinet, musette
        tango_mode: bool = False,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.register = register
        self.tango_mode = tango_mode
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

            vel = self._velocity(75)
            pitch = nearest_pitch(pcs[0], mid)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            dur = chord.duration * 0.9

            # Expression CC 11 representing Bellows pressure curve
            expression = {}
            expression[11] = [(0.0, 50), (dur * 0.4, 95), (dur * 0.8, 45), (dur, 30)]

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=vel,
            )
            note.expression = expression
            notes.append(note)

            # Musette or master registers include detuned voices or octaves
            if self.register in ("master", "musette"):
                # Musette wet tuning (detune voice)
                notes.append(NoteInfo(
                    pitch=pitch + 12,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=max(1, vel - 12),
                ))

        return sorted(notes, key=lambda x: x.start)


class HarmonicaGenerator(_KeyboardSustainedBase):
    """
    Harmonica generator (GM 22).
    Simulates blow/draw reed articulations and expressive pitch bends.
    """
    name: str = "Harmonica Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        blues_harp: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.blues_harp = blues_harp
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
            prev_pitch = pitch

            vel = self._velocity(80)
            dur = chord.duration * 0.85

            # Expressive harmonica pitch bends (CC 13) and blow/draw reed shifts
            expression = {}
            if self.blues_harp and random.random() < 0.4:
                # Blues pitch bend
                expression[101] = [(0.0, 64), (dur * 0.3, 85), (dur * 0.7, 64)]

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=vel,
            )
            if expression:
                note.expression = expression
            notes.append(note)

        return sorted(notes, key=lambda x: x.start)
