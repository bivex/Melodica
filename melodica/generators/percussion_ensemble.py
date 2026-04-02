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
generators/percussion_ensemble.py — Percussion ensemble with polyrhythmic layering.

Layer: Application / Domain
Style: World music, afro-cuban, brazilian, contemporary percussion.

Produces interlocking percussion patterns with configurable polyrhythm.
Each instrument plays its own rhythmic cell; the polyrhythm ratio
determines how the cells interlock (e.g., 3 against 2).

Instrument MIDI map:
    conga=62, bongo=60, shaker=82, tambourine=54, cowbell=56
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


INSTRUMENT_MAP: dict[str, int] = {
    "conga": 62,
    "bongo": 60,
    "shaker": 82,
    "tambourine": 54,
    "cowbell": 56,
}

INSTRUMENT_PATTERNS: dict[str, list[float]] = {
    "conga": [0.0, 0.75, 1.5, 2.5, 3.25],
    "bongo": [0.0, 0.5, 1.25, 2.0, 2.75, 3.5],
    "shaker": [
        0.0,
        0.25,
        0.5,
        0.75,
        1.0,
        1.25,
        1.5,
        1.75,
        2.0,
        2.25,
        2.5,
        2.75,
        3.0,
        3.25,
        3.5,
        3.75,
    ],
    "tambourine": [0.0, 1.0, 2.0, 3.0],
    "cowbell": [0.0, 1.5, 2.0, 3.5],
}


@dataclass
class PercussionEnsembleGenerator(PhraseGenerator):
    """
    Ensemble of percussion instruments with polyrhythm.

    instruments:
        List of instrument names from: conga, bongo, shaker, tambourine, cowbell.
    density:
        Note density factor (0.0–1.0). Controls velocity and subdivision.
    polyrhythm_ratio:
        Polyrhythm as "NxM" (e.g., "3x2" = 3 against 2).
    """

    name: str = "Percussion Ensemble Generator"
    instruments: list[str] = field(
        default_factory=lambda: ["conga", "bongo", "shaker", "tambourine"]
    )
    density: float = 0.6
    polyrhythm_ratio: str = "3x2"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instruments: list[str] | None = None,
        density: float = 0.6,
        polyrhythm_ratio: str = "3x2",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.instruments = (
            instruments if instruments is not None else ["conga", "bongo", "shaker", "tambourine"]
        )
        self.density = max(0.0, min(1.0, density))
        self.polyrhythm_ratio = polyrhythm_ratio
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
        last_chord = chords[-1]

        ratio_a, ratio_b = self._parse_ratio()
        t = 0.0

        while t < duration_beats:
            for idx, inst_name in enumerate(self.instruments):
                midi_pitch = INSTRUMENT_MAP.get(inst_name, 62)
                base_pattern = INSTRUMENT_PATTERNS.get(inst_name, [0.0, 1.0, 2.0, 3.0])

                # Apply polyrhythm: alternate bar length based on ratio
                if idx % 2 == 0:
                    step = 4.0 / ratio_a
                else:
                    step = 4.0 / ratio_b

                poly_offset = 0.0
                for beat_offset in base_pattern:
                    onset = t + beat_offset + poly_offset
                    if onset >= duration_beats:
                        break
                    if random.random() < self.density:
                        vel = int(50 + self.params.density * 40)
                        vel += random.randint(-8, 8)
                        vel = max(1, min(127, vel))
                        dur = 0.15 if inst_name in ("shaker", "tambourine") else 0.25
                        notes.append(
                            NoteInfo(
                                pitch=midi_pitch,
                                start=round(onset, 6),
                                duration=dur,
                                velocity=vel,
                            )
                        )

                # Extra polyrhythmic layer
                poly_t = 0.0
                while poly_t < 4.0:
                    onset = t + poly_t
                    if onset < duration_beats and random.random() < self.density * 0.5:
                        vel = int(40 + self.params.density * 30)
                        notes.append(
                            NoteInfo(
                                pitch=midi_pitch,
                                start=round(onset, 6),
                                duration=0.12,
                                velocity=max(1, min(127, vel)),
                            )
                        )
                    poly_t += step

            t += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _parse_ratio(self) -> tuple[int, int]:
        try:
            parts = self.polyrhythm_ratio.lower().split("x")
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            return 3, 2
