# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/cinematic_ethereal.py — Cinematic and ambient ethereal generators.
Implements GlassHarpGenerator, HandPanGenerator, and ThereminGenerator.
"""

from __future__ import annotations

import random
import math

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.generators.plucked_solo import _PluckedSoloBase
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


class GlassHarpGenerator(PhraseGenerator):
    """
    Glass Harp Generator.
    Produces ethereal, resonant glass friction sounds with slow note attacks
    and CC 1 friction flutter.
    """
    name: str = "Glass Harp"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        friction_noise: float = 0.3,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.friction_noise = max(0.0, min(1.0, friction_noise))
        self.note_density = note_density
        # Register: C4 (60) to C7 (96)
        self.params.key_range_low = max(60, self.params.key_range_low)
        self.params.key_range_high = min(96, self.params.key_range_high)

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

            # Chordal textures (up to 3 voices)
            voiced_pitches = []
            for pc in pcs[:3]:
                p = nearest_pitch(pc, mid)
                p = snap_to_scale(p, key)
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                voiced_pitches.append(p)
            voiced_pitches = sorted(list(set(voiced_pitches)))

            # Ethereal swell dynamics: slow attack
            vel = int(60 + self.params.density * 12)
            dur = chord.duration * 0.96

            for p in voiced_pitches:
                expression = {}
                
                # Slow volume swell on CC 11
                expression[11] = [
                    (0.0, 20),
                    (dur * 0.3, 90),
                    (dur * 0.8, 85),
                    (dur, 40)
                ]

                # CC 1 Friction flutter
                if self.friction_noise > 0:
                    step = 0.05
                    expr_points = []
                    t = 0.0
                    while t < dur:
                        # 8Hz rapid rub vibration
                        rub = math.sin(t * 8.0 * 2.0 * math.pi) * 12.0 * self.friction_noise
                        val = int(70 + rub + random.uniform(-4, 4))
                        expr_points.append((round(t, 3), max(0, min(127, val))))
                        t += step
                    if expr_points:
                        expression[1] = expr_points

                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(chord.start, 6),
                        duration=round(dur, 6),
                        velocity=vel,
                        articulation="sustain",
                        expression=expression,
                    )
                )

        return sorted(notes, key=lambda x: x.start)

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


class HandPanGenerator(_PluckedSoloBase):
    """
    Handpan (Hang Drum) Generator.
    Produces metallic, highly resonant percussive tongue-drum plucks.
    """
    name: str = "Handpan Drum"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        strike_damping: float = 0.5,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.strike_damping = max(0.1, min(1.0, strike_damping))
        self.note_density = note_density
        # Register: D3 (50) to A5 (81)
        self.params.key_range_low = max(50, self.params.key_range_low)
        self.params.key_range_high = min(81, self.params.key_range_high)

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

            # Pick pitch and snap
            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            vel = self._velocity(76)
            
            # Dampened, resonant metallic decay
            dur = min(chord.duration * 0.8, 0.4 + 0.6 * (1.0 - self.strike_damping))

            # Simulate metallic ring-out by adding a very quiet octave harmonic
            if self.strike_damping < 0.8 and random.random() < 0.6:
                harmonic_pitch = pitch + 12
                if harmonic_pitch <= self.params.key_range_high:
                    notes.append(
                        NoteInfo(
                            pitch=harmonic_pitch,
                            start=round(chord.start + 0.005, 6),
                            duration=round(dur * 1.4, 6),
                            velocity=max(5, int(vel * 0.35)),
                            articulation="sustain",
                        )
                    )

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation="sustain",
                )
            )

        return sorted(notes, key=lambda x: x.start)


class ThereminGenerator(PhraseGenerator):
    """
    Theremin Generator.
    Expressive sci-fi monophonic glissando generator with 100% glide transitions
    and continuous wide pitch vibrato.
    """
    name: str = "Theremin Glide"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        vibrato_speed: float = 6.0,
        vibrato_depth: float = 0.4,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.vibrato_speed = max(2.0, min(10.0, vibrato_speed))
        self.vibrato_depth = max(0.0, min(1.5, vibrato_depth))
        self.note_density = note_density
        # Register: C3 (48) to C6 (84)
        self.params.key_range_low = max(48, self.params.key_range_low)
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

        for i, chord in enumerate(chords):
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            vel = int(68 + random.uniform(-5, 5))
            dur = chord.duration * 0.98

            # Continuous glissando glide from prev_pitch to target pitch
            expression = {}
            bend_range = 12  # wide bend range for theremin slides
            
            # Start pitch bend offset
            diff = prev_pitch - pitch
            start_bend = int(diff * (8192.0 / bend_range))

            # Build pitch bend curve: glide to 0, then start vibrato
            slide_t = min(0.35, dur * 0.5)
            bend_points = [(0.0, start_bend), (slide_t, 0)]

            # Wide sine vibrato
            step = 0.05
            vib_t = slide_t
            vib_amplitude = int(self.vibrato_depth * (8192.0 / bend_range))

            while vib_t < dur:
                val = int(vib_amplitude * math.sin((vib_t - slide_t) * self.vibrato_speed * 2.0 * math.pi))
                bend_points.append((round(vib_t, 3), val))
                vib_t += step
            bend_points.append((round(dur, 3), 0))
            expression["pitch_bend"] = bend_points

            # Expression CC 11 volume flutter
            vol_points = []
            t = 0.0
            while t < dur:
                # Theremin volume has constant hand shake
                vol = int(80 + math.sin(t * 7.5 * 2.0 * math.pi) * 8.0)
                vol_points.append((round(t, 3), vol))
                t += step
            if vol_points:
                expression[11] = vol_points

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation="sustain",
                    expression=expression,
                )
            )

            prev_pitch = pitch

        return sorted(notes, key=lambda x: x.start)

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
