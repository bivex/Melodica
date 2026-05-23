# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/plucked_solo.py — Plucked and percussive solo instruments.
Implements highly professional, register-aware generators for Piano, Harpsichord,
Acoustic & Clean Guitars, Sitar, Koto, and Kalimba.
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


class _PluckedSoloBase(PhraseGenerator, ABC):
    """Abstract base class for all plucked and percussive solo generators."""
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


class PianoSoloGenerator(_PluckedSoloBase):
    """
    Solo Piano & Harpsichord generator.
    Covers Acoustic Grand (0), Bright Acoustic (1), Electric Grand (2), Honky-tonk (3),
    Electric Piano 1 (4), Electric Piano 2 (5), Harpsichord (6), Clavinet (7).
    """
    name: str = "Piano Solo Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "grand_piano",  # grand_piano, bright_piano, electric_grand, honky_tonk, electric_piano_1, electric_piano_2, harpsichord, clavinet
        pedal: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = instrument
        self.pedal = pedal
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

            # Pick a pitch: chord tones prioritized, with stepwise smooth flow
            pc = random.choice(pcs) if random.random() < 0.8 else random.choice([int(d) % 12 for d in key.degrees()])
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            # Generate dynamic levels
            if self.instrument == "bright_piano":
                vel = self._velocity(90)
            elif self.instrument in ("electric_piano", "electric_piano_1"):
                vel = self._velocity(80)
            elif self.instrument == "electric_piano_2":
                vel = self._velocity(72)
            elif self.instrument == "electric_grand":
                vel = self._velocity(82)
            else:
                vel = self._velocity(80)

            # Pedal sustains notes longer
            if self.instrument == "harpsichord":
                dur_mult = 0.4
            elif self.instrument == "clavinet":
                dur_mult = 0.6
            elif self.instrument == "bright_piano":
                dur_mult = 1.5 if self.pedal else 0.85
            elif self.instrument == "electric_grand":
                dur_mult = 1.3 if self.pedal else 0.8
            elif self.instrument == "honky_tonk":
                dur_mult = 1.6 if self.pedal else 0.9
            elif self.instrument == "electric_piano_2":
                dur_mult = 2.0 if self.pedal else 1.1
            elif self.instrument in ("electric_piano", "electric_piano_1"):
                dur_mult = 1.8 if self.pedal else 0.95
            else:
                dur_mult = 1.8 if self.pedal else 0.9

            duration = max(0.1, chord.duration * dur_mult)

            # Harpsichord and Clavinet have rapid release transients, E-Piano has mellow decays
            expression = {}
            if self.instrument == "harpsichord":
                duration = min(duration, 0.4)
            elif self.instrument == "clavinet":
                duration = min(duration, 0.6)
            elif self.instrument in ("electric_piano", "electric_piano_1"):
                # Add expression chorus LFO sweep
                expression[11] = [(0.0, 70), (duration * 0.5, 95), (duration, 60)]
            elif self.instrument == "electric_piano_2":
                # High chorus send (93) and rich tremolo sweep
                expression[93] = [(0.0, 105), (duration, 105)]
                expression[11] = [(0.0, 80), (duration * 0.25, 95), (duration * 0.5, 80), (duration * 0.75, 95), (duration, 80)]
            elif self.instrument == "electric_grand":
                # CP-70 type metallic chorus
                expression[93] = [(0.0, 80), (duration, 80)]
                expression[11] = [(0.0, 75), (duration * 0.5, 90), (duration, 70)]
            elif self.instrument == "honky_tonk":
                # Out-of-tune chorus send
                expression[93] = [(0.0, 95), (duration, 95)]

            note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(duration, 6),
                velocity=vel,
            )
            if expression:
                note.expression = expression
            notes.append(note)

            # Add honky-tonk double strike companion note
            if self.instrument == "honky_tonk":
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start + random.uniform(0.01, 0.025), 6),
                    duration=round(duration * 0.8, 6),
                    velocity=max(1, int(vel * 0.75)),
                ))

            # Left-hand/Bass companion chords
            if random.random() < 0.5:
                bass_pitch = max(36, nearest_pitch(pcs[0], mid - 12))
                notes.append(NoteInfo(
                    pitch=bass_pitch,
                    start=round(chord.start, 6),
                    duration=round(duration * 0.7, 6),
                    velocity=max(1, vel - 15),
                ))

        return sorted(notes, key=lambda x: x.start)


