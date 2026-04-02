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
generators/bongo_flava.py — Bongo Flava pattern generator.

Layer: Application / Domain
Style: Bongo Flava, Tanzanian hip-hop, East African pop.

Generates Tanzanian Bongo Flava elements:
  - Bouncy kick patterns
  - Melodic vocal lines
  - African percussion with modern production
  - Sing-song rap melodies

Variants:
    "classic"    — classic Bongo Flava
    "modern"     — modern production (Diamond Platnumz)
    "singeli"    — Singeli (fast Tanzanian electronic)
    "taarab_pop" — Taarab-influenced pop
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
CLAP = 39
SHAKER = 70


@dataclass
class BongoFlavaGenerator(PhraseGenerator):
    """Bongo Flava generator. variant: classic, modern, singeli, taarab_pop."""

    name: str = "Bongo Flava Generator"
    variant: str = "modern"
    melody_density: float = 0.6
    include_percussion: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "modern",
        melody_density: float = 0.6,
        include_percussion: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.melody_density = max(0.0, min(1.0, melody_density))
        self.include_percussion = include_percussion

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
        low = max(24, self.params.key_range_low)
        last_chord = chords[-1]
        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue
            self._render_drums(notes, bar_start, duration_beats)
            self._render_bass(notes, bar_start, duration_beats, chord, low)
            self._render_melody(notes, bar_start, duration_beats, chord, key)
            if self.include_percussion:
                self._render_perc(notes, bar_start, duration_beats)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_drums(self, notes, bar_start, total):
        if self.variant == "singeli":
            for i in range(16):
                onset = bar_start + i * 0.25
                if onset >= total:
                    break
                if i % 4 == 0:
                    notes.append(
                        NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.2, velocity=110)
                    )
                if i % 8 == 4:
                    notes.append(
                        NoteInfo(pitch=SNARE, start=round(onset, 6), duration=0.15, velocity=100)
                    )
                notes.append(
                    NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.06, velocity=60)
                )
        else:
            for off in [0.0, 0.75, 2.0, 2.75]:
                if bar_start + off < total:
                    notes.append(
                        NoteInfo(
                            pitch=KICK, start=round(bar_start + off, 6), duration=0.3, velocity=105
                        )
                    )
            for beat in [1, 3]:
                if bar_start + beat < total:
                    notes.append(
                        NoteInfo(
                            pitch=SNARE,
                            start=round(bar_start + beat, 6),
                            duration=0.2,
                            velocity=100,
                        )
                    )
                    notes.append(
                        NoteInfo(
                            pitch=CLAP, start=round(bar_start + beat, 6), duration=0.15, velocity=80
                        )
                    )
            for i in range(8):
                if random.random() < 0.8:
                    onset = bar_start + i * 0.5
                    if onset < total:
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED, start=round(onset, 6), duration=0.1, velocity=60
                            )
                        )

    def _render_bass(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        for off in [0.0, 2.0]:
            if bar_start + off < total:
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(bar_start + off, 6), duration=1.5, velocity=90
                    )
                )

    def _render_melody(self, notes, bar_start, total, chord, key):
        mid = 66
        scale_pcs = [int(d) for d in key.degrees()]
        t = bar_start
        prev = mid
        while t < min(bar_start + 4.0, total):
            if random.random() < self.melody_density:
                pc = random.choice(scale_pcs)
                pitch = nearest_pitch(pc, prev)
                dur = random.choice([0.5, 1.0])
                notes.append(
                    NoteInfo(
                        pitch=max(48, min(84, pitch)), start=round(t, 6), duration=dur, velocity=70
                    )
                )
                prev = pitch
            t += 0.5

    def _render_perc(self, notes, bar_start, total):
        for i in range(8):
            if random.random() < 0.4:
                onset = bar_start + i * 0.5
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=SHAKER, start=round(onset, 6), duration=0.08, velocity=40)
                    )
