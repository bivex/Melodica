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
generators/polyrhythm.py — Polyrhythmic note generator.

Layer: Application / Domain
Style: Minimalism, African music, contemporary classical, electronic.

Generates notes in a polyrhythmic relationship: two or more streams
of notes with different subdivisions playing simultaneously.

Common polyrhythms:
    "3v2" — triplet against eighth notes
    "5v4" — quintuplets against sixteenths
    "3v4" — triplet against sixteenths
    "7v8" — septuplets against eighths
    "2v3" — even against triplet

Each stream can target a different pitch, creating interlocking patterns.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class PolyrhythmGenerator(PhraseGenerator):
    """
    Polyrhythmic note generator.

    ratio:
        Polyrhythm ratio as "AxB" string (e.g., "3x2", "5x4").
    stream_a_pitch:
        Pitch selection for stream A: "chord_root", "chord_tone", "scale_tone".
    stream_b_pitch:
        Pitch selection for stream B.
    pitch_offset:
        Semitone offset between stream A and B pitches.
    duration:
        Duration of the polyrhythm cycle in beats.
    """

    name: str = "Polyrhythm Generator"
    ratio: str = "3x2"
    stream_a_pitch: str = "chord_root"
    stream_b_pitch: str = "fifth"
    pitch_offset: int = 7
    duration: float = 4.0
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        ratio: str = "3x2",
        stream_a_pitch: str = "chord_root",
        stream_b_pitch: str = "fifth",
        pitch_offset: int = 7,
        duration: float = 4.0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.ratio = ratio
        self.stream_a_pitch = stream_a_pitch
        self.stream_b_pitch = stream_b_pitch
        self.pitch_offset = pitch_offset
        self.duration = max(1.0, min(16.0, duration))
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

        a, b = self._parse_ratio()
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        last_chord: ChordLabel | None = None
        cycle_dur = self.duration

        t = 0.0
        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is None:
                t += cycle_dur
                continue
            last_chord = chord

            # Stream A: 'a' notes per cycle
            pitch_a = self._pick_pitch(chord, self.stream_a_pitch, anchor, key, low, high)
            vel_a = int(60 + self.params.density * 30)

            for i in range(a):
                onset = t + (i / a) * cycle_dur
                if onset >= duration_beats:
                    break
                n_dur = (cycle_dur / a) * 0.85
                notes.append(
                    NoteInfo(
                        pitch=max(low, min(high, pitch_a)),
                        start=round(onset, 6),
                        duration=n_dur,
                        velocity=max(1, min(127, vel_a)),
                    )
                )

            # Stream B: 'b' notes per cycle
            pitch_b = self._pick_pitch(chord, self.stream_b_pitch, anchor, key, low, high)
            pitch_b = max(low, min(high, pitch_b + self.pitch_offset))
            vel_b = int(55 + self.params.density * 25)

            for i in range(b):
                onset = t + (i / b) * cycle_dur
                if onset >= duration_beats:
                    break
                n_dur = (cycle_dur / b) * 0.85
                notes.append(
                    NoteInfo(
                        pitch=pitch_b,
                        start=round(onset, 6),
                        duration=n_dur,
                        velocity=max(1, min(127, vel_b)),
                    )
                )

            t += cycle_dur

        # Sort by onset time
        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _parse_ratio(self) -> tuple[int, int]:
        parts = self.ratio.split("x")
        if len(parts) != 2:
            return (3, 2)
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            return (3, 2)

    def _pick_pitch(
        self,
        chord: ChordLabel,
        strategy: str,
        anchor: int,
        key: Scale,
        low: int,
        high: int,
    ) -> int:
        if strategy == "chord_root":
            return nearest_pitch(chord.root, anchor)
        elif strategy == "chord_tone":
            pcs = chord.pitch_classes()
            return nearest_pitch(int(random.choice(pcs)), anchor)
        elif strategy == "scale_tone":
            degs = key.degrees()
            return (
                nearest_pitch(int(random.choice(degs)), anchor)
                if degs
                else nearest_pitch(chord.root, anchor)
            )
        elif strategy == "fifth":
            return nearest_pitch((chord.root + 7) % 12, anchor)
        return nearest_pitch(chord.root, anchor)
