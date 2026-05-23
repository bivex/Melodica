# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/ethnic_world.py — Ethnic World Instruments.
Implements highly expressive, register-aware generators for Banjo, Shamisen,
Bagpipe, Fiddle, and Shanai.
"""

from __future__ import annotations

import random
import math
from abc import ABC

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


class _EthnicWorldBase(PhraseGenerator, ABC):
    """Abstract base class for all ethnic/world solo generators."""
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


class EthnicWorldGenerator(_EthnicWorldBase):
    """
    Ethnic World Instruments Generator.
    Covers Banjo (105), Shamisen (106), Bagpipe (109), Fiddle (110), Shanai (111).
    """
    name: str = "Ethnic World Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "banjo",  # banjo, shamisen, bagpipe, fiddle, shanai
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = instrument
        self.note_density = note_density
        # Clamp ranges based on instrument acoustics
        if self.instrument == "banjo":
            self.params.key_range_low = max(48, self.params.key_range_low)  # C3
            self.params.key_range_high = min(84, self.params.key_range_high)  # C6
        elif self.instrument == "shamisen":
            self.params.key_range_low = max(45, self.params.key_range_low)  # A2
            self.params.key_range_high = min(77, self.params.key_range_high)  # F5
        elif self.instrument == "bagpipe":
            self.params.key_range_low = max(54, self.params.key_range_low)  # F#3
            self.params.key_range_high = min(78, self.params.key_range_high)  # F#5
        elif self.instrument == "fiddle":
            self.params.key_range_low = max(55, self.params.key_range_low)  # G3
            self.params.key_range_high = min(88, self.params.key_range_high)  # E6
        elif self.instrument == "shanai":
            self.params.key_range_low = max(58, self.params.key_range_low)  # Bb3
            self.params.key_range_high = min(82, self.params.key_range_high)  # Bb5

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

            # Pick a main melody pitch
            pc = random.choice(pcs) if random.random() < 0.7 else random.choice([int(d) % 12 for d in key.degrees()])
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            dur = chord.duration * 0.95
            vel = self._velocity(80)

            # 1. Banjo - Rapid rolls (triplets or 16th notes)
            if self.instrument == "banjo":
                # Banjo is extremely snappy. If density is high or complexity is high, we generate a picking roll!
                sub_count = 3 if self.params.complexity < 0.5 else 4
                sub_dur = chord.duration / sub_count
                for i in range(sub_count):
                    # Alternate pitches in a banjo roll fashion (e.g. thumb, index, middle finger alternation)
                    if i == 0:
                        roll_pitch = pitch
                    elif i == 1:
                        # High string G (up an octave or nearest chord tone)
                        roll_pitch = pitch + 12
                    elif i == 2:
                        roll_pitch = pitch + 5
                    else:
                        roll_pitch = pitch + 7
                    
                    roll_pitch = snap_to_scale(roll_pitch, key)
                    roll_pitch = max(self.params.key_range_low, min(self.params.key_range_high, roll_pitch))
                    
                    notes.append(NoteInfo(
                        pitch=roll_pitch,
                        start=round(chord.start + i * sub_dur, 6),
                        duration=round(sub_dur * 0.85, 6),
                        velocity=self._velocity(85 if i == 0 else 72),
                    ))
                continue

            # 2. Shamisen - Sharp wood-pick snaps with slide-up bend
            elif self.instrument == "shamisen":
                # A sharp snap at onset, then quick decay
                dur = chord.duration * 0.5
                expression = {
                    11: [(0.0, 110), (dur * 0.3, 70), (dur, 10)],
                    "pitch_bend": [(0.0, -1200), (0.05, -600), (0.1, 0)],
                }
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=self._velocity(95),
                )
                note.expression = expression
                notes.append(note)

            # 3. Bagpipe - Low sustained drone + High melodic note
            elif self.instrument == "bagpipe":
                # Drone starts at the beginning of the chord and sustains fully
                drone_pitch = key.root + 36  # low drone octave
                drone_pitch = max(self.params.key_range_low, min(self.params.key_range_high, drone_pitch))
                
                drone_note = NoteInfo(
                    pitch=drone_pitch,
                    start=round(chord.start, 6),
                    duration=round(chord.duration, 6),
                    velocity=self._velocity(70),
                )
                # Bellows swell on drone
                drone_note.expression = {
                    11: [(0.0, 50), (chord.duration * 0.5, 80), (chord.duration, 70)],
                }
                notes.append(drone_note)

                # Melodic pipe note
                pipe_note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=self._velocity(85),
                )
                pipe_note.expression = {
                    11: [(0.0, 75), (dur * 0.5, 95), (dur, 80)],
                }
                notes.append(pipe_note)

            # 4. Fiddle - Expressive slides and warm dynamic swells
            elif self.instrument == "fiddle":
                # Add expressive sliding pitch bend at onset and vibrato
                expression = {
                    11: [(0.0, 60), (dur * 0.2, 95), (dur * 0.8, 85), (dur, 40)],
                    1: [(0.0, 30), (dur * 0.5, 85), (dur, 60)],
                    "pitch_bend": [(0.0, -800), (0.12, 0), (dur * 0.8, 0)],
                }
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=self._velocity(78),
                )
                note.expression = expression
                notes.append(note)

            # 5. Shanai - Nasal wind with microtonal pitch bends
            elif self.instrument == "shanai":
                # Expression has rapid brightness swells (CC 74) and microtonal pitch curves
                expression = {
                    11: [(0.0, 55), (dur * 0.3, 90), (dur * 0.7, 75), (dur, 40)],
                    74: [(0.0, 50), (dur * 0.25, 95), (dur * 0.5, 70), (dur * 0.75, 100), (dur, 60)],
                    "pitch_bend": [(0.0, 0), (dur * 0.2, 400), (dur * 0.4, -400), (dur * 0.6, 0)],
                }
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=self._velocity(82),
                )
                note.expression = expression
                notes.append(note)

        return sorted(notes, key=lambda x: x.start)
