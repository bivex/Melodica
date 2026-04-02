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
generators/woodwinds_ensemble.py — Woodwind section harmonization.

Layer: Application / Domain
Style: Classical, film scoring, orchestral, chamber music.

Produces harmonized woodwind lines using flute, clarinet, oboe, and
bassoon voicings. Each section size controls how many instruments
participate in the texture.

Sections:
    "trio"    — flute, clarinet, oboe
    "quartet" — flute, clarinet, oboe, bassoon
    "full"    — doubled flute, clarinet, oboe, bassoon, english horn
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


SECTION_VOICINGS: dict[str, list[int]] = {
    "trio": [0, -1, 1],  # clarinet, oboe above, flute below anchor
    "quartet": [0, -1, 1, -2],  # + bassoon low
    "full": [0, 0, -1, 1, -2],  # doubled top + english horn
}

ARTICULATION_DURATIONS: dict[str, float] = {
    "legato": 0.95,
    "staccato": 0.3,
    "marcato": 0.7,
}

ARTICULATION_VELOCITY_BOOST: dict[str, int] = {
    "legato": 0,
    "staccato": 10,
    "marcato": 20,
}


@dataclass
class WoodwindsEnsembleGenerator(PhraseGenerator):
    """
    Woodwind section: flute, clarinet, oboe harmonized.

    section:
        "trio", "quartet", "full"
    articulation:
        "legato", "staccato", "marcato"
    dynamic_range:
        Controls velocity spread (0.0–1.0). Higher = more variation.
    """

    name: str = "Woodwinds Ensemble Generator"
    section: str = "quartet"
    articulation: str = "legato"
    dynamic_range: float = 0.5
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        section: str = "quartet",
        articulation: str = "legato",
        dynamic_range: float = 0.5,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.section = section
        self.articulation = articulation
        self.dynamic_range = max(0.0, min(1.0, dynamic_range))
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
        voicing_offsets = SECTION_VOICINGS.get(self.section, SECTION_VOICINGS["quartet"])
        dur_factor = ARTICULATION_DURATIONS.get(self.articulation, 0.95)
        vel_boost = ARTICULATION_VELOCITY_BOOST.get(self.articulation, 0)

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            for voice_idx, offset in enumerate(voicing_offsets):
                pc = pcs[voice_idx % len(pcs)]
                anchor = mid + offset * 12
                pitch = nearest_pitch(int(pc), anchor)
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

                base_vel = int(55 + self.params.density * 25) + vel_boost
                vel_var = int(self.dynamic_range * 15)
                vel = base_vel + random.randint(-vel_var, vel_var)
                vel = max(1, min(127, vel))

                onset = chord.start + random.uniform(0.0, 0.02 * self.dynamic_range)
                note_dur = chord.duration * dur_factor

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=max(0.1, note_dur),
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
