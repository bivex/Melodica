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
generators/hardstyle.py — Hardstyle / Hard Dance pattern generator.

Layer: Application / Domain
Style: Hardstyle, hard dance, euphoric hardstyle, rawstyle.

Generates characteristic hardstyle elements:
  - Distorted kick with pitch envelope
  - Reverse bass
  - Screech leads
  - Melodic euphoric sections

Variants:
    "euphoric"  — euphoric hardstyle (melodic)
    "raw"       — rawstyle (darker, harder)
    "reverse"   — reverse bass focused
    "classic"   — classic hardstyle
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


KICK = 36
HH_CLOSED = 42
CLAP = 39


@dataclass
class HardstyleGenerator(PhraseGenerator):
    """
    Hardstyle / Hard Dance pattern generator.

    variant:
        "euphoric", "raw", "reverse", "classic"
    kick_distortion:
        Amount of kick distortion (0.0-1.0).
    include_lead:
        Whether to include screech/melodic leads.
    reverse_bass_weight:
        How much reverse bass is used (0.0-1.0).
    """

    name: str = "Hardstyle Generator"
    variant: str = "euphoric"
    kick_distortion: float = 0.8
    include_lead: bool = True
    reverse_bass_weight: float = 0.5
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "euphoric",
        kick_distortion: float = 0.8,
        include_lead: bool = True,
        reverse_bass_weight: float = 0.5,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.kick_distortion = max(0.0, min(1.0, kick_distortion))
        self.include_lead = include_lead
        self.reverse_bass_weight = max(0.0, min(1.0, reverse_bass_weight))

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
            self._render_kick(notes, bar_start, duration_beats, chord, low)
            self._render_hats(notes, bar_start, duration_beats)
            if self.include_lead:
                self._render_lead(notes, bar_start, duration_beats, chord, key)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_kick(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        vel = int(100 + self.kick_distortion * 25)
        for beat in range(4):
            onset = bar_start + beat
            if onset >= total:
                break
            # Hardstyle kick: long, distorted
            notes.append(
                NoteInfo(
                    pitch=KICK, start=round(onset, 6), duration=0.8, velocity=min(MIDI_MAX, vel)
                )
            )
            # Reverse bass on offbeats
            if beat in (1, 3) and random.random() < self.reverse_bass_weight:
                rev_onset = onset - 0.25
                if rev_onset >= bar_start:
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(rev_onset, 6), duration=0.2, velocity=80)
                    )
            # Sub layer
            notes.append(
                NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.9, velocity=vel - 10)
            )

    def _render_hats(self, notes, bar_start, total):
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            notes.append(
                NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.1, velocity=70)
            )
            if random.random() < 0.3:
                notes.append(NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.1, velocity=50))

    def _render_lead(self, notes, bar_start, total, chord, key):
        mid = 72
        pcs = [int(d) for d in key.degrees()]
        sub = 0.5
        t = bar_start
        prev = mid
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.7:
                pc = random.choice(pcs)
                pitch = nearest_pitch(pc, prev)
                notes.append(
                    NoteInfo(
                        pitch=max(60, min(84, pitch)),
                        start=round(t, 6),
                        duration=sub * 0.9,
                        velocity=85,
                    )
                )
                prev = pitch
            t += sub
