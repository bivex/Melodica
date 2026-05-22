# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/choir_ahhs.py — Choir "aah" harmony generator in SATB voicing.

Layer: Application / Domain
Style: Choral, cinematic, sacred, gospel, pop ballad.

Produces sustained choral harmonies on open vowels. SATB voicing
(Soprano, Alto, Tenor, Bass) derived from chord tones.

Syllables:
    "aah"  — open vowel, bright
    "oh"   — mid vowel, rounded
    "mm"   — closed-lip hum, intimate
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


SATB_OCTAVES = [0, 0, -1, -1]  # soprano, alto, tenor, bass offsets from mid


@dataclass
class ChoirAahsGenerator(PhraseGenerator):
    """
    Choir "aah" harmonies in SATB voicing.

    voice_count:
        Number of voices (2–4). Uses top N from SATB ordering.
    dynamics:
        Overall dynamic level: "pp", "mf", "ff".
    vibrato:
        Velocity variation to simulate vocal vibrato (0.0–1.0).
    syllable:
        Vowel sound: "aah", "oh", "mm".
    """

    name: str = "Choir Aahs Generator"
    voice_count: int = 4
    dynamics: str = "mf"
    vibrato: float = 0.3
    syllable: str = "aah"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        voice_count: int = 4,
        dynamics: str = "mf",
        vibrato: float = 0.3,
        syllable: str = "aah",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.voice_count = max(2, min(4, voice_count))
        self.dynamics = dynamics
        self.vibrato = max(0.0, min(1.0, vibrato))
        self.syllable = syllable
        self.rhythm = rhythm

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        import math
        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord = chords[-1]

        # Soprano (60-84), Alto (53-72), Tenor (48-69), Bass (41-64)
        satb_ranges = [(60, 84), (53, 72), (48, 69), (41, 64)]

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            for voice_idx in range(self.voice_count):
                pc = pcs[voice_idx % len(pcs)]
                anchor = mid + SATB_OCTAVES[voice_idx] * 12
                pitch = nearest_pitch(int(pc), anchor)

                # Keep in natural SATB range
                low_r, high_r = satb_ranges[voice_idx]
                while pitch < low_r:
                    pitch += 12
                while pitch > high_r:
                    pitch -= 12
                pitch = snap_to_scale(pitch, key)
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

                vel = self._velocity()
                vel += random.randint(-int(self.vibrato * 10), int(self.vibrato * 10))
                vel = max(1, min(127, vel))

                # 1. Advanced SATB Attack Staggering based on voice index
                onset = chord.start
                if voice_idx == 0:    # Soprano (immediate)
                    onset += random.uniform(0.0, 0.010)
                elif voice_idx == 1:  # Alto
                    onset += random.uniform(0.005, 0.015)
                elif voice_idx == 2:  # Tenor
                    onset += random.uniform(0.010, 0.022)
                else:                 # Bass (slowest attack response)
                    onset += random.uniform(0.015, 0.032)

                # 2. Syllable/Vowel Morphing: long notes morph from hum/darker vowel to open bright vowel
                cutoff_base = 95 if self.syllable == "aah" else (65 if self.syllable == "oh" else 35)
                
                expression = {}
                note_dur = chord.duration * 0.92
                
                if chord.duration >= 1.2:
                    steps = 15
                    cc74_list = []
                    for s in range(steps + 1):
                        progress = s / steps
                        t_rel = progress * note_dur
                        # Morph starting from slightly darker/hummed vowel (or baseline) and opening up
                        morph_factor = 0.65 + 0.35 * progress
                        # Add LFO micro-vibrato filter oscillation (vowel formant filter fluctuations)
                        lfo_freq = 5.5  # Hz
                        vibrato_osc = math.sin(2 * math.pi * lfo_freq * t_rel) * 6 * self.vibrato
                        val = int(cutoff_base * morph_factor + vibrato_osc)
                        cc74_list.append((t_rel, max(10, min(127, val))))
                    expression[74] = cc74_list
                    
                    # 3. Voice Pitch Vibrato LFO: natural pitch vibrato sweep (Modulation/Pitch Bend)
                    pb_list = []
                    for s in range(steps + 1):
                        progress = s / steps
                        t_rel = progress * note_dur
                        # Pitch vibrato slowly sweeps/fades in over the first 0.8 seconds
                        vibrato_fade = min(1.0, t_rel / 0.8)
                        # ±120 Pitch Bend units (approx 15 cents vibrato) at 5.5 Hz
                        pb_osc = int(vibrato_fade * 120 * math.sin(2 * math.pi * 5.5 * t_rel))
                        pb_list.append((t_rel, pb_osc))
                    expression["pitch_bend"] = pb_list
                else:
                    expression[74] = cutoff_base

                note = NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=note_dur,
                    velocity=vel,
                )
                if expression:
                    note.expression = expression
                notes.append(note)

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _velocity(self) -> int:
        if self.dynamics == "pp":
            base = 40
        elif self.dynamics == "ff":
            base = 110
        else:  # mf
            base = 75
        base += int(self.params.density * 10)
        return max(1, min(127, base))
