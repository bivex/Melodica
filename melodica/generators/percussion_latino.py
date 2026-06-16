# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/percussion_latino.py — Latin percussion instruments.
Implements ShakerGenerator (shaker, maracas, cabasa).
"""

from __future__ import annotations

import random

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale


class ShakerGenerator(PhraseGenerator):
    """
    Shaker / Maracas / Cabasa Generator.
    Produces steady, rhythmic shake patterns with hand-movement velocity accents.
    """
    name: str = "Latino Shaker"

    # GM Percussion Map: Cabasa (69), Maracas (70), Shaker (82)
    INSTRUMENTS = {
        "shaker": 82,
        "maracas": 70,
        "cabasa": 69,
    }

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "shaker",
        rhythm_style: str = "16th",  # 16th, 8th, accented
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = instrument
        self.rhythm_style = rhythm_style
        self.note_density = note_density

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if duration_beats <= 0:
            return []

        pitch = self.INSTRUMENTS.get(self.instrument, 82)
        notes: list[NoteInfo] = []

        step_dur = 0.25 if self.rhythm_style in ("16th", "accented") else 0.5
        t = 0.0
        step_idx = 0

        while t < duration_beats:
            # Apply density gating
            if random.random() <= self.note_density:
                # Simulate natural shaker back-and-forth shake accentuation
                # downstroke is slightly louder than upstroke
                is_accent = (step_idx % 2 == 0)
                if self.rhythm_style == "accented":
                    is_accent = (step_idx % 4 == 0)
                
                base_vel = 84 if is_accent else 55
                vel = base_vel + random.randint(-8, 8)

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=round(step_dur * 0.75, 6),
                        velocity=max(1, min(127, vel)),
                        absolute=True,
                    )
                )

            t += step_dur
            step_idx += 1

        return sorted(notes, key=lambda x: x.start)
