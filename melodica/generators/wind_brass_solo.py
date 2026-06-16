# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/wind_brass_solo.py — Professional register-aware solo winds and brass.
Implements dedicated generators for Muted Trumpet (59), Synth Brass 1 & 2 (62-63),
Piccolo (72), Recorder (74), Pan Flute (75), Blown Bottle (76), Shakuhachi (77),
Whistle (78), and Ocarina (79).
"""

from __future__ import annotations

import random
import math
from abc import ABC

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale, chord_pitches_closed


class _WindBrassSoloBase(PhraseGenerator, ABC):
    """Abstract base class for solo winds and brass generators."""
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


class MutedTrumpetGenerator(_WindBrassSoloBase):
    """
    Muted Trumpet Generator (GM 59).
    Simulates a jazz/cinematic harmon muted trumpet with plunge wah-wah plunger sweeps.
    """
    name: str = "Muted Trumpet Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        plunger_wah: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.plunger_wah = plunger_wah
        self.note_density = note_density
        # Muted Trumpet register range: Bb3 (58) to C6 (84)
        self.params.key_range_low = max(58, self.params.key_range_low)
        self.params.key_range_high = min(84, self.params.key_range_high)

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

            # Pick a leading melodic voice
            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            vel = self._velocity(76)
            dur = chord.duration * 0.9

            expression = {}
            if self.plunger_wah:
                # Plunger Harmon Mute opening & closing sweeps (CC 74 wah sweep)
                expression[74] = [(0.0, 40), (dur * 0.25, 95), (dur * 0.5, 55), (dur * 0.75, 95), (dur, 60)]
                expression[11] = [(0.0, 60), (dur * 0.3, 90), (dur * 0.7, 75), (dur, 50)]

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


class SynthBrassGenerator(_WindBrassSoloBase):
    """
    Synth Brass 1 & 2 Generator (GM 62, 63).
    Classic analog polyphonic synth brass with rapid brass envelope snaps.
    """
    name: str = "Synth Brass Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        brass_type: str = "synth_brass_1",  # synth_brass_1, synth_brass_2
        harmony_count: int = 3,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.brass_type = brass_type
        self.harmony_count = max(2, min(4, harmony_count))
        self.note_density = note_density
        # Synth brass range: C2 (36) to C6 (84)
        self.params.key_range_low = max(36, self.params.key_range_low)
        self.params.key_range_high = min(84, self.params.key_range_high)

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
            voicing = chord_pitches_closed(chord, mid)
            voicing = voicing[: self.harmony_count]
            dur = chord.duration * 0.95

            # Analog brass filter snap envelope on CC 74 (Cutoff)
            expression = {}
            if self.brass_type == "synth_brass_1":
                # Sharp brass cutoff attack decay
                expression[74] = [(0.0, 110), (dur * 0.15, 60), (dur * 0.6, 75), (dur, 50)]
                vel = self._velocity(88)
            else:
                # Synth Brass 2 is warmer, detuned, with heavy chorusing send (CC 93)
                expression[74] = [(0.0, 75), (dur * 0.3, 90), (dur, 65)]
                expression[93] = [(0.0, 100), (dur, 100)]
                vel = self._velocity(78)

            for p in voicing:
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                p = snap_to_scale(p, key)

                note = NoteInfo(
                    pitch=p,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                )
                if expression:
                    note.expression = expression
                notes.append(note)

        return sorted(notes, key=lambda x: x.start)


class WoodwindSoloGenerator(_WindBrassSoloBase):
    """
    Woodwind Solo Generator covering Piccolo (72), Recorder (74), Pan Flute (75),
    Blown Bottle (76), Shakuhachi (77), Whistle (78), and Ocarina (79).
    """
    name: str = "Woodwind Solo Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "recorder",  # piccolo, recorder, pan_flute, blown_bottle, shakuhachi, whistle, ocarina
        breath_vibrato: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = instrument
        self.breath_vibrato = breath_vibrato
        self.note_density = note_density
        
        # Configure register-specific pitch ranges
        ranges = {
            "piccolo":      {"low": 72, "high": 108},
            "recorder":     {"low": 60, "high": 84},
            "pan_flute":    {"low": 55, "high": 88},
            "blown_bottle": {"low": 48, "high": 72},
            "shakuhachi":   {"low": 54, "high": 84},
            "whistle":      {"low": 72, "high": 96},
            "ocarina":      {"low": 60, "high": 84},
        }
        r = ranges.get(instrument, ranges["recorder"])
        self.params.key_range_low = max(r["low"], self.params.key_range_low)
        self.params.key_range_high = min(r["high"], self.params.key_range_high)

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

            # Pick a leading melodic voice
            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            dur = chord.duration * 0.9

            # Custom wind properties:
            if self.instrument == "piccolo":
                vel = self._velocity(84)  # piercing high attack
                dur = chord.duration * 0.85
            elif self.instrument == "pan_flute":
                vel = self._velocity(72)  # soft, highly breathy
                dur = chord.duration * 0.8
            elif self.instrument == "shakuhachi":
                vel = self._velocity(70)  # traditional bamboo reedy attack
                dur = chord.duration * 0.95
            elif self.instrument == "blown_bottle":
                vel = self._velocity(64)  # very soft and hollow
                dur = chord.duration * 0.92
            elif self.instrument == "whistle":
                vel = self._velocity(80)  # rapid grace-note whistle ornaments
                dur = chord.duration * 0.78
            else:
                vel = self._velocity(75)
                dur = chord.duration * 0.88

            # Breath-vibrato LFO sweep
            expression = {}
            if self.breath_vibrato:
                step = 0.05
                expr_points = []
                t = 0.0
                # Shakuhachi has wider vibrato, ocarina/bottle have minimal
                depth = 18 if self.instrument == "shakuhachi" else 8
                speed = 4.5 if self.instrument == "shakuhachi" else 6.0

                while t < dur:
                    val = int(80 + depth * math.sin(t * speed * 2.0 * math.pi))
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

            # Traditional woodwind ornamentations:
            # 1. Whistle/Piccolo: add a tiny grace note ornamentation at start
            if self.instrument in ("whistle", "piccolo") and random.random() < 0.4:
                grace_pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 2))
                notes.append(NoteInfo(
                    pitch=snap_to_scale(grace_pitch, key),
                    start=round(chord.start, 6),
                    duration=0.08,  # ultra short grace note
                    velocity=max(1, vel - 15),
                ))
            # 2. Pan Flute: breath puff transient click
            elif self.instrument == "pan_flute" and random.random() < 0.5:
                puff_pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 12))
                notes.append(NoteInfo(
                    pitch=snap_to_scale(puff_pitch, key),
                    start=round(chord.start, 6),
                    duration=0.05,  # breath puff click
                    velocity=max(1, vel + 15),
                ))

        return sorted(notes, key=lambda x: x.start)


class FlugelhornGenerator(_WindBrassSoloBase):
    """
    Flugelhorn Generator.
    Simulates a warm, lyrical jazz ballad flugelhorn with soft attacks
    and gentle vibrato expression sweeps.
    """
    name: str = "Flugelhorn Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        breath_vibrato: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.breath_vibrato = breath_vibrato
        self.note_density = note_density
        # Register: Gb3 (54) to C6 (84)
        self.params.key_range_low = max(54, self.params.key_range_low)
        self.params.key_range_high = min(84, self.params.key_range_high)

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

            vel = self._velocity(68)  # soft ballad attack
            dur = chord.duration * 0.92

            expression = {}
            if self.breath_vibrato:
                # Gentle 5Hz vibrato on CC 11
                step = 0.06
                expr_points = []
                t = 0.0
                while t < dur:
                    val = int(82 + 8 * math.sin(t * 5.0 * 2.0 * math.pi))
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

        return sorted(notes, key=lambda x: x.start)


class EnglishHornGenerator(_WindBrassSoloBase):
    """
    English Horn (Cor Anglais) Generator.
    Produces a warm, melancholy, lyrical alto oboe line.
    """
    name: str = "English Horn"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        vibrato: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.vibrato = vibrato
        self.note_density = note_density
        # Register: E3 (52) to Bb5 (82)
        self.params.key_range_low = max(52, self.params.key_range_low)
        self.params.key_range_high = min(82, self.params.key_range_high)

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

            vel = self._velocity(72)
            dur = chord.duration * 0.94

            expression = {}
            if self.vibrato:
                # Oboe/English horn vibrato (CC 1)
                step = 0.08
                expr_points = []
                t = 0.0
                while t < dur:
                    val = int(40 + 20 * math.sin(t * 4.5 * 2.0 * math.pi))
                    expr_points.append((t, val))
                    t += step
                if expr_points:
                    expression[1] = expr_points

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


class BassClarinetGenerator(_WindBrassSoloBase):
    """
    Bass Clarinet Generator.
    Low register warm woodwind generator.
    """
    name: str = "Bass Clarinet"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.note_density = note_density
        # Register: D2 (38) to G5 (79)
        self.params.key_range_low = max(38, self.params.key_range_low)
        self.params.key_range_high = min(79, self.params.key_range_high)

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

            vel = self._velocity(65)  # low warm woody dynamic
            dur = chord.duration * 0.90

            # Clarinet has very minimal vibrato, but nice volume breath swells
            expression = {
                11: [(0.0, 50), (dur * 0.2, 85), (dur * 0.8, 80), (dur, 30)]
            }

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=vel,
                expression=expression,
            )
            notes.append(note)

        return sorted(notes, key=lambda x: x.start)


class EuphoniumGenerator(_WindBrassSoloBase):
    """
    Euphonium (Baritone Horn) Generator.
    Produces warm, resonant low brass solo lines with slow, swelling marcato dynamics.
    """
    name: str = "Euphonium Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.note_density = note_density
        # Register: Bb1 (34) to Bb4 (70)
        self.params.key_range_low = max(34, self.params.key_range_low)
        self.params.key_range_high = min(70, self.params.key_range_high)

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

            vel = self._velocity(70)
            dur = chord.duration * 0.94

            # Low brass slow marcato swell
            expression = {
                11: [(0.0, 40), (dur * 0.25, 95), (dur * 0.8, 80), (dur, 40)]
            }

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=vel,
                expression=expression,
            )
            notes.append(note)

        return sorted(notes, key=lambda x: x.start)


class AltoFluteGenerator(_WindBrassSoloBase):
    """
    Alto Flute Generator.
    Produces low, breathy woodwind tones with gentle pitch vibrato sweeps.
    """
    name: str = "Alto Flute"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        breath_vibrato: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.breath_vibrato = breath_vibrato
        self.note_density = note_density
        # Register: G3 (55) to G6 (91)
        self.params.key_range_low = max(55, self.params.key_range_low)
        self.params.key_range_high = min(91, self.params.key_range_high)

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

            vel = self._velocity(66)  # breathy low dynamic
            dur = chord.duration * 0.90

            expression = {}
            if self.breath_vibrato:
                step = 0.06
                expr_points = []
                t = 0.0
                while t < dur:
                    val = int(80 + 8 * math.sin(t * 5.5 * 2.0 * math.pi))
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

        return sorted(notes, key=lambda x: x.start)


