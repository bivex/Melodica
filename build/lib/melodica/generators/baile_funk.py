"""
generators/baile_funk.py — Brazilian Phonk / Baile Funk pattern generator.

Layer: Application / Domain
Style: Brazilian Phonk, Baile Funk, Funk Carока, Phonk Brasil.

Generates characteristic Baile Funk elements:
  - Heavy distorted 808 with long sustain
  - Characteristic percussion (tamborzão pattern)
  - MC vocal chop simulation
  - Aggressive cowbell/timbale hits
  - Sliding bass

Variants:
    "classic"      — classic funk carioca
    "phonk_br"     — Brazilian phonk fusion
    "mandela"      — Mandela-style aggressive funk
    "rasterinha"   — Rasterinha (slower, groovier)
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
COWBELL = 56
TIMBALE = 65
RIM = 37


@dataclass
class BaileFunkGenerator(PhraseGenerator):
    """
    Brazilian Phonk / Baile Funk pattern generator.

    variant:
        "classic", "phonk_br", "mandela", "rasterinha"
    bass_distortion:
        Amount of 808 distortion/saturation (0.0-1.0).
    percussion_density:
        Density of tamborzão percussion hits (0.0-1.0).
    mc_chops:
        Whether to include MC vocal chop hits.
    slide_amount:
        Amount of 808 pitch sliding in semitones (0-12).
    """

    name: str = "Baile Funk Generator"
    variant: str = "classic"
    bass_distortion: float = 0.7
    percussion_density: float = 0.6
    mc_chops: bool = True
    slide_amount: int = 7
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "classic",
        bass_distortion: float = 0.7,
        percussion_density: float = 0.6,
        mc_chops: bool = True,
        slide_amount: int = 7,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.bass_distortion = max(0.0, min(1.0, bass_distortion))
        self.percussion_density = max(0.0, min(1.0, percussion_density))
        self.mc_chops = mc_chops
        self.slide_amount = max(0, min(12, slide_amount))

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

            # 808 Bass
            self._render_bass(notes, bar_start, duration_beats, chord, low)

            # Tamborzão percussion
            self._render_tamborzao(notes, bar_start, duration_beats)

            # Kick
            self._render_kick(notes, bar_start, duration_beats)

            # MC chops
            if self.mc_chops:
                self._render_mc_chops(notes, bar_start, duration_beats, chord)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_bass(
        self,
        notes: list[NoteInfo],
        bar_start: float,
        total: float,
        chord: ChordLabel,
        low: int,
    ) -> None:
        root_pc = chord.root
        base_pitch = max(low, min(low + 12, nearest_pitch(root_pc, low + 6)))
        vel = int(100 + self.bass_distortion * 25)

        if self.variant == "rasterinha":
            # Rasterinha: slower bass
            offsets = [(0.0, 2.0), (2.0, 1.8)]
        elif self.variant == "mandela":
            # Mandela: aggressive, frequent
            offsets = [(0.0, 1.5), (1.5, 0.5), (2.5, 1.3)]
        else:
            offsets = [(0.0, 3.0), (3.0, 0.8)]

        prev_pitch = base_pitch
        for off, dur in offsets:
            onset = bar_start + off
            if onset >= total:
                continue
            pitch = base_pitch
            if random.random() < 0.4 and self.slide_amount > 0:
                slide_pc = (root_pc + self.slide_amount) % 12
                pitch = max(low, min(low + 12, nearest_pitch(slide_pc, prev_pitch)))
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=min(dur, 3.5),
                    velocity=min(MIDI_MAX, vel),
                )
            )
            prev_pitch = pitch

    def _render_tamborzao(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        """Tamborzão — characteristic baile funk percussion pattern."""
        # Cowbell/timbale pattern
        offsets = [0.0, 0.5, 1.0, 1.75, 2.0, 2.5, 3.0, 3.75]
        for off in offsets:
            if random.random() > self.percussion_density:
                continue
            onset = bar_start + off
            if onset >= total:
                continue
            pitch = COWBELL if random.random() < 0.5 else TIMBALE
            vel = 80 if off in (0.0, 2.0) else 60
            notes.append(NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.1, velocity=vel))

        # Hi-hat layer
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            if random.random() < 0.8:
                notes.append(
                    NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.08, velocity=55)
                )

    def _render_kick(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        if self.variant == "mandela":
            offsets = [0.0, 1.0, 2.0, 3.0]
        else:
            offsets = [0.0, 2.0]
        for off in offsets:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.3, velocity=110)
                )

    def _render_mc_chops(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        """MC vocal chop hits — pitched percussion."""
        mid = 72
        for off in [1.25, 3.25]:
            if random.random() < 0.5:
                continue
            onset = bar_start + off
            if onset >= total:
                continue
            pc = (chord.root + random.choice([0, 3, 7])) % 12
            pitch = nearest_pitch(pc, mid)
            notes.append(NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.15, velocity=65))
