"""
generators/dnb_jungle.py — Drum & Bass / Jungle pattern generator.

Layer: Application / Domain
Style: DnB, jungle, liquid DnB, neurofunk.

Generates characteristic DnB elements:
  - Fast breakbeat patterns (174 BPM feel)
  - Reese bass
  - Chopped Amen breaks
  - Sub-bass wobbles

Variants:
    "liquid"      — liquid DnB (musical, rolling)
    "jungle"      — jungle (chopped breaks, ragga)
    "neurofunk"   — neurofunk (dark, technical)
    "minimal"     — minimal DnB
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
TOM_LOW = 41
TOM_MID = 45


@dataclass
class DnBJungleGenerator(PhraseGenerator):
    """
    Drum & Bass / Jungle pattern generator.

    variant:
        "liquid", "jungle", "neurofunk", "minimal"
    break_density:
        Density of breakbeat chops (0.0-1.0).
    reese_amount:
        Amount of reese bass character (0.0-1.0).
    sub_weight:
        Weight of sub-bass vs mid bass (0.0-1.0).
    """

    name: str = "DnB Jungle Generator"
    variant: str = "liquid"
    break_density: float = 0.6
    reese_amount: float = 0.5
    sub_weight: float = 0.7
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "liquid",
        break_density: float = 0.6,
        reese_amount: float = 0.5,
        sub_weight: float = 0.7,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.break_density = max(0.0, min(1.0, break_density))
        self.reese_amount = max(0.0, min(1.0, reese_amount))
        self.sub_weight = max(0.0, min(1.0, sub_weight))

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
            self._render_breaks(notes, bar_start, duration_beats)
            self._render_bass(notes, bar_start, duration_beats, chord, low)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_breaks(self, notes, bar_start, total):
        """Chopped breakbeat pattern at DnB speed."""
        # DnB is in 4/4 but at ~174 BPM, so beats are shorter
        # We simulate 174 BPM feel within the 4-beat bar
        sub = 0.25  # 16th note grid
        if self.variant == "jungle":
            # Jungle: dense chopped breaks
            offsets = [0.0, 0.25, 0.5, 1.0, 1.25, 1.5, 2.0, 2.5, 2.75, 3.0, 3.25, 3.5]
            instruments = [
                KICK,
                HH_CLOSED,
                SNARE,
                KICK,
                HH_CLOSED,
                SNARE,
                KICK,
                HH_CLOSED,
                SNARE,
                TOM_LOW,
                HH_CLOSED,
                SNARE,
            ]
        elif self.variant == "neurofunk":
            offsets = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
            instruments = [KICK, SNARE, HH_CLOSED, KICK, SNARE, HH_CLOSED, KICK, SNARE]
        elif self.variant == "minimal":
            offsets = [0.0, 1.0, 2.0, 3.0]
            instruments = [KICK, SNARE, KICK, SNARE]
        else:  # liquid
            offsets = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.25, 3.5]
            instruments = [
                KICK,
                HH_CLOSED,
                SNARE,
                HH_CLOSED,
                KICK,
                HH_OPEN,
                SNARE,
                HH_CLOSED,
                HH_CLOSED,
            ]

        for off, inst in zip(offsets, instruments):
            onset = bar_start + off
            if onset >= total:
                continue
            if random.random() > self.break_density and inst in (HH_CLOSED, TOM_LOW):
                continue
            vel = 110 if inst in (KICK, SNARE) else 65
            notes.append(NoteInfo(pitch=inst, start=round(onset, 6), duration=0.15, velocity=vel))

    def _render_bass(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 18, nearest_pitch(chord.root, low + 12)))
        if self.variant == "neurofunk":
            # Aggressive mid-range bass
            for off in [0.0, 1.0, 2.0, 3.0]:
                if bar_start + off < total:
                    notes.append(
                        NoteInfo(
                            pitch=pitch + 12,
                            start=round(bar_start + off, 6),
                            duration=0.8,
                            velocity=90,
                        )
                    )
        elif self.variant == "liquid":
            # Rolling sub
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=85)
            )
        else:
            # Reese bass
            for off in [0.0, 2.0]:
                if bar_start + off < total:
                    notes.append(
                        NoteInfo(
                            pitch=pitch, start=round(bar_start + off, 6), duration=1.8, velocity=90
                        )
                    )
