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
generators/witch_house.py — Witch House pattern generator.

Layer: Application / Domain
Style: Witch house, drag, haunted house.

Generates characteristic witch house elements:
  - Slowed, chopped patterns
  - Dark atmospheric pads
  - Pitched-down vocals
  - Minimal, eerie drums

Variants:
    "classic"  — classic witch house
    "drag"     — drag/slowed
    "dark_ambient" — dark ambient witch house
    "occult"   — occult-influenced (more aggressive)
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
RIM = 37


@dataclass
class WitchHouseGenerator(PhraseGenerator):
    """Witch House pattern generator. variant: classic, drag, dark_ambient, occult."""

    name: str = "Witch House Generator"
    variant: str = "classic"
    slowdown_factor: float = 0.5
    pad_darkness: float = 0.8
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "classic",
        slowdown_factor: float = 0.5,
        pad_darkness: float = 0.8,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.slowdown_factor = max(0.25, min(1.0, slowdown_factor))
        self.pad_darkness = max(0.0, min(1.0, pad_darkness))

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
        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue
            self._render_drums(notes, bar_start, duration_beats)
            self._render_pad(notes, bar_start, duration_beats, chord)
            self._render_bass(notes, bar_start, duration_beats, chord)
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
        # Very sparse, slowed drums
        sp = 1.0 / self.slowdown_factor
        if bar_start < total:
            notes.append(NoteInfo(pitch=KICK, start=round(bar_start, 6), duration=0.5, velocity=80))
        snare_onset = bar_start + 2 * sp
        if snare_onset < total:
            notes.append(
                NoteInfo(pitch=SNARE, start=round(snare_onset, 6), duration=0.3, velocity=75)
            )
        # Minimal hats
        for i in range(4):
            onset = bar_start + i * sp
            if onset >= total:
                break
            if random.random() < 0.6:
                notes.append(
                    NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.15, velocity=35)
                )

    def _render_pad(self, notes, bar_start, total, chord):
        mid = 48  # Low register for darkness
        pcs = chord.pitch_classes()[:3]
        vel = int(35 + (1.0 - self.pad_darkness) * 20)
        if bar_start < total:
            for pc in pcs:
                pitch = nearest_pitch(pc, mid)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=vel)
                )
            # Dissonant added note
            if random.random() < 0.4:
                dissonant = (chord.root + random.choice([1, 6, 11])) % 12
                pitch = nearest_pitch(dissonant, mid)
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=vel - 10
                    )
                )

    def _render_bass(self, notes, bar_start, total, chord):
        low = max(24, self.params.key_range_low)
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        if bar_start < total:
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.5, velocity=85)
            )
