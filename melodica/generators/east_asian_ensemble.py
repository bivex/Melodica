# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/east_asian_ensemble.py — East Asian traditional instruments.
Implements Erhu, Shamisen, and Koto generators.
"""

from __future__ import annotations

import random
import math

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.generators.plucked_solo import _PluckedSoloBase
from melodica.generators.orchestral_strings import _OrchestralStringBase
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


class ErhuGenerator(_OrchestralStringBase):
    """
    Chinese Erhu (2-string fiddle) Generator.
    Produces highly expressive monophonic lines with frequent portamento slides
    and slow, wide pitch-bend vibrato.
    """
    name: str = "Chinese Erhu"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        glide_probability: float = 0.4,
        vibrato_depth: float = 0.3,     # vibrato depth in semitones
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.glide_probability = max(0.0, min(1.0, glide_probability))
        self.vibrato_depth = max(0.0, min(1.0, vibrato_depth))
        self.note_density = note_density
        # Register: D4 (62) to A6 (93)
        self.params.key_range_low = max(62, self.params.key_range_low)
        self.params.key_range_high = min(93, self.params.key_range_high)

    def _velocity(self, base_val: int) -> int:
        if self.params.velocity_range:
            v_min, v_max = self.params.velocity_range
            return random.randint(v_min, v_max)
        return max(1, min(127, base_val + random.randint(-6, 6)))

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
            
            vel = self._velocity(74)
            dur = chord.duration * 0.94
            expression = {}
            bend_range = 2

            # 1. Slide portamento glides
            if i > 0 and random.random() < self.glide_probability:
                diff = prev_pitch - pitch
                if 0 < abs(diff) <= 3:  # glide up or down a third/step
                    start_bend = int(diff * (8192.0 / bend_range))
                    slide_t = min(0.25, dur * 0.5)
                    expression["pitch_bend"] = [(0.0, start_bend), (slide_t, 0)]

            # 2. Slow, wide pitch bend vibrato (typical of Erhu's fretless finger pressure)
            if dur > 0.4 and self.vibrato_depth > 0:
                vib_points = expression.get("pitch_bend", [(0.0, 0)])
                vib_start_t = 0.2
                vib_t = vib_start_t
                step = 0.06
                vib_amplitude = int(self.vibrato_depth * (8192.0 / bend_range))
                vib_freq = 4.0  # slow 4Hz vibrato
                
                while vib_t < dur:
                    val = int(vib_amplitude * math.sin((vib_t - vib_start_t) * vib_freq * 2.0 * math.pi))
                    vib_points.append((round(vib_t, 3), val))
                    vib_t += step
                vib_points.append((round(dur, 3), 0))
                expression["pitch_bend"] = vib_points

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=vel,
                articulation="sustain",
                expression=expression,
            )
            notes.append(note)
            prev_pitch = pitch

        return sorted(notes, key=lambda x: x.start)


class ShamisenGenerator(_PluckedSoloBase):
    """
    Japanese Shamisen (3-string plucked lute) Generator.
    Produces highly sharp, percussive bachi attacks, short decays,
    and sawari buzzing resonance.
    """
    name: str = "Japanese Shamisen"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        sawari_buzz: float = 0.4,
        strike_velocity: int = 80,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.sawari_buzz = max(0.0, min(1.0, sawari_buzz))
        self.strike_velocity = max(40, min(127, strike_velocity))
        self.note_density = note_density
        # Register: C3 (48) to D6 (86)
        self.params.key_range_low = max(48, self.params.key_range_low)
        self.params.key_range_high = min(86, self.params.key_range_high)

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

            # Percussive bachi strike accent
            is_accented = (chord.start % 1.0 < 0.05)
            vel = self._velocity(self.strike_velocity + (12 if is_accented else 0))
            
            # Short, crisp decay
            dur = chord.duration * 0.68

            expression = {}
            # Sawari Buzz (CC 12)
            if self.sawari_buzz > 0:
                buzz_points = []
                step = 0.08
                t = 0.0
                while t < dur:
                    phase = t / dur
                    val = int(80 * self.sawari_buzz * (1.0 - phase) + random.uniform(-5, 5))
                    buzz_points.append((round(t, 3), max(0, min(127, val))))
                    t += step
                if buzz_points:
                    expression[12] = buzz_points

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation="staccato",
                    expression=expression,
                )
            )

            # High-accent transient double pluck (simulates bachi striking the body skin)
            if is_accented and self.sawari_buzz > 0.3:
                double_pitch = pitch + 12
                if double_pitch <= self.params.key_range_high:
                    notes.append(
                        NoteInfo(
                            pitch=double_pitch,
                            start=round(chord.start + 0.03, 6),  # tiny delay
                            duration=0.08,
                            velocity=max(10, vel - 20),
                            articulation="staccato",
                        )
                    )

        return sorted(notes, key=lambda x: x.start)


class KotoGenerator(_PluckedSoloBase):
    """
    Japanese Koto (13-string zither) Generator.
    Snaps notes to pentatonic scales, with rapid double-plucks,
    tremolos, and string noise ornaments.
    """
    name: str = "Japanese Koto"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        tremolo_probability: float = 0.25,
        double_pluck: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.tremolo_probability = max(0.0, min(1.0, tremolo_probability))
        self.double_pluck = double_pluck
        self.note_density = note_density
        # Register: G2 (43) to D6 (86)
        self.params.key_range_low = max(43, self.params.key_range_low)
        self.params.key_range_high = min(86, self.params.key_range_high)

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
            dur = chord.duration * 0.82

            def add_pluck(start_t: float, pluck_dur: float, pluck_vel: int):
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(start_t, 6),
                        duration=round(pluck_dur, 6),
                        velocity=pluck_vel,
                    )
                )

            # Tremolo string-scraping logic
            if dur >= 0.75 and random.random() < self.tremolo_probability:
                tremolo_rate = 0.1
                t_offset = 0.0
                while t_offset < dur:
                    stroke_dur = min(tremolo_rate * 0.95, dur - t_offset)
                    stroke_vel = int(vel * random.uniform(0.65, 0.9))
                    add_pluck(chord.start + t_offset, stroke_dur, stroke_vel)
                    t_offset += tremolo_rate
            else:
                # Standard pluck or double-pluck
                if self.double_pluck and random.random() < 0.4:
                    # Double pluck: quick transient pluck
                    add_pluck(chord.start, dur * 0.3, vel)
                    add_pluck(chord.start + 0.06, dur * 0.6, max(1, vel - 12))
                else:
                    add_pluck(chord.start, dur, vel)

        return sorted(notes, key=lambda x: x.start)
