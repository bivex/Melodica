# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/country_ensemble.py — Traditional Country & Texan instruments.
Implements PedalSteelGenerator, DobroLapSteelGenerator, and FiddleGenerator.
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


class PedalSteelGenerator(_PluckedSoloBase):
    """
    Pedal Steel Guitar Generator.
    Produces lush chord voicings with volume pedal swells and independent
    slide glissandi between chord changes.
    """
    name: str = "Pedal Steel Guitar"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        slide_speed: float = 0.2,       # duration of pitch slides in beats
        volume_swell: bool = True,      # swell notes from quiet to peak
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.slide_speed = max(0.05, min(1.0, slide_speed))
        self.volume_swell = volume_swell
        self.note_density = note_density
        # Register: G2 (43) to C6 (84)
        self.params.key_range_low = max(43, self.params.key_range_low)
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
        prev_pitches: list[int] = []

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            # Voice the chord (typically 3 or 4 notes in the middle register)
            voiced_pitches: list[int] = []
            for pc in pcs[:4]:
                p = nearest_pitch(pc, mid)
                p = snap_to_scale(p, key)
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                voiced_pitches.append(p)
            voiced_pitches = sorted(list(set(voiced_pitches)))

            dur = chord.duration * 0.96
            vel = int(70 + self.params.density * 10)

            # Match voiced pitches to previous pitches to calculate slides
            slides: dict[int, int] = {}  # maps new pitch to start bend value
            if prev_pitches and self.slide_speed > 0:
                for new_p in voiced_pitches:
                    # Find nearest previous pitch to glide from
                    closest_prev = min(prev_pitches, key=lambda x: abs(x - new_p))
                    diff = closest_prev - new_p
                    if 0 < abs(diff) <= 5:  # realistic slide range (up to 5 semitones)
                        # Assume bend range of +/- 12 semitones for wide pedal steel slides
                        bend_range = 12
                        start_bend = int(diff * (8192.0 / bend_range))
                        slides[new_p] = start_bend

            for new_p in voiced_pitches:
                expression = {}
                
                # 1. Slide Pitch Bend Curve
                if new_p in slides:
                    start_bend = slides[new_p]
                    # Glide to 0 (target pitch) over slide_speed beats
                    slide_t = min(self.slide_speed, dur * 0.6)
                    expression["pitch_bend"] = [
                        (0.0, start_bend),
                        (slide_t, 0)
                    ]
                else:
                    expression["pitch_bend"] = [(0.0, 0)]

                # 2. Volume swells (CC 11 / Expression)
                if self.volume_swell:
                    swell_t = min(0.35, dur * 0.5)
                    expression[11] = [
                        (0.0, 45),
                        (swell_t, 95),
                        (dur * 0.8, 90),
                        (dur, 60)
                    ]

                notes.append(
                    NoteInfo(
                        pitch=new_p,
                        start=round(chord.start, 6),
                        duration=round(dur, 6),
                        velocity=vel,
                        articulation="sustain",
                        expression=expression,
                    )
                )

            prev_pitches = voiced_pitches

        return sorted(notes, key=lambda x: x.start)


