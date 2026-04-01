"""
generators/gqom.py — Gqom pattern generator.

Layer: Application / Domain
Style: Gqom, South African dance, Durban house.

Generates the distinctive Gqom sound:
  - Heavy, syncopated kick patterns
  - Dark, minimal atmosphere
  - Sparse percussion
  - Distorted bass hits
  - Vocal stabs

Variants:
    "classic"    — classic Durban Gqom
    "dark"       — darker, more aggressive
    "minimal"    — minimal Gqom
    "sgubhu"     — Sgubhu (Gqom subgenre)
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
RIM = 37


@dataclass
class GqomGenerator(PhraseGenerator):
    """Gqom pattern generator. variant: classic, dark, minimal, sgubhu."""

    name: str = "Gqom Generator"
    variant: str = "classic"
    kick_weight: float = 0.8
    include_vocal_stabs: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "classic",
        kick_weight: float = 0.8,
        include_vocal_stabs: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.kick_weight = max(0.0, min(1.0, kick_weight))
        self.include_vocal_stabs = include_vocal_stabs

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
            self._render_kicks(notes, bar_start, duration_beats, chord, low)
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

    def _render_kicks(self, notes, bar_start, total, chord, low):
        vel = int(100 + self.kick_weight * 25)
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        if self.variant == "classic":
            offsets = [0.0, 0.5, 1.0, 2.0, 2.5, 3.0]
        elif self.variant == "sgubhu":
            offsets = [0.0, 0.75, 1.5, 2.0, 2.75, 3.5]
        elif self.variant == "minimal":
            offsets = [0.0, 2.0]
        else:
            offsets = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
        for off in offsets:
            onset = bar_start + off
            if onset >= total:
                continue
            is_main = off in (0.0, 2.0)
            v = vel if is_main else int(vel * 0.7)
            notes.append(
                NoteInfo(
                    pitch=KICK,
                    start=round(onset, 6),
                    duration=0.3 if is_main else 0.2,
                    velocity=min(MIDI_MAX, v),
                )
            )
            if is_main:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.8, velocity=v - 10)
                )
            if self.include_vocal_stabs and random.random() < 0.2:
                stab_pitch = nearest_pitch(chord.root, 72)
                notes.append(
                    NoteInfo(
                        pitch=stab_pitch, start=round(onset + 0.125, 6), duration=0.15, velocity=60
                    )
                )

    def _render_perc(self, notes, bar_start, total):
        for i in range(8):
            if random.random() < 0.5:
                onset = bar_start + i * 0.5
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.08, velocity=45)
                    )
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total and random.random() < 0.7:
                notes.append(
                    NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.15, velocity=80)
                )
