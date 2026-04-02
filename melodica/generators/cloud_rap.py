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
generators/cloud_rap.py — Cloud Rap / Wave pattern generator.

Layer: Application / Domain
Style: Cloud rap, wave, ethereal hip-hop, drain.

Generates atmospheric cloud rap elements:
  - Reverb-heavy pad washes
  - Sparse, ethereal drums
  - Pitched vocal textures
  - Dreamy arpeggios

Variants:
    "cloud"   — classic cloud rap (Yung Lean style)
    "wave"    — bladee/drain gang wave
    "ethereal"— ethereal, ambient hip-hop
    "dark_cloud" — darker cloud rap
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
class CloudRapGenerator(PhraseGenerator):
    """
    Cloud Rap / Wave pattern generator.

    variant:
        "cloud", "wave", "ethereal", "dark_cloud"
    pad_density:
        Density of atmospheric pad notes (0.0-1.0).
    drum_sparseness:
        How sparse the drums are (0.0 = full, 1.0 = very sparse).
    arp_speed:
        Arpeggio speed: "slow" (8th), "medium" (16th), "fast" (32nd).
    """

    name: str = "Cloud Rap Generator"
    variant: str = "cloud"
    pad_density: float = 0.6
    drum_sparseness: float = 0.5
    arp_speed: str = "slow"
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "cloud",
        pad_density: float = 0.6,
        drum_sparseness: float = 0.5,
        arp_speed: str = "slow",
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.pad_density = max(0.0, min(1.0, pad_density))
        self.drum_sparseness = max(0.0, min(1.0, drum_sparseness))
        self.arp_speed = arp_speed

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
            self._render_pad(notes, bar_start, duration_beats, chord)
            self._render_drums(notes, bar_start, duration_beats)
            self._render_arp(notes, bar_start, duration_beats, chord, key)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_pad(self, notes, bar_start, total, chord):
        mid = 60
        pcs = chord.pitch_classes()[:4]
        if bar_start < total:
            for pc in pcs:
                pitch = nearest_pitch(pc, mid)
                vel = 40 if self.variant == "wave" else 45
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=vel)
                )

    def _render_drums(self, notes, bar_start, total):
        if random.random() > self.drum_sparseness:
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=KICK, start=round(bar_start, 6), duration=0.4, velocity=80)
                )
        if random.random() > self.drum_sparseness:
            snare_onset = bar_start + 2
            if snare_onset < total:
                pitch = RIM if self.variant == "dark_cloud" else SNARE
                notes.append(
                    NoteInfo(pitch=pitch, start=round(snare_onset, 6), duration=0.2, velocity=75)
                )
        sub = 0.5
        t = bar_start
        while t < min(bar_start + 4.0, total):
            if random.random() > self.drum_sparseness * 0.5:
                notes.append(
                    NoteInfo(pitch=HH_CLOSED, start=round(t, 6), duration=0.1, velocity=40)
                )
            t += sub

    def _render_arp(self, notes, bar_start, total, chord, key):
        sub = {"slow": 0.5, "medium": 0.25, "fast": 0.125}.get(self.arp_speed, 0.5)
        mid = 72
        pcs = [int(d) for d in key.degrees()]
        t = bar_start
        prev = mid
        while t < min(bar_start + 4.0, total):
            if random.random() < self.pad_density:
                pc = random.choice(pcs)
                pitch = nearest_pitch(pc, prev)
                notes.append(
                    NoteInfo(
                        pitch=max(60, min(84, pitch)),
                        start=round(t, 6),
                        duration=sub * 0.8,
                        velocity=35,
                    )
                )
                prev = pitch
            t += sub
