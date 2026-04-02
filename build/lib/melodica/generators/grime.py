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
generators/grime.py — Grime pattern generator.

Layer: Application / Domain
Style: Grime, UK grime, eskibeat, weightless.

Generates characteristic grime elements:
  - Square wave synth stabs
  - 140 BPM patterns
  - Aggressive bass
  - Sparse, hard-hitting drums

Variants:
    "classic"    — classic grime (Wiley style)
    "eskibeat"   — eskibeat (minimal, dark)
    "weightless" — weightless grime (Logos style)
    "modern"     — modern grime (Skepta/Stormzy)
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


@dataclass
class GrimeGenerator(PhraseGenerator):
    """Grime pattern generator. variant: classic, eskibeat, weightless, modern."""

    name: str = "Grime Generator"
    variant: str = "classic"
    synth_aggression: float = 0.7
    include_melody: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "classic",
        synth_aggression: float = 0.7,
        include_melody: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.synth_aggression = max(0.0, min(1.0, synth_aggression))
        self.include_melody = include_melody

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
            self._render_synth(notes, bar_start, duration_beats, chord)
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
        if self.variant == "weightless":
            # Minimal drums
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=KICK, start=round(bar_start, 6), duration=0.4, velocity=90)
                )
            snare_onset = bar_start + 2
            if snare_onset < total:
                notes.append(
                    NoteInfo(pitch=SNARE, start=round(snare_onset, 6), duration=0.2, velocity=85)
                )
        else:
            for off in [0.0, 1.0, 2.0, 3.0] if self.variant == "modern" else [0.0, 2.0]:
                if bar_start + off < total:
                    notes.append(
                        NoteInfo(
                            pitch=KICK, start=round(bar_start + off, 6), duration=0.3, velocity=110
                        )
                    )
            for beat in [1, 3]:
                if bar_start + beat < total:
                    notes.append(
                        NoteInfo(
                            pitch=SNARE,
                            start=round(bar_start + beat, 6),
                            duration=0.2,
                            velocity=105,
                        )
                    )
                    notes.append(
                        NoteInfo(
                            pitch=CLAP, start=round(bar_start + beat, 6), duration=0.15, velocity=85
                        )
                    )
            for i in range(8):
                onset = bar_start + i * 0.5
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.08, velocity=60)
                    )

    def _render_bass(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        if self.variant == "eskibeat":
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.5, velocity=95)
                )
        else:
            for off in [0.0, 2.0]:
                if bar_start + off < total:
                    notes.append(
                        NoteInfo(
                            pitch=pitch, start=round(bar_start + off, 6), duration=1.5, velocity=95
                        )
                    )

    def _render_synth(self, notes, bar_start, total, chord):
        mid = 60
        root = nearest_pitch(chord.root, mid)
        vel = int(80 + self.synth_aggression * 20)
        # Square wave stab pattern
        offsets = [0.0, 0.5, 2.0, 2.5] if self.variant == "classic" else [0.0, 1.5, 3.0]
        for off in offsets:
            if random.random() < 0.6:
                continue
            onset = bar_start + off
            if onset >= total:
                continue
            notes.append(
                NoteInfo(
                    pitch=root, start=round(onset, 6), duration=0.5, velocity=min(MIDI_MAX, vel)
                )
            )
            fifth = nearest_pitch((chord.root + 7) % 12, root)
            notes.append(
                NoteInfo(pitch=fifth, start=round(onset, 6), duration=0.5, velocity=vel - 10)
            )
