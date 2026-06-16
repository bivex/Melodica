# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/orchestral_drum.py — Orchestral concert drums.
Implements ConcertBassDrumGenerator (bass drum, tenor drum).
"""

from __future__ import annotations

import random
import math

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale


class ConcertBassDrumGenerator(PhraseGenerator):
    """
    Concert Bass Drum / Tenor Drum Generator.
    Produces single impacts, rolls, and crescendo sweeps on orchestral drums.
    """
    name: str = "Concert Bass Drum"

    # GM Concert Drum Map: Concert Bass Drum (35), Tenor Drum (47)
    DRUMS = {
        "bass_drum": 35,
        "tenor_drum": 47,
    }

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        drum_type: str = "bass_drum",
        pattern_type: str = "roll",  # single_impact, roll, crescendo
        roll_subdivision: float = 0.125,
    ) -> None:
        super().__init__(params)
        self.drum_type = drum_type
        self.pattern_type = pattern_type
        self.roll_subdivision = max(0.03125, roll_subdivision)

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if duration_beats <= 0:
            return []

        pitch = self.DRUMS.get(self.drum_type, 35)
        notes: list[NoteInfo] = []

        for chord in chords:
            dur = chord.duration * 0.95
            
            if self.pattern_type == "single_impact":
                # Single heavy hit at the beginning of the chord segment
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(chord.start, 6),
                        duration=0.5,
                        velocity=105,
                        absolute=True,
                    )
                )
            else:
                # Orchestral Roll (steady or crescendo)
                t = 0.0
                step_idx = 0
                while t < dur:
                    phase = t / dur
                    
                    # Compute velocity curve
                    if self.pattern_type == "crescendo":
                        # rise from very soft to very loud
                        base_vel = int(30 + 75 * (phase ** 1.8))
                    else:
                        # steady roll
                        base_vel = 70
                        
                    # Hand-to-hand roll velocity jitter
                    vel = base_vel + random.randint(-6, 6)
                    
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(chord.start + t, 6),
                            duration=round(self.roll_subdivision * 0.9, 6),
                            velocity=max(1, min(127, vel)),
                            absolute=True,
                        )
                    )
                    t += self.roll_subdivision
                    step_idx += 1

        return sorted(notes, key=lambda x: x.start)
