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
generators/afro_samba.py — Afro Samba / Brazilian-African fusion generator.

Layer: Application / Domain
Style: Afro samba, Brazilian-African fusion, Afro-Latin.

Generates fusion of African and Brazilian rhythms:
  - Samba batucada patterns
  - African percussion overlays
  - Bossa nova guitar comping
  - Afro-Latin bass patterns

Variants:
    "samba_afro"  — Samba + African fusion
    "bossa_afro"  — Bossa nova + Afro
    "axe"         — Axé music
    "maracatu"    — Maracatu rhythm
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
TIMBALE = 65
SURDO = 36


@dataclass
class AfroSambaGenerator(PhraseGenerator):
    """Afro Samba / Brazilian-African fusion generator."""

    name: str = "Afro Samba Generator"
    variant: str = "samba_afro"
    perc_density: float = 0.7
    include_guitar: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "samba_afro",
        perc_density: float = 0.7,
        include_guitar: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.perc_density = max(0.0, min(1.0, perc_density))
        self.include_guitar = include_guitar

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
            self._render_batucada(notes, bar_start, duration_beats)
            self._render_bass(notes, bar_start, duration_beats, chord, low)
            if self.include_guitar:
                self._render_guitar(notes, bar_start, duration_beats, chord)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_batucada(self, notes, bar_start, total):
        if self.variant == "samba_afro":
            pattern = [
                (0.0, SURDO, 90),
                (0.5, SHAKER, 50),
                (0.75, TIMBALE, 65),
                (1.0, SNARE, 75),
                (1.5, SHAKER, 50),
                (1.75, TIMBALE, 60),
                (2.0, SURDO, 85),
                (2.5, SHAKER, 50),
                (2.75, TIMBALE, 65),
                (3.0, SNARE, 75),
                (3.25, HH_CLOSED, 55),
                (3.5, SHAKER, 50),
                (3.75, TIMBALE, 60),
            ]
        elif self.variant == "bossa_afro":
            pattern = [
                (0.0, SURDO, 80),
                (0.5, SHAKER, 45),
                (1.0, TIMBALE, 60),
                (1.5, SHAKER, 45),
                (2.0, SURDO, 75),
                (2.5, TIMBALE, 55),
                (3.0, SHAKER, 45),
                (3.5, TIMBALE, 60),
            ]
        elif self.variant == "axe":
            pattern = [
                (0.0, SURDO, 95),
                (0.5, CLAP, 70),
                (1.0, SNARE, 85),
                (1.5, CLAP, 65),
                (2.0, SURDO, 90),
                (2.5, CLAP, 70),
                (3.0, SNARE, 85),
                (3.5, CLAP, 65),
            ]
        else:  # maracatu
            pattern = [
                (0.0, SURDO, 95),
                (0.75, TIMBALE, 70),
                (1.5, SNARE, 80),
                (2.0, SURDO, 90),
                (2.75, TIMBALE, 70),
                (3.5, SNARE, 75),
            ]

        for off, pitch, vel in pattern:
            if random.random() > self.perc_density:
                continue
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.2, velocity=vel)
                )

    def _render_bass(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        for off in [0.0, 2.0]:
            if bar_start + off < total:
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(bar_start + off, 6), duration=1.5, velocity=85
                    )
                )

    def _render_guitar(self, notes, bar_start, total, chord):
        mid = 66
        root = chord.root
        is_minor = chord.quality.name in ("MINOR", "MIN7")
        third = (root + (3 if is_minor else 4)) % 12
        seventh = (root + 10) % 12
        pcs = [root, third, seventh]
        for off in [0.0, 1.5, 3.0]:
            onset = bar_start + off
            if onset >= total:
                continue
            for pc in pcs:
                pitch = nearest_pitch(pc, mid)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.6, velocity=60)
                )
