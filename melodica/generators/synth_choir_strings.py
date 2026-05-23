# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/synth_choir_strings.py — Electronic and synthetic pad ensembles.
Implements dedicated generators for Synth Strings 1 & 2 (50-51), Voice Oohs (53),
and Synth Choir (54).
"""

from __future__ import annotations

import random
import math

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import chord_pitches_closed, snap_to_scale


class SynthStringsGenerator(PhraseGenerator):
    """
    Synth Strings 1 & 2 generator (GM 50, 51).
    Creates rich, sustained synth string pads.
    """
    name: str = "Synth Strings Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        string_type: str = "synth_strings_1",  # synth_strings_1, synth_strings_2
        harmony_count: int = 3,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.string_type = string_type
        self.harmony_count = max(2, min(4, harmony_count))
        self.note_density = note_density

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

        for chord in chords:
            voicing = chord_pitches_closed(chord, mid)
            voicing = voicing[: self.harmony_count]
            dur = chord.duration * 0.98

            # Rich analog pad crescendo on CC 11
            expression = {}
            expression[11] = [(0.0, 50), (dur * 0.4, 95), (dur * 0.8, 85), (dur, 60)]

            if self.string_type == "synth_strings_2":
                # Synth Strings 2 has heavy chorusing (CC 93)
                expression[93] = [(0.0, 105), (dur, 105)]
                # Slight modulation wheel (CC 1) sweep
                expression[1] = [(0.0, 40), (dur * 0.5, 75), (dur, 50)]

            for p in voicing:
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                p = snap_to_scale(p, key)

                note = NoteInfo(
                    pitch=p,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=max(1, min(127, int(65 + self.params.density * 20))),
                )
                if expression:
                    note.expression = expression
                notes.append(note)

        return sorted(notes, key=lambda x: x.start)


class VoiceOohsGMGenerator(PhraseGenerator):
    """
    Sustained Voice Oohs pad (GM 53).
    Intimate vocal pad with breath phasing and warm pitch-vibrato modulations.
    """
    name: str = "Voice Oohs GM Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        harmony_count: int = 3,
        vibrato_depth: int = 8,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.harmony_count = max(2, min(4, harmony_count))
        self.vibrato_depth = vibrato_depth
        self.note_density = note_density

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

        for chord in chords:
            voicing = chord_pitches_closed(chord, mid)
            voicing = voicing[: self.harmony_count]
            dur = chord.duration * 0.96

            for i, p in enumerate(voicing):
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                p = snap_to_scale(p, key)

                # Breath phasing: slight timing offset
                onset = chord.start + random.uniform(0.0, 0.04)

                # Subtle vibrato on CC 1
                expression = {}
                expression[1] = [(0.0, 30), (dur * 0.4, 75), (dur, 45)]

                vel = max(1, min(127, int(55 + random.randint(-self.vibrato_depth, self.vibrato_depth))))

                note = NoteInfo(
                    pitch=p,
                    start=round(onset, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                )
                note.expression = expression
                notes.append(note)

        return sorted(notes, key=lambda x: x.start)


class SynthChoirGenerator(PhraseGenerator):
    """
    Synth Choir / Vocoder pad generator (GM 54).
    Airy synth pad with sweeping filters and resonant sweeps.
    """
    name: str = "Synth Choir Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        harmony_count: int = 3,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.harmony_count = max(2, min(4, harmony_count))
        self.note_density = note_density

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

        for chord in chords:
            voicing = chord_pitches_closed(chord, mid)
            voicing = voicing[: self.harmony_count]
            dur = chord.duration * 0.98

            # Airy vocoder filter sweep (CC 74 brightness LFO)
            expression = {}
            step = 0.05
            expr_points = []
            t = 0.0
            while t < dur:
                # 4Hz resonant vocoder filter sweep
                lfo_val = int(70 + 25 * math.sin(t * 4.0 * 2.0 * math.pi))
                expr_points.append((t, lfo_val))
                t += step
            if expr_points:
                expression[74] = expr_points
                expression[11] = [(0.0, 50), (dur * 0.5, 90), (dur, 60)]

            for p in voicing:
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                p = snap_to_scale(p, key)

                note = NoteInfo(
                    pitch=p,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=max(1, min(127, int(60 + self.params.density * 20))),
                )
                if expression:
                    note.expression = expression
                notes.append(note)

        return sorted(notes, key=lambda x: x.start)
