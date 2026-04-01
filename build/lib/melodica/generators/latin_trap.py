"""
generators/latin_trap.py — Latin Trap pattern generator.

Layer: Application / Domain
Style: Latin trap, reggaeton trap, Spanish trap, urbano.

Fusion of reggaeton dembow with trap production:
  - Dembow-influenced kick/snare patterns
  - 808 bass with Latin flavor
  - Trap hi-hat rolls
  - Plena/bomba percussion accents

Variants:
    "reggaeton_trap" — standard Latin trap
    "urbano"         — Bad Bunny / Ozuna style
    "spanish_trap"   — Spanish trap (C. Tangana style)
    "bachata_trap"   — Bachata + trap fusion
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


@dataclass
class LatinTrapGenerator(PhraseGenerator):
    """
    Latin Trap pattern generator.

    variant:
        "reggaeton_trap", "urbano", "spanish_trap", "bachata_trap"
    dembow_influence:
        How much dembow rhythm is used (0.0-1.0).
    hat_rolls:
        Whether to include trap hi-hat rolls.
    include_percussion:
        Whether to add Latin percussion layers.
    """

    name: str = "Latin Trap Generator"
    variant: str = "reggaeton_trap"
    dembow_influence: float = 0.6
    hat_rolls: bool = True
    include_percussion: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "reggaeton_trap",
        dembow_influence: float = 0.6,
        hat_rolls: bool = True,
        include_percussion: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.dembow_influence = max(0.0, min(1.0, dembow_influence))
        self.hat_rolls = hat_rolls
        self.include_percussion = include_percussion

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
            self._render_808(notes, bar_start, duration_beats, chord, low)
            self._render_drums(notes, bar_start, duration_beats)
            if self.include_percussion:
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

    def _render_808(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        for off in [0.0, 2.0] if self.dembow_influence > 0.5 else [0.0, 1.5, 3.0]:
            if bar_start + off < total:
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(bar_start + off, 6), duration=1.5, velocity=95
                    )
                )

    def _render_drums(self, notes, bar_start, total):
        # Dembow-influenced kick/snare
        if self.dembow_influence > 0.5:
            kick_offs = [0.0, 0.75, 2.0, 2.75]
        else:
            kick_offs = [0.0, 2.0]
        for off in kick_offs:
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
                        pitch=SNARE, start=round(bar_start + beat, 6), duration=0.2, velocity=105
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=CLAP, start=round(bar_start + beat, 6), duration=0.15, velocity=85
                    )
                )
        # Hats
        sub = 0.25
        t = bar_start
        idx = 0
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.85:
                notes.append(
                    NoteInfo(
                        pitch=HH_CLOSED,
                        start=round(t, 6),
                        duration=0.1,
                        velocity=70 if idx % 4 == 0 else 50,
                    )
                )
            # Rolls
            if self.hat_rolls and random.random() < 0.15 and idx < 15:
                for r in range(random.choice([3, 5])):
                    r_onset = t + r * (sub / 5)
                    if r_onset < total:
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED, start=round(r_onset, 6), duration=0.05, velocity=45
                            )
                        )
            t += sub
            idx += 1

    def _render_perc(self, notes, bar_start, total):
        for i in range(8):
            if random.random() < 0.3:
                onset = bar_start + i * 0.5
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=SHAKER, start=round(onset, 6), duration=0.08, velocity=40)
                    )
