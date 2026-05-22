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
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


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
    breath_interval: float = 6.0
    breath_gap: float = 0.3
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        section: str = "quartet",
        articulation: str = "legato",
        dynamic_range: float = 0.5,
        breath_interval: float = 6.0,
        breath_gap: float = 0.3,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.section = section
        self.articulation = articulation
        self.dynamic_range = max(0.0, min(1.0, dynamic_range))
        self.breath_interval = max(2.0, breath_interval)
        self.breath_gap = max(0.0, min(1.0, breath_gap))
        self.rhythm = rhythm

    def _velocity(self, vel_boost: int = 0) -> int:
        base = self.base_velocity()
        vel_var = int(self.dynamic_range * 15)
        vel = base + vel_boost + random.randint(-vel_var, vel_var)
        return max(1, min(127, vel))

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

        # Natural instrument ranges (low, high MIDI pitch)
        if self.section == "trio":
            # Trio: Flute (60-96), Oboe (58-91), Clarinet (50-89)
            ranges = [(60, 96), (58, 91), (50, 89)]
        elif self.section == "quartet":
            # Quartet: Flute (60-96), Oboe (58-91), Clarinet (50-89), Bassoon (26-67)
            ranges = [(60, 96), (58, 91), (50, 89), (26, 67)]
        else:
            # Full: Flute 1 (60-96), Flute 2 (60-96), Oboe (58-91), Clarinet (50-89), Bassoon (26-67)
            ranges = [(60, 96), (60, 96), (58, 91), (50, 89), (26, 67)]

        # Track cumulative play duration per voice index to insert breaths
        voice_accumulators = {v_idx: 0.0 for v_idx in range(len(voicing_offsets))}

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            for voice_idx, offset in enumerate(voicing_offsets):
                pc = pcs[voice_idx % len(pcs)]
                anchor = mid + offset * 12
                pitch = nearest_pitch(int(pc), anchor)

                # Transpose to natural instrument register range
                low_r, high_r = ranges[voice_idx % len(ranges)]
                while pitch < low_r:
                    pitch += 12
                while pitch > high_r:
                    pitch -= 12
                pitch = snap_to_scale(pitch, key)
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

                vel = self._velocity(vel_boost)

                onset = chord.start + random.uniform(0.0, 0.02 * self.dynamic_range)
                note_dur = chord.duration * dur_factor

                # Breath mark logic:
                # If cumulative play duration for this voice exceeds breath_interval, shorten note to take a breath!
                accum = voice_accumulators[voice_idx]
                if accum >= self.breath_interval:
                    note_dur = max(0.1, note_dur - self.breath_gap)
                    voice_accumulators[voice_idx] = 0.0
                else:
                    voice_accumulators[voice_idx] += chord.duration

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=max(0.1, note_dur),
                        velocity=vel,
                        articulation=self.articulation,
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
