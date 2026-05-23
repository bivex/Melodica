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


class PercussiveOrganGenerator(_KeyboardSustainedBase):
    """
    Percussive Organ generator (GM 17).
    Simulates a Hammond-style organ with a sharp, fast percussive key click.
    """
    name: str = "Percussive Organ Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        click_octave_offset: int = 2,  # percussive click is usually 2 octaves higher
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.click_octave_offset = click_octave_offset
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

            vel = self._velocity(80)
            duration = chord.duration * 0.95

            # Main organ note
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, nearest_pitch(pcs[0], mid)))
            notes.append(NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(duration, 6),
                velocity=vel,
            ))

            # Percussive click: super short high-velocity transient note at a higher octave
            click_pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + self.click_octave_offset * 12))
            notes.append(NoteInfo(
                pitch=click_pitch,
                start=round(chord.start, 6),
                duration=0.08,  # very short transient click
                velocity=max(1, min(127, vel + 25)),
            ))

            # Companion chord tones (drawbars)
            if len(pcs) >= 3:
                for pc in pcs[1:3]:
                    drawbar_pitch = max(self.params.key_range_low, min(self.params.key_range_high, nearest_pitch(pc, mid)))
                    notes.append(NoteInfo(
                        pitch=drawbar_pitch,
                        start=round(chord.start, 6),
                        duration=round(duration, 6),
                        velocity=max(1, vel - 12),
                    ))

        return sorted(notes, key=lambda x: x.start)


class RockOrganGenerator(_KeyboardSustainedBase):
    """
    Rock Organ generator (GM 18).
    Simulates aggressive overdrive rock organ with a spinning Leslie rotary speaker rotary modulation.
    """
    name: str = "Rock Organ Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        leslie_speed_hz: float = 6.5,  # Leslie rotor speed in Hz
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.leslie_speed_hz = leslie_speed_hz
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

            vel = self._velocity(92)  # Aggressive and loud rock dynamic
            duration = chord.duration * 0.98

            # Rock organ voicing (often fat 3-voice blocks: Root, 5th, and Octave)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, nearest_pitch(pcs[0], mid)))
            fifth_pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 7))
            octave_pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 12))

            # Simulate spinning Leslie speaker effect using rapid volume LFO sweep on CC 11 and modulation wheel CC 1
            expression = {}
            step = 0.05
            expr_points = []
            t = 0.0
            while t < duration:
                # 6.5Hz LFO rotary sweep
                lfo_val = int(80 + 20 * math.sin(t * self.leslie_speed_hz * 2.0 * math.pi))
                expr_points.append((t, lfo_val))
                t += step
            if expr_points:
                expression[11] = expr_points
                # Set a high modulation wheel value (CC 1) for standard rotary speaker simulation
                expression[1] = [(0.0, 95), (duration, 95)]

            for p in (pitch, fifth_pitch, octave_pitch):
                note = NoteInfo(
                    pitch=p,
                    start=round(chord.start, 6),
                    duration=round(duration, 6),
                    velocity=vel,
                )
                if expression:
                    note.expression = expression
                notes.append(note)

        return sorted(notes, key=lambda x: x.start)


class ReedOrganGenerator(_KeyboardSustainedBase):
    """
    Reed Organ / Harmonium generator (GM 20).
    Continuous reed sound with slow pump bellows pressure sweeps.
    """
    name: str = "Reed Organ Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
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

            vel = self._velocity(72)  # Mellow nasal reed volume
            duration = chord.duration * 0.96

            # Mellow 2-voice reed stops (root & third/fifth depending on chord size)
            pitch1 = max(self.params.key_range_low, min(self.params.key_range_high, nearest_pitch(pcs[0], mid)))
            pitch2 = max(self.params.key_range_low, min(self.params.key_range_high, nearest_pitch(pcs[1 % len(pcs)], mid + 4)))

            # Harmonium bellows air pump swell LFO
            expression = {}
            expression[11] = [(0.0, 40), (duration * 0.4, 90), (duration * 0.8, 50), (duration, 35)]

            for p in (pitch1, pitch2):
                note = NoteInfo(
                    pitch=p,
                    start=round(chord.start, 6),
                    duration=round(duration, 6),
                    velocity=vel,
                )
                note.expression = expression
                notes.append(note)

        return sorted(notes, key=lambda x: x.start)
