"""
generators/afro_house.py — Afro House pattern generator.

Layer: Application / Domain
Style: Afro house, South African house, deep Afro.

Generates characteristic Afro House elements (Black Coffee style):
  - 4/4 house kick with African percussion
  - Deep bass lines
  - Vocal chant chops
  - Marimba/kalimba patterns

Variants:
    "deep"       — deep Afro house (Black Coffee)
    "spiritual"  — spiritual Afro house
    "tech"       — Afro tech house
    "organic"    — organic Afro house
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
SHAKER = 70
MARIMBA_LOW = 72
MARIMBA_HIGH = 96


@dataclass
class AfroHouseGenerator(PhraseGenerator):
    """Afro House generator. variant: deep, spiritual, tech, organic."""

    name: str = "Afro House Generator"
    variant: str = "deep"
    percussion_density: float = 0.6
    include_marimba: bool = True
    bass_depth: float = 0.7
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "deep",
        percussion_density: float = 0.6,
        include_marimba: bool = True,
        bass_depth: float = 0.7,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.percussion_density = max(0.0, min(1.0, percussion_density))
        self.include_marimba = include_marimba
        self.bass_depth = max(0.0, min(1.0, bass_depth))

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
            self._render_kick(notes, bar_start, duration_beats)
            self._render_hats(notes, bar_start, duration_beats)
            self._render_percussion(notes, bar_start, duration_beats)
            self._render_bass(notes, bar_start, duration_beats, chord, low)
            if self.include_marimba:
                self._render_marimba(notes, bar_start, duration_beats, chord)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_kick(self, notes, bar_start, total):
        for beat in range(4):
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.3, velocity=115)
                )

    def _render_hats(self, notes, bar_start, total):
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            is_open = (i == 3 or i == 7) and random.random() < 0.4
            hat = HH_OPEN if is_open else HH_CLOSED
            notes.append(
                NoteInfo(
                    pitch=hat, start=round(onset, 6), duration=0.3 if is_open else 0.1, velocity=65
                )
            )

    def _render_percussion(self, notes, bar_start, total):
        # African percussion layer
        pattern = [0.25, 0.75, 1.25, 1.75, 2.25, 3.0, 3.5, 3.75]
        for off in pattern:
            if random.random() > self.percussion_density:
                continue
            onset = bar_start + off
            if onset < total:
                pitch = random.choice([SHAKER, 63, 64])  # Shaker + percussion
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.1, velocity=55)
                )

    def _render_bass(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        vel = int(85 + self.bass_depth * 15)
        for off in [0.0, 2.0]:
            if bar_start + off < total:
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(bar_start + off, 6), duration=1.8, velocity=vel
                    )
                )

    def _render_marimba(self, notes, bar_start, total, chord):
        root_pc = chord.root
        mid = 78
        pcs = [root_pc, (root_pc + 3) % 12, (root_pc + 7) % 12, (root_pc + 10) % 12]
        t = bar_start
        idx = 0
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.7:
                pc = pcs[idx % len(pcs)]
                pitch = nearest_pitch(pc, mid)
                notes.append(
                    NoteInfo(
                        pitch=max(MARIMBA_LOW, min(MARIMBA_HIGH, pitch)),
                        start=round(t, 6),
                        duration=0.3,
                        velocity=65,
                    )
                )
            t += 0.5
            idx += 1
