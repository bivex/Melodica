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
generators/puzzle_loop.py — Puzzle game minimal loop generator.

Layer: Application / Domain
Style: Puzzle games, minimal, ambient, Tetris, Monument Valley.

Generates minimal, non-distracting loops for puzzle gameplay:
  - Arpeggiated bell-like patterns
  - Soft pads
  - Gentle rhythmic pulse
  - Designed for seamless looping

Variants:
    "bells"      — bell/glockenspiel arpeggios (Tetris-like)
    "ambient"    — soft ambient pads (Monument Valley)
    "clockwork"  — mechanical, precise patterns
    "zen"        — ultra-minimal, meditative
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


@dataclass
class PuzzleLoopGenerator(PhraseGenerator):
    """
    Puzzle game minimal loop generator.

    variant:
        "bells", "ambient", "clockwork", "zen"
    complexity:
        Pattern complexity (0.0-1.0). Lower = simpler, more repetitive.
    loop_bars:
        Loop length in bars (2-8).
    register:
        "low", "mid", "high" — preferred register.
    """

    name: str = "Puzzle Loop Generator"
    variant: str = "bells"
    complexity: float = 0.3
    loop_bars: int = 4
    register: str = "mid"
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "bells",
        complexity: float = 0.3,
        loop_bars: int = 4,
        register: str = "mid",
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.complexity = max(0.0, min(1.0, complexity))
        self.loop_bars = max(2, min(8, loop_bars))
        self.register = register

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
        loop_beats = self.loop_bars * 4
        mid = {"low": 48, "mid": 60, "high": 72}.get(self.register, 60)
        bar_start = 0.0

        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            end = min(bar_start + loop_beats, duration_beats)
            pcs = chord.pitch_classes()

            if self.variant == "bells":
                # Arpeggiated bell pattern
                t = bar_start
                idx = 0
                sub = 0.5 if self.complexity < 0.5 else 0.25
                while t < end:
                    if random.random() < 0.7 + self.complexity * 0.3:
                        pc = pcs[idx % len(pcs)]
                        pitch = nearest_pitch(pc, mid)
                        notes.append(
                            NoteInfo(
                                pitch=max(48, min(96, pitch)),
                                start=round(t, 6),
                                duration=sub * 0.8,
                                velocity=55,
                            )
                        )
                    t += sub
                    idx += 1

            elif self.variant == "ambient":
                # Soft sustained pads
                if bar_start < end:
                    for pc in pcs[:3]:
                        pitch = nearest_pitch(pc, mid)
                        notes.append(
                            NoteInfo(
                                pitch=pitch,
                                start=round(bar_start, 6),
                                duration=min(end - bar_start, 3.8),
                                velocity=35,
                            )
                        )

            elif self.variant == "clockwork":
                # Mechanical, precise
                for i in range(int(loop_beats * 2)):
                    onset = bar_start + i * 0.5
                    if onset >= end:
                        break
                    if i % 4 < 2 + int(self.complexity * 2):
                        pc = pcs[i % len(pcs)]
                        pitch = nearest_pitch(pc, mid)
                        notes.append(
                            NoteInfo(
                                pitch=max(48, min(84, pitch)),
                                start=round(onset, 6),
                                duration=0.3,
                                velocity=50,
                            )
                        )

            else:  # zen
                # Ultra-minimal
                t = bar_start
                while t < end:
                    if random.random() < 0.2 + self.complexity * 0.2:
                        pc = random.choice(pcs)
                        pitch = nearest_pitch(pc, mid)
                        notes.append(
                            NoteInfo(
                                pitch=max(48, min(84, pitch)),
                                start=round(t, 6),
                                duration=2.0,
                                velocity=30,
                            )
                        )
                        t += 2.0 + random.uniform(0, 2.0)
                    else:
                        t += 1.0

            bar_start += loop_beats

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes
