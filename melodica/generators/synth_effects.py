# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/synth_effects.py — Specialized GM Synth Sound Effects (FX 96-103).
Implements dedicated generators for rain, soundtrack, crystal, atmosphere,
brightness, goblins, echoes, and sci-fi.
"""

from __future__ import annotations

import random
import math
from abc import ABC

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale, chord_pitches_closed


class SynthEffectsGenerator(PhraseGenerator):
    """
    Dedicated generator for Synth Sound Effects (FX 96-103).
    """
    name: str = "Synth Effects Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        fx_type: str = "crystal",  # rain, soundtrack, crystal, atmosphere, brightness, goblins, echoes, sci_fi
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.fx_type = fx_type
        self.note_density = note_density
        # Synth FX range: C2 (36) to C7 (96)
        self.params.key_range_low = max(36, self.params.key_range_low)
        self.params.key_range_high = min(96, self.params.key_range_high)

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
        prev_pitch = mid

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            # Pick base pitch
            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            dur = chord.duration * 0.95
            vel = int(72 + self.params.density * 15)

            expression = {}

            # 1. FX 1 (rain) - continuous rain clicks (panned panning CC 10 LFO)
            if self.fx_type == "rain":
                step = 0.05
                expr_points = []
                t = 0.0
                while t < dur:
                    pan_val = int(64 + 40 * math.sin(t * 3.0 * 2.0 * math.pi))  # 3Hz pan LFO
                    expr_points.append((t, pan_val))
                    t += step
                if expr_points:
                    expression[10] = expr_points
                vel = int(vel * 0.8)

            # 2. FX 2 (soundtrack) - slow crescendo dynamic pad swell
            elif self.fx_type == "soundtrack":
                expression[11] = [(0.0, 30), (dur * 0.5, 95), (dur, 50)]
                expression[74] = [(0.0, 45), (dur * 0.7, 90), (dur, 60)]

            # 3. FX 3 (crystal) - highly chorused (CC 93) sweeping glassy bells
            elif self.fx_type == "crystal":
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 12))
                expression[93] = [(0.0, 110), (dur, 110)]
                expression[1] = [(0.0, 40), (dur * 0.5, 90), (dur, 55)]

            # 4. FX 4 (atmosphere) - soft airy pad
            elif self.fx_type == "atmosphere":
                expression[11] = [(0.0, 20), (dur * 0.45, 90), (dur, 30)]

            # 5. FX 5 (brightness) - extremely high piercing bells
            elif self.fx_type == "brightness":
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 24))
                vel = int(vel * 1.2)

            # 6. FX 6 (goblins) - spooky high staccatos with filter snapping
            elif self.fx_type == "goblins":
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch + 12))
                dur = chord.duration * 0.25
                expression[74] = [(0.0, 110), (dur, 45)]

            # 7. FX 8 (sci_fi) - pitch LFO sweep on CC 1
            elif self.fx_type == "sci_fi":
                expression[1] = [(0.0, 95), (dur, 95)]
                expression[74] = [(0.0, 35), (dur * 0.5, 115), (dur, 55)]

            main_note = NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=round(dur, 6),
                velocity=max(1, min(127, vel)),
            )
            if expression:
                main_note.expression = expression.copy()
            notes.append(main_note)

            # 8. FX 7 (echoes) - auto layer delayed echo notes (secondary and tertiary)
            if self.fx_type == "echoes":
                # First echo: 0.25 beats later, 70% velocity
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start + 0.25, 6),
                    duration=round(dur * 0.7, 6),
                    velocity=max(1, int(vel * 0.7)),
                ))
                # Second echo: 0.5 beats later, 45% velocity
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start + 0.5, 6),
                    duration=round(dur * 0.5, 6),
                    velocity=max(1, int(vel * 0.45)),
                ))

        return sorted(notes, key=lambda x: x.start)
