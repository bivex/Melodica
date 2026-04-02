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
generators/boom_bap.py — Boom Bap / Classic Hip-Hop pattern generator.

Layer: Application / Domain
Style: Boom bap, golden age hip-hop, 90s rap.

Generates classic boom bap elements:
  - Dusty drum breaks
  - MPC-style swing
  - Jazz/soul sample chops
  - Classic kick-snare patterns

Variants:
    "classic"    — classic 90s boom bap
    "jazz_hop"   — jazz-influenced boom bap
    "golden_age" — golden age (DJ Premier style)
    "dusty"      — extra dusty, lo-fi boom bap
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
HH_OPEN = 46
CLAP = 39
RIM = 37


@dataclass
class BoomBapGenerator(PhraseGenerator):
    """
    Boom Bap / Classic Hip-Hop pattern generator.

    variant:
        "classic", "jazz_hop", "golden_age", "dusty"
    swing_ratio:
        Amount of MPC swing (0.5=straight, 0.67=heavy swing).
    chop_density:
        Density of jazz/soul sample chops (0.0-1.0).
    ghost_snares:
        Whether to include ghost snare hits.
    dusty_velocities:
        Whether to add vintage MPC velocity variation.
    """

    name: str = "Boom Bap Generator"
    variant: str = "classic"
    swing_ratio: float = 0.58
    chop_density: float = 0.4
    ghost_snares: bool = True
    dusty_velocities: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "classic",
        swing_ratio: float = 0.58,
        chop_density: float = 0.4,
        ghost_snares: bool = True,
        dusty_velocities: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.swing_ratio = max(0.5, min(0.75, swing_ratio))
        self.chop_density = max(0.0, min(1.0, chop_density))
        self.ghost_snares = ghost_snares
        self.dusty_velocities = dusty_velocities

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
            self._render_chops(notes, bar_start, duration_beats, chord)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _dusty_vel(self, base: int) -> int:
        if self.dusty_velocities:
            return max(30, min(MIDI_MAX, base + random.randint(-12, 12)))
        return base

    def _render_drums(self, notes, bar_start, total):
        sw = self.swing_ratio * 0.5
        # Kick
        for off in [0.0, 2.0]:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=KICK,
                        start=round(onset, 6),
                        duration=0.3,
                        velocity=self._dusty_vel(105),
                    )
                )
        # Extra kick (golden age style)
        if self.variant == "golden_age" and random.random() < 0.5:
            extra = bar_start + 0.75
            if extra < total:
                notes.append(
                    NoteInfo(
                        pitch=KICK,
                        start=round(extra, 6),
                        duration=0.2,
                        velocity=self._dusty_vel(85),
                    )
                )
        # Snare
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=SNARE,
                        start=round(onset, 6),
                        duration=0.2,
                        velocity=self._dusty_vel(105),
                    )
                )
        # Ghost snares
        if self.ghost_snares:
            for off in [1.75, 3.75]:
                if random.random() < 0.4:
                    onset = bar_start + off
                    if onset < total:
                        notes.append(
                            NoteInfo(
                                pitch=RIM,
                                start=round(onset, 6),
                                duration=0.1,
                                velocity=self._dusty_vel(35),
                            )
                        )
        # Hi-hats with swing
        for beat in range(4):
            h1 = bar_start + beat
            h2 = bar_start + beat + sw
            for h in [h1, h2]:
                if h >= total:
                    continue
                if random.random() < 0.9:
                    is_open = (beat == 3) and random.random() < 0.3
                    hat = HH_OPEN if is_open else HH_CLOSED
                    vel = self._dusty_vel(65 if h == h1 else 50)
                    notes.append(
                        NoteInfo(
                            pitch=hat,
                            start=round(h, 6),
                            duration=0.3 if is_open else 0.1,
                            velocity=vel,
                        )
                    )

    def _render_chops(self, notes, bar_start, total, chord):
        mid = 60
        root = chord.root
        if self.variant in ("jazz_hop", "golden_age"):
            pcs = chord.pitch_classes()[:4]
        else:
            pcs = [root, (root + 7) % 12]
        for off in [0.0, 1.5, 2.5]:
            if random.random() > self.chop_density:
                continue
            onset = bar_start + off
            if onset >= total:
                continue
            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, mid)
            dur = random.choice([0.5, 1.0])
            notes.append(
                NoteInfo(
                    pitch=pitch, start=round(onset, 6), duration=dur, velocity=self._dusty_vel(70)
                )
            )
