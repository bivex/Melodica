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
from melodica.utils import nearest_pitch, chord_at


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

        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord = chords[-1]

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            for voice_idx in range(self.voice_count):
                pc = pcs[voice_idx % len(pcs)]
                anchor = mid + SATB_OCTAVES[voice_idx] * 12
                pitch = nearest_pitch(int(pc), anchor)
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

                vel = self._velocity()
                vel += random.randint(-int(self.vibrato * 10), int(self.vibrato * 10))
                vel = max(1, min(127, vel))

                onset = chord.start
                onset += random.uniform(0.0, 0.03)  # ensemble breath offset

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=chord.duration * 0.92,
                        velocity=vel,
                    )
                )

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _velocity(self) -> int:
        base = {"pp": 35, "mf": 65, "ff": 100}
        return int(base.get(self.dynamics, 65) + self.params.density * 15)