class DobroLapSteelGenerator(_PluckedSoloBase):
    """
    Dobro / Lap Steel Resonator Guitar.
    Simulates slide guitar plucks, scoop-up slides at the start of notes,
    and tail pitch vibrato.
    """
    name: str = "Dobro Lap Steel"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        scoop_depth: float = 1.5,       # scoop-up pitch bend in semitones
        vibrato_depth: float = 0.25,    # tail vibrato depth in semitones
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.scoop_depth = max(0.0, min(3.0, scoop_depth))
        self.vibrato_depth = max(0.0, min(1.0, vibrato_depth))
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

            vel = self._velocity(74)
            dur = chord.duration * 0.82

            expression = {}
            bend_range = 2  # standard bend range

            # 1. Pitch scoop at start of note
            # Start scoop_depth semitones below target, slide up in 0.1 beats
            scoop_bend = -int(self.scoop_depth * (8192.0 / bend_range))
            
            # 2. Pitch Vibrato on tail of sustained notes (dur > 0.5)
            bend_points = [(0.0, scoop_bend), (0.1, 0)]
            
            if dur > 0.5 and self.vibrato_depth > 0:
                vib_start_t = 0.25
                vib_t = vib_start_t
                step = 0.05
                vib_amplitude = int(self.vibrato_depth * (8192.0 / bend_range))
                vib_frequency = 6.0  # 6Hz vibrato
                
                while vib_t < dur:
                    val = int(vib_amplitude * math.sin((vib_t - vib_start_t) * vib_frequency * 2.0 * math.pi))
                    bend_points.append((round(vib_t, 3), val))
                    vib_t += step
                bend_points.append((round(dur, 3), 0))
                
            expression["pitch_bend"] = bend_points

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=vel,
                articulation="sustain",
                expression=expression,
            )
            notes.append(note)

        return sorted(notes, key=lambda x: x.start)


class FiddleGenerator(_OrchestralStringBase):
    """
    Country Fiddle Generator.
    Features folk bowing, frequent double-stops, open-string drone notes,
    and slides into melody notes.
    """
    name: str = "Country Fiddle"

    # Fiddle standard open strings: G3 (55), D4 (62), A4 (69), E5 (76)
    OPEN_STRINGS = [55, 62, 69, 76]

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        double_stop_probability: float = 0.4,
        open_string_drone: bool = True,
        slide_probability: float = 0.3,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.double_stop_probability = max(0.0, min(1.0, double_stop_probability))
        self.open_string_drone = open_string_drone
        self.slide_probability = max(0.0, min(1.0, slide_probability))
        self.note_density = note_density
        # Register: G3 (55) to E6 (88)
        self.params.key_range_low = max(55, self.params.key_range_low)
        self.params.key_range_high = min(88, self.params.key_range_high)

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

            # Rhythmic folk bowing: accent downbeats strongly
            is_accented = (chord.start % 1.0 < 0.05)
            vel = int(88 if is_accented else 70)
            vel += random.randint(-6, 6)
            
            dur = chord.duration * 0.88
            expression = {}

            # 1. Slide slide-up ornaments (scoops)
            if random.random() < self.slide_probability:
                # Slide up from a semitone below (approx -4096 bend units for range = 2)
                expression["pitch_bend"] = [(0.0, -4096), (0.08, 0)]

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=max(1, min(127, vel)),
                articulation="sustain" if is_accented else "staccato",
            )
            if expression:
                note.expression = expression
            notes.append(note)

            # 2. Double-Stops or Open String Drones
            if random.random() < self.double_stop_probability:
                double_pitch = 0
                
                # Check for open string drone first
                if self.open_string_drone and random.random() < 0.5:
                    # Pick an open string close to the melody note
                    closest_open = min(self.OPEN_STRINGS, key=lambda x: abs(x - pitch))
                    if closest_open != pitch:
                        double_pitch = closest_open

                # Otherwise, use a perfect fifth/fourth/octave harmony tone
                if double_pitch == 0:
                    for interval in [7, 5, 12, -5, -7, -12]:
                        cand = snap_to_scale(pitch + interval, key)
                        if self.params.key_range_low <= cand <= self.params.key_range_high and cand != pitch:
                            double_pitch = cand
                            break

                if double_pitch > 0:
                    # Slightly softer for the harmony double-stop string
                    double_vel = max(30, int(vel * 0.85))
                    notes.append(
                        NoteInfo(
                            pitch=double_pitch,
                            start=round(chord.start + random.uniform(0.002, 0.012), 6),  # tiny bowing offset
                            duration=round(dur, 6),
                            velocity=double_vel,
                            articulation="sustain",
                        )
                    )

        return sorted(notes, key=lambda x: x.start)
