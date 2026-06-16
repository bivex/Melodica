# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/sound_design.py — Atmospheric sound design generators.
Implements WindMachineGenerator (wind, rainstick, thunder sheet).
"""

from __future__ import annotations

import random
import math

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale


class WindMachineGenerator(PhraseGenerator):
    """
    Wind Machine / Rainstick / Thunder Sheet Generator.
    Produces long cinematic sound effect sweeps with CC 11/1 intensity curves.
    """
    name: str = "Cinematic Sound Design"

    # Pitch mappings: Thunder (82), Rainstick (83), Wind (84)
    EFFECTS = {
        "thunder": 82,
        "rainstick": 83,
        "wind": 84,
    }

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        effect_type: str = "wind",
        intensity_curve: str = "swell",  # swell, steady, fade
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.effect_type = effect_type
        self.intensity_curve = intensity_curve
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

        pitch = self.EFFECTS.get(self.effect_type, 84)
        notes: list[NoteInfo] = []

        # Typically creates one long sustained note per segment or chord
        t = 0.0
        for chord in chords:
            dur = chord.duration * 0.98
            vel = 64
            expression = {}

            # Generate intensity sweeps on CC 11
            step = 0.1
            expr_points = []
            sweep_t = 0.0
            
            while sweep_t < dur:
                phase = sweep_t / dur
                if self.intensity_curve == "swell":
                    # rise up, then fall
                    val = int(20 + 95 * math.sin(phase * math.pi))
                elif self.intensity_curve == "fade":
                    # fade out
                    val = int(110 * (1.0 - phase))
                else:
                    # steady with flutter
                    val = int(80 + random.uniform(-6, 6))
                
                expr_points.append((round(sweep_t, 3), max(0, min(127, val))))
                sweep_t += step
                
            if expr_points:
                expression[11] = expr_points

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation="sustain",
                    expression=expression,
                    absolute=True,
                )
            )

        return sorted(notes, key=lambda x: x.start)
