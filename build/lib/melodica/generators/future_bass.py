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
generators/future_bass.py — Future Bass pattern generator.

Layer: Application / Domain
Style: Future bass, EDM, festival bass, melodic bass.

Generates characteristic future bass elements:
  - Supersaw chord chops
  - Sidechain pumping feel
  - Vocal chops
  - Build-ups and drops

Variants:
    "standard"   — standard future bass
    "festival"   — festival-ready (bigger, louder)
    "chill"      — chill future bass (softer)
    "wave_race"  — wave-race style (flume-influenced)
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


@dataclass
class FutureBassGenerator(PhraseGenerator):
    """
    Future Bass pattern generator.

    variant:
        "standard", "festival", "chill", "wave_race"
    chord_chop_rate:
        Rate of chord chops in beats (0.25 = 16th, 0.5 = 8th).
    sidechain_feel:
        Whether to simulate sidechain pumping via velocity.
    include_vocal_chops:
        Whether to include vocal chop hits.
    supersaw_voices:
        Number of supersaw voices per chord (3-7).
    """

    name: str = "Future Bass Generator"
    variant: str = "standard"
    chord_chop_rate: float = 0.5
    sidechain_feel: bool = True
    include_vocal_chops: bool = True
    supersaw_voices: int = 5
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "standard",
        chord_chop_rate: float = 0.5,
        sidechain_feel: bool = True,
        include_vocal_chops: bool = True,
        supersaw_voices: int = 5,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.chord_chop_rate = max(0.125, min(1.0, chord_chop_rate))
        self.sidechain_feel = sidechain_feel
        self.include_vocal_chops = include_vocal_chops
        self.supersaw_voices = max(3, min(7, supersaw_voices))

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
            self._render_chord_chops(notes, bar_start, duration_beats, chord)
            if self.include_vocal_chops:
                self._render_vocal_chops(notes, bar_start, duration_beats, chord)
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
        for beat in range(4):
            onset = bar_start + beat
            if onset >= total:
                break
            notes.append(NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.3, velocity=110))
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(pitch=SNARE, start=round(onset, 6), duration=0.2, velocity=105)
                )
                notes.append(
                    NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.15, velocity=90)
                )
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset < total:
                notes.append(
                    NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.1, velocity=65)
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

    def _render_chord_chops(self, notes, bar_start, total, chord):
        mid = 60
        root = chord.root
        is_minor = chord.quality.name in ("MINOR", "MIN7")
        third = (root + (3 if is_minor else 4)) % 12
        fifth = (root + 7) % 12
        seventh = (root + 10) % 12
        pcs = [root, third, fifth, seventh]
        t = bar_start
        idx = 0
        while t < min(bar_start + 4.0, total):
            # Sidechain: louder on downbeats, softer after
            if self.sidechain_feel:
                vel = 80 if idx % 2 == 0 else 50
            else:
                vel = 70
            for pc in pcs[: self.supersaw_voices - 2]:
                pitch = nearest_pitch(pc, mid)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=self.chord_chop_rate * 0.8,
                        velocity=vel,
                    )
                )
            t += self.chord_chop_rate
            idx += 1

    def _render_vocal_chops(self, notes, bar_start, total, chord):
        mid = 72
        root = chord.root
        for off in [0.5, 1.5, 3.25]:
            if random.random() < 0.4:
                continue
            onset = bar_start + off
            if onset >= total:
                continue
            pc = (root + random.choice([0, 4, 7, 11])) % 12
            pitch = nearest_pitch(pc, mid)
            notes.append(NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.2, velocity=60))