class AcousticGuitarGenerator(_PluckedSoloBase):
    """
    Solo Acoustic & Electric Guitar generator.
    Covers Nylon (24), Steel (25), Jazz (26), Clean Electric (27), Muted (28),
    Overdriven (29), Distortion (30), Guitar Harmonics (31).
    """
    name: str = "Acoustic Guitar Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "fingerpicking",  # fingerpicking, strumming, lead
        acoustic_type: str = "nylon",  # nylon, steel, clean_electric, muted, overdriven, distortion, harmonics
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.style = style
        self.acoustic_type = acoustic_type
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

            if self.style == "fingerpicking" and self.acoustic_type not in ("overdriven", "distortion", "harmonics") and len(pcs) >= 3:
                # Pluck bass note first, then arpeggiated high tones
                vel = self._velocity(75)
                # Bass
                notes.append(NoteInfo(
                    pitch=max(40, nearest_pitch(pcs[0], mid - 8)),
                    start=round(chord.start, 6),
                    duration=round(chord.duration * 0.95, 6),
                    velocity=vel,
                ))
                # High strings arpeggio
                sub_dur = chord.duration / 3.0
                for s in range(1, 3):
                    p_idx = s % len(pcs)
                    p_high = max(52, nearest_pitch(pcs[p_idx], mid + 6))
                    notes.append(NoteInfo(
                        pitch=p_high,
                        start=round(chord.start + s * sub_dur, 6),
                        duration=round(sub_dur * 0.9, 6),
                        velocity=max(1, vel - 8),
                    ))
            else:
                # Strumming/Lead
                if self.acoustic_type == "overdriven":
                    vel = self._velocity(90)
                elif self.acoustic_type == "distortion":
                    vel = self._velocity(98)
                elif self.acoustic_type == "harmonics":
                    vel = self._velocity(80)
                elif self.acoustic_type == "muted":
                    vel = self._velocity(75)
                else:
                    vel = self._velocity(85)

                pc = random.choice(pcs)
                pitch = nearest_pitch(pc, prev_pitch)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
                prev_pitch = pitch

                dur = chord.duration * 0.15 if self.acoustic_type == "muted" else chord.duration * 0.85
                if self.acoustic_type == "harmonics":
                    # Transpose up to represent natural guitar bell harmonic
                    pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 12))
                    dur = chord.duration * 0.35

                expression = {}
                if self.acoustic_type in ("overdriven", "distortion"):
                    # Aggressive pitch-vibrato sweep on CC 1 (Modulation Wheel)
                    expression[1] = [(0.0, 70), (dur * 0.5, 95), (dur, 75)]
                    if self.acoustic_type == "distortion":
                        expression[93] = [(0.0, 85), (dur, 85)]

                main_note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                )
                if expression:
                    main_note.expression = expression
                notes.append(main_note)

                # Rock/Metal heavy power chord layering (root + fifth + octave)
                if self.acoustic_type in ("overdriven", "distortion") and len(pcs) >= 1:
                    fifth_pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 7))
                    octave_pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 12))

                    for p in (fifth_pitch, octave_pitch):
                        layer_note = NoteInfo(
                            pitch=p,
                            start=round(chord.start, 6),
                            duration=round(dur, 6),
                            velocity=max(1, vel - 10),
                        )
                        if expression:
                            layer_note.expression = expression
                        notes.append(layer_note)

        return sorted(notes, key=lambda x: x.start)


class EthnicPluckedGenerator(_PluckedSoloBase):
    """
    Solo World & Ethnic Plucked generator.
    Covers Sitar (104), Koto (107), Kalimba (108).
    """
    name: str = "Ethnic Plucked Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "sitar",  # sitar, koto, kalimba
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = instrument
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

            vel = self._velocity(70)

            # Sitar has resonant bends, Kalimba has transient pops, Koto has rapid double-plucks
            expression = {}
            dur = chord.duration * 0.8

            if self.instrument == "sitar":
                # Resonant pitch bend (expression CC 12)
                expression[12] = [(0.0, 64), (dur * 0.3, 90), (dur * 0.7, 50), (dur, 64)]
            elif self.instrument == "koto":
                # Double pluck effect
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start + 0.08, 6),
                    duration=round(dur * 0.4, 6),
                    velocity=max(1, vel - 12),
                ))
                dur = dur * 0.3
            elif self.instrument == "kalimba":
                dur = min(dur, 0.25)  # Kalimba is extremely short transient

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
