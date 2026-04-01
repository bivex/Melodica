"""
generators/dembow.py — Dancehall / Reggaeton Dembow pattern generator.

Layer: Application / Domain
Style: Dancehall, reggaeton, Latin pop, dembow.

Generates the iconic dembow rhythm:
  - Characteristic kick-snare pattern
  - Shaker/percussion layers
  - Bass patterns
  - Cowbell accents

Variants:
    "classic"     — classic dembow rhythm
    "reggaeton"   — modern reggaeton production
    "dancehall"   — Jamaican dancehall
    "moombahton"  — moombahton (slowed dutch house + dembow)
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
SHAKER = 70
COWBELL = 56


@dataclass
class DembowGenerator(PhraseGenerator):
    """
    Dancehall / Reggaeton Dembow pattern generator.

    variant:
        "classic", "reggaeton", "dancehall", "moombahton"
    shaker_density:
        Density of shaker hits (0.0-1.0).
    include_bass:
        Whether to include bass line.
    cowbell_accent:
        Whether to add cowbell accents.
    swing_amount:
        Amount of swing/groove (0.0-1.0).
    """

    name: str = "Dembow Generator"
    variant: str = "classic"
    shaker_density: float = 0.7
    include_bass: bool = True
    cowbell_accent: bool = True
    swing_amount: float = 0.1
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "classic",
        shaker_density: float = 0.7,
        include_bass: bool = True,
        cowbell_accent: bool = True,
        swing_amount: float = 0.1,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.shaker_density = max(0.0, min(1.0, shaker_density))
        self.include_bass = include_bass
        self.cowbell_accent = cowbell_accent
        self.swing_amount = max(0.0, min(1.0, swing_amount))

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

            # Core dembow pattern
            self._render_dembow_core(notes, bar_start, duration_beats)

            # Shakers
            self._render_shakers(notes, bar_start, duration_beats)

            # Bass
            if self.include_bass:
                self._render_bass(notes, bar_start, duration_beats, chord)

            # Cowbell
            if self.cowbell_accent:
                self._render_cowbell(notes, bar_start, duration_beats)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_dembow_core(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        """The classic dembow: kick-kick-snare, kick-kick-snare."""
        sw = self.swing_amount * 0.25
        if self.variant == "moombahton":
            # Moombahton: slower, four on floor
            for beat in range(4):
                onset = bar_start + beat + (sw if beat % 2 == 1 else 0)
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.3, velocity=110)
                    )
                if beat in (1, 3):
                    sn_onset = bar_start + beat + 0.5 + sw
                    if sn_onset < total:
                        notes.append(
                            NoteInfo(
                                pitch=SNARE, start=round(sn_onset, 6), duration=0.2, velocity=105
                            )
                        )
        elif self.variant == "dancehall":
            # Dancehall: more syncopated
            offsets = [
                (0.0, KICK, 110),
                (0.5, KICK, 95),
                (1.0, SNARE, 105),
                (2.0, KICK, 110),
                (2.5, KICK, 95),
                (3.0, SNARE, 105),
                (3.5, RIM, 70),
            ]
            for off, pitch, vel in offsets:
                onset = bar_start + off + (sw if int(off) % 2 == 1 else 0)
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.2, velocity=vel)
                    )
        else:
            # Classic / Reggaeton dembow
            offsets = [
                (0.0, KICK, 115),
                (0.75, KICK, 90),
                (1.0, SNARE, 105),
                (1.5, KICK, 85),
                (2.0, KICK, 110),
                (2.75, KICK, 90),
                (3.0, SNARE, 105),
                (3.5, KICK, 80),
            ]
            for off, pitch, vel in offsets:
                onset = bar_start + off
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.2, velocity=vel)
                    )
            # Clap layer
            for beat in [1.0, 3.0]:
                onset = bar_start + beat
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.15, velocity=85)
                    )

    def _render_shakers(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        sub = 0.25 if self.variant == "moombahton" else 0.25
        t = bar_start
        idx = 0
        while t < min(bar_start + 4.0, total):
            if random.random() < self.shaker_density:
                vel = 50 if idx % 2 == 0 else 35
                notes.append(
                    NoteInfo(pitch=SHAKER, start=round(t, 6), duration=sub * 0.6, velocity=vel)
                )
            t += sub
            idx += 1

    def _render_bass(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        low = max(30, self.params.key_range_low)
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        for off in [0.0, 2.0]:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=1.5, velocity=90)
                )

    def _render_cowbell(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            if random.random() < 0.3:
                notes.append(
                    NoteInfo(pitch=COWBELL, start=round(onset, 6), duration=0.1, velocity=55)
                )
