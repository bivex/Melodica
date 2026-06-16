# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/folk_ensemble.py — European Folk and regional generators.
Implements BandoneonGenerator.
"""

from __future__ import annotations

import random
import math

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


class BandoneonGenerator(PhraseGenerator):
    """
    Bandoneon (Tango Accordion) Generator.
    Produces highly expressive tango lines with bellows shakes (CC 11)
    and sharp marcato accents.
    """
    name: str = "Tango Bandoneon"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        bellows_accents: float = 0.5,   # intensity of bellows shake (0.0 to 1.0)
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.bellows_accents = max(0.0, min(1.0, bellows_accents))
        self.note_density = note_density
        # Register: C3 (48) to Bb5 (82)
        self.params.key_range_low = max(48, self.params.key_range_low)
        self.params.key_range_high = min(82, self.params.key_range_high)

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        prev_pitch = mid

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            # Voice up to 3 chord tones (standard bandoneon chordal play)
            voiced_pitches: list[int] = []
            for pc in pcs[:3]:
                p = nearest_pitch(pc, mid)
                p = snap_to_scale(p, key)
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                voiced_pitches.append(p)
            voiced_pitches = sorted(list(set(voiced_pitches)))

            # Tango rhythm: marcato accents on downbeats/boundaries
            is_accented = (chord.start % 1.0 < 0.05)
            vel = int(98 if is_accented else 75)
            vel += random.randint(-6, 6)

            dur = chord.duration * 0.90

            for p in voiced_pitches:
                expression = {}

                # Bellows shake volume sweep on CC 11
                if self.bellows_accents > 0:
                    step = 0.06
                    expr_points = []
                    t = 0.0
                    while t < dur:
                        # 6.5Hz bellows shake fluctuation
                        shake = math.sin(t * 6.5 * 2.0 * math.pi) * 16.0 * self.bellows_accents
                        val = int(82 + shake)
                        expr_points.append((t, max(0, min(127, val))))
                        t += step
                    if expr_points:
                        expression[11] = expr_points

                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(chord.start, 6),
                        duration=round(dur, 6),
                        velocity=max(1, min(127, vel)),
                        articulation="sustain",
                        expression=expression,
                    )
                )

        return sorted(notes, key=lambda x: x.start)

    def _apply_note_density(self, chords: list[ChordLabel]) -> list[ChordLabel]:
        note_density = getattr(self, "note_density", 1.0)
        if not chords or note_density == 1.0:
            return chords
        
        if note_density <= 0.0:
            return []
        
        if note_density < 1.0:
            new_chords = []
            for i, chord in enumerate(chords):
                prev_val = int((i - 1) * note_density) if i > 0 else -1
                curr_val = int(i * note_density)
                if curr_val > prev_val:
                    new_chords.append(chord)
            return new_chords
        
        subdivisions = max(1, round(note_density))
        if subdivisions <= 1:
            return chords
            
        import dataclasses
        new_chords = []
        for chord in chords:
            sub_dur = chord.duration / subdivisions
            for s in range(subdivisions):
                new_chord = dataclasses.replace(
                    chord,
                    start=chord.start + s * sub_dur,
                    duration=sub_dur
                )
                new_chords.append(new_chord)
        return new_chords
