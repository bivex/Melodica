# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/sfx_percussion.py — General MIDI Percussion & Sound SFX (programs 112-127).
Implements specialized physical envelopes, syncopation, rolls, sweeps, and real-world 
sound effect behaviors.
"""

from __future__ import annotations

import random
import math
from abc import ABC

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


class _SFXPercussionBase(PhraseGenerator, ABC):
    """Abstract base class for all percussion and SFX generators."""
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


class SFXPercussionGenerator(_SFXPercussionBase):
    """
    General MIDI Percussion & SFX Generator.
    Covers Tinkle Bell (112), Agogo (113), Steel Drums (114), Woodblock (115),
    Taiko Drum (116), Melodic Tom (117), Synth Drum (118), Reverse Cymbal (119),
    and GM SFX 120-127 (Guitar Fret, Breath, Seashore, Bird Tweet, Telephone, Helicopter, Applause, Gunshot).
    """
    name: str = "SFX Percussion Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "tinkle_bell",  # tinkle_bell, agogo, steel_drums, woodblock, taiko_drum, melodic_tom, synth_drum, reverse_cymbal, fret_noise, breath_noise, seashore, bird_tweet, telephone, helicopter, applause, gunshot
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = instrument
        self.note_density = note_density
        # Clamp ranges based on physical characteristics
        if self.instrument == "tinkle_bell":
            self.params.key_range_low = max(72, self.params.key_range_low)  # High register
            self.params.key_range_high = min(108, self.params.key_range_high)
        elif self.instrument == "taiko_drum":
            self.params.key_range_low = max(36, self.params.key_range_low)  # Low register
            self.params.key_range_high = min(60, self.params.key_range_high)
        elif self.instrument in ("seashore", "applause", "helicopter"):
            self.params.key_range_low = max(36, self.params.key_range_low)
            self.params.key_range_high = min(72, self.params.key_range_high)

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

            # Pick a melody pitch or root pitch class
            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            dur = chord.duration * 0.95
            vel = self._velocity(80)

            # --- Chromatic Percussion (112 - 119) ---

            # 1. Tinkle Bell (112) - short, delicate, high-pitched
            if self.instrument == "tinkle_bell":
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 24))
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(max(0.1, chord.duration * 0.15), 6),
                    velocity=self._velocity(95),
                ))

            # 2. Agogo (113) - high/low pair playing a syncopated double hit
            elif self.instrument == "agogo":
                # High hit at start, Low hit 0.5 beats later
                p_high = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 7))
                notes.append(NoteInfo(
                    pitch=p_high,
                    start=round(chord.start, 6),
                    duration=0.15,
                    velocity=self._velocity(90),
                ))
                if chord.duration > 0.5:
                    p_low = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
                    notes.append(NoteInfo(
                        pitch=p_low,
                        start=round(chord.start + 0.5, 6),
                        duration=0.15,
                        velocity=self._velocity(80),
                    ))

            # 3. Steel Drums (114) - rapid alternating rolls on sustain
            elif self.instrument == "steel_drums":
                # Subdivide into 32nd notes if chord is long enough, otherwise triplets
                sub_count = 6 if chord.duration >= 1.0 else 3
                sub_dur = chord.duration / sub_count
                for i in range(sub_count):
                    notes.append(NoteInfo(
                        pitch=pitch if i % 2 == 0 else pitch + 4,  # alternate pitches slightly
                        start=round(chord.start + i * sub_dur, 6),
                        duration=round(sub_dur * 0.9, 6),
                        velocity=self._velocity(82 if i == 0 else 72),
                    ))

            # 4. Woodblock (115) - extremely dry staccato clicks
            elif self.instrument == "woodblock":
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=0.08,
                    velocity=self._velocity(98),
                ))

            # 5. Taiko Drum (116) - deep, explosive attack, long resonant tail
            elif self.instrument == "taiko_drum":
                pitch_low = max(self.params.key_range_low, min(self.params.key_range_high, pitch - 12))
                notes.append(NoteInfo(
                    pitch=pitch_low,
                    start=round(chord.start, 6),
                    duration=round(chord.duration * 1.5, 6),  # ring out long
                    velocity=self._velocity(115),
                ))

            # 6. Melodic Tom (117) - tom pitches jumping scale tones
            elif self.instrument == "melodic_tom":
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=0.25,
                    velocity=self._velocity(92),
                ))

            # 7. Synth Drum (118) - pitch drop sweep downwards
            elif self.instrument == "synth_drum":
                expression = {
                    "pitch_bend": [(0.0, 3000), (0.08, 0), (0.2, -4000)],
                }
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=0.3,
                    velocity=self._velocity(100),
                )
                note.expression = expression
                notes.append(note)

            # 8. Reverse Cymbal (119) - volume crescendo swelling up then cutting short
            elif self.instrument == "reverse_cymbal":
                expression = {
                    11: [(0.0, 10), (dur * 0.5, 45), (dur * 0.9, 120), (dur, 0)],
                }
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=self._velocity(95),
                )
                note.expression = expression
                notes.append(note)

            # --- Sound Effects (SFX 120 - 127) ---

            # 9. Guitar Fret Noise (120) - high-pass squeak
            elif self.instrument == "fret_noise":
                notes.append(NoteInfo(
                    pitch=max(self.params.key_range_low, min(self.params.key_range_high, pitch + 24)),
                    start=round(chord.start, 6),
                    duration=0.1,
                    velocity=self._velocity(60),
                ))

            # 10. Breath Noise (121) - gradual breath sound
            elif self.instrument == "breath_noise":
                expression = {
                    11: [(0.0, 20), (dur * 0.5, 80), (dur, 10)],
                }
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=self._velocity(50),
                )
                note.expression = expression
                notes.append(note)

            # 11. Seashore (122) - slow rolling ocean wave swells
            elif self.instrument == "seashore":
                expression = {
                    11: [(0.0, 15), (dur * 0.5, 95), (dur, 10)],
                    74: [(0.0, 40), (dur * 0.5, 80), (dur, 35)],
                }
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(chord.duration, 6),
                    velocity=self._velocity(45),
                )
                note.expression = expression
                notes.append(note)

            # 12. Bird Tweet (123) - rapid rhythmic chirping
            elif self.instrument == "bird_tweet":
                sub_count = 3
                sub_dur = chord.duration / sub_count
                for i in range(sub_count):
                    # Each chirp is brief and high register
                    notes.append(NoteInfo(
                        pitch=max(self.params.key_range_low, min(self.params.key_range_high, pitch + 19 + i * 2)),
                        start=round(chord.start + i * sub_dur, 6),
                        duration=0.08,
                        velocity=self._velocity(75),
                    ))

            # 13. Telephone Ring (124) - rapid double-ring rhythmic pulses
            elif self.instrument == "telephone":
                # Pulse double ring at chord starts
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=0.12,
                    velocity=self._velocity(85),
                ))
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start + 0.18, 6),
                    duration=0.12,
                    velocity=self._velocity(85),
                ))

            # 14. Helicopter (125) - continuous blade motor panning/volume LFO modulation
            elif self.instrument == "helicopter":
                step = 0.05
                expr_vol = []
                expr_pan = []
                t = 0.0
                while t < chord.duration:
                    vol_val = int(70 + 35 * math.sin(t * 12.0 * 2.0 * math.pi))  # 12Hz rotor motor
                    pan_val = int(64 + 30 * math.cos(t * 2.0 * 2.0 * math.pi))   # slow pan
                    expr_vol.append((t, vol_val))
                    expr_pan.append((t, pan_val))
                    t += step
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(chord.duration, 6),
                    velocity=self._velocity(80),
                )
                note.expression = {11: expr_vol, 10: expr_pan}
                notes.append(note)

            # 15. Applause (126) - large crowd roar dynamic swell
            elif self.instrument == "applause":
                expression = {
                    11: [(0.0, 40), (dur * 0.4, 95), (dur * 0.8, 80), (dur, 30)],
                }
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(chord.duration, 6),
                    velocity=self._velocity(70),
                )
                note.expression = expression
                notes.append(note)

            # 16. Gunshot (127) - explosive attack, extremely brief duration, maximum velocity
            elif self.instrument == "gunshot":
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=0.12,
                    velocity=self._velocity(125),
                ))

        return sorted(notes, key=lambda x: x.start)
