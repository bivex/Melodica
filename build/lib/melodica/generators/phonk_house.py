"""
generators/phonk_house.py — Phonk House pattern generator.

Layer: Application / Domain
Style: Phonk house, house phonk, drift house.

Fusion of phonk aesthetics with house music:
  - Four-on-floor kick with phonk cowbell
  - Drift-style bass slides
  - House hi-hats with phonk groove
  - Memphis vocal chops

Variants:
    "drift_house"  — drift phonk + house fusion
    "dark_house"   — dark phonk house
    "brazilian"    — Brazilian phonk house (baile + house)
    "classic"      — classic phonk house
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
COWBELL = 56


@dataclass
class PhonkHouseGenerator(PhraseGenerator):
    """Phonk House pattern generator. variant: drift_house, dark_house, brazilian, classic."""

    name: str = "Phonk House Generator"
    variant: str = "drift_house"
    cowbell_density: float = 0.6
    bass_slides: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "drift_house",
        cowbell_density: float = 0.6,
        bass_slides: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.cowbell_density = max(0.0, min(1.0, cowbell_density))
        self.bass_slides = bass_slides

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
            self._render_cowbell(notes, bar_start, duration_beats)
            self._render_bass(notes, bar_start, duration_beats, chord, low)
            self._render_clap(notes, bar_start, duration_beats)
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
                vel = 115 if beat % 2 == 0 else 100
                notes.append(
                    NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.3, velocity=vel)
                )

    def _render_hats(self, notes, bar_start, total):
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            is_open = (i == 3 or i == 7) and random.random() < 0.4
            hat = HH_OPEN if is_open else HH_CLOSED
            dur = 0.4 if is_open else 0.1
            notes.append(NoteInfo(pitch=hat, start=round(onset, 6), duration=dur, velocity=65))

    def _render_cowbell(self, notes, bar_start, total):
        if self.variant in ("drift_house", "brazilian"):
            for i in range(8):
                if random.random() < self.cowbell_density:
                    onset = bar_start + i * 0.5
                    if onset < total:
                        vel = 80 if i % 2 == 0 else 55
                        notes.append(
                            NoteInfo(
                                pitch=COWBELL, start=round(onset, 6), duration=0.1, velocity=vel
                            )
                        )

    def _render_bass(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        for off in [0.0, 2.0]:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=1.8, velocity=95)
                )
                if self.bass_slides and off == 0.0:
                    fifth = max(low, min(low + 12, nearest_pitch((chord.root + 7) % 12, pitch)))
                    if fifth != pitch:
                        notes.append(
                            NoteInfo(
                                pitch=fifth, start=round(onset + 1.5, 6), duration=0.5, velocity=80
                            )
                        )

    def _render_clap(self, notes, bar_start, total):
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.15, velocity=90)
                )
                notes.append(
                    NoteInfo(pitch=SNARE, start=round(onset, 6), duration=0.2, velocity=100)
                )
