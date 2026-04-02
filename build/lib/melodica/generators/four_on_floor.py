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
generators/four_on_floor.py — Four-on-the-floor drum pattern generator.

Layer: Application / Domain
Style: House, techno, disco, EDM.

Four-on-the-floor is the quintessential dance music rhythm:
kick drum on every beat, hi-hats on offbeats, clap/snare on 2 and 4.

Variants:
    "house"    — classic house (open hats, clap on 2+4)
    "techno"   — driving techno (closed hats, rim on 2+4)
    "disco"    — disco (open hats on offbeats, tambourine)
    "progressive" — progressive house (syncopated hats)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
CLAP = 39
HH_CLOSED = 42
HH_OPEN = 46
RIM = 37
TAMB = 54
CRASH = 49


@dataclass
class FourOnFloorGenerator(PhraseGenerator):
    """
    Four-on-the-floor drum pattern generator.

    variant:
        "house", "techno", "disco", "progressive"
    hihat_style:
        "closed", "open", "mixed"
    clap_location:
        "2_4" (beats 2 and 4), "offbeat" (between beats)
    swing:
        Swing factor (0.0 = straight, 1.0 = full triplet swing).
    """

    name: str = "Four on the Floor Generator"
    variant: str = "house"
    hihat_style: str = "mixed"
    clap_location: str = "2_4"
    swing: float = 0.0
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "house",
        hihat_style: str = "mixed",
        clap_location: str = "2_4",
        swing: float = 0.0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.hihat_style = hihat_style
        self.clap_location = clap_location
        self.swing = max(0.0, min(1.0, swing))
        self.rhythm = rhythm

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

        bar = 0.0
        while bar < duration_beats:
            # Kick on every beat
            for beat in range(4):
                onset = bar + beat
                if onset < duration_beats:
                    notes.append(
                        NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.25, velocity=110)
                    )

            # Clap/Snare on 2 and 4
            if self.clap_location == "2_4":
                for b in [1, 3]:
                    onset = bar + b
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.2, velocity=100)
                        )
                        notes.append(
                            NoteInfo(pitch=SNARE, start=round(onset, 6), duration=0.2, velocity=95)
                        )
            else:
                for off in [0.5, 1.5, 2.5, 3.5]:
                    onset = bar + off
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.15, velocity=90)
                        )

            # Hi-hats
            if self.variant == "house":
                for i in range(8):
                    onset = bar + i * 0.5
                    if onset < duration_beats:
                        is_open = (
                            (i % 2 == 1) if self.hihat_style == "open" else (random.random() < 0.3)
                        )
                        hat = HH_OPEN if is_open else HH_CLOSED
                        vel = 75 if i % 2 == 0 else 60
                        notes.append(
                            NoteInfo(pitch=hat, start=round(onset, 6), duration=0.2, velocity=vel)
                        )

            elif self.variant == "techno":
                for i in range(8):
                    onset = bar + i * 0.5
                    if onset < duration_beats:
                        vel = 70 + random.randint(-5, 5)
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED, start=round(onset, 6), duration=0.1, velocity=vel
                            )
                        )
                # Rim on 2 and 4
                for b in [1, 3]:
                    onset = bar + b
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(pitch=RIM, start=round(onset, 6), duration=0.1, velocity=85)
                        )

            elif self.variant == "disco":
                for i in range(8):
                    onset = bar + i * 0.5
                    if onset < duration_beats:
                        is_open = i % 2 == 1
                        hat = HH_OPEN if is_open else HH_CLOSED
                        vel = 80 if i % 2 == 0 else 65
                        notes.append(
                            NoteInfo(pitch=hat, start=round(onset, 6), duration=0.2, velocity=vel)
                        )
                # Tambourine
                for i in range(8):
                    onset = bar + i * 0.5 + 0.05
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(pitch=TAMB, start=round(onset, 6), duration=0.1, velocity=55)
                        )

            elif self.variant == "progressive":
                # Syncopated hats
                for i in range(16):
                    onset = bar + i * 0.25
                    if onset < duration_beats and random.random() < 0.75:
                        vel = 65 + random.randint(-10, 10)
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED,
                                start=round(onset, 6),
                                duration=0.08,
                                velocity=max(1, vel),
                            )
                        )

            # Crash on first bar of phrase
            if bar % 16 == 0 and bar < duration_beats:
                notes.append(NoteInfo(pitch=CRASH, start=round(bar, 6), duration=1.0, velocity=95))

            bar += 4.0

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes
