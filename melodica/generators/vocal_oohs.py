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
generators/vocal_oohs.py — Background vocal pad generator.

Layer: Application / Domain
Style: A cappella, gospel, R&B, pop, film scoring.

Background vocal "oohs" and "aahs" — sustained vocal harmonies
sung on open syllables. Creates lush harmonic pads from vocal timbres.

Syllables:
    "ooh"  — closed vowel, darker tone
    "aah"  — open vowel, brighter tone
    "hum"  — humming, intimate
    "mm"   — humming with closed lips
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, chord_pitches_closed, snap_to_scale


@dataclass
class VocalOohsGenerator(PhraseGenerator):
    """
    Background vocal pad generator.

    syllable:
        "ooh", "aah", "hum", "mm"
    harmony_count:
        Number of vocal harmony parts (2–4).
    vibrato:
        Velocity variation to simulate vibrato (0.0–1.0).
    breath_phasing:
        Slight timing offsets between voices to simulate different singers.
    """

    name: str = "Vocal Oohs Generator"
    syllable: str = "ooh"
    harmony_count: int = 3
    vibrato: float = 0.4
    breath_phasing: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        syllable: str = "ooh",
        harmony_count: int = 3,
        vibrato: float = 0.4,
        breath_phasing: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.syllable = syllable
        self.harmony_count = max(2, min(4, harmony_count))
        self.vibrato = max(0.0, min(1.0, vibrato))
        self.breath_phasing = breath_phasing
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
            voicing = chord_pitches_closed(chord, mid)
            voicing = voicing[: self.harmony_count]

            for i, p in enumerate(voicing):
                p = snap_to_scale(max(self.params.key_range_low, min(self.params.key_range_high, p)), key)
                vel = int(45 + self.params.density * 20)
                # Vibrato
                vel += random.randint(-int(self.vibrato * 8), int(self.vibrato * 8))
                vel = max(1, min(127, vel))

                # Breath phasing: slight timing offset
                onset = chord.start
                if self.breath_phasing:
                    onset += random.uniform(0.0, 0.05)

                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(onset, 6),
                        duration=chord.duration * 0.95,
                        velocity=vel,
                    )
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes
