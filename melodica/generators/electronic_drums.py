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
generators/electronic_drums.py — Electronic drum machine patterns.

Layer: Application / Domain
Style: House, techno, electro, synthwave, trap.

Produces drum patterns using classic electronic drum machine kits.
Supports 909, 808, CR-78, and LinnDrum style kits with
characteristic patterns and optional sidechain ducking simulation.

Drum map (MIDI):
    kick=36, snare=38, hh_closed=42, hh_open=46,
    clap=39, tom_low=41, tom_mid=45, tom_high=50,
    crash=49, ride=51, rim=37
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
CLAP = 39
TOM_LOW = 41
TOM_MID = 45
TOM_HIGH = 50
CRASH = 49
RIM = 37

KIT_CHARACTER: dict[str, dict] = {
    "909": {"kick_vel": 115, "snare_vel": 110, "hat_vel": 70, "use_clap": True},
    "808": {"kick_vel": 120, "snare_vel": 95, "hat_vel": 60, "use_clap": False},
    "cr78": {"kick_vel": 95, "snare_vel": 85, "hat_vel": 55, "use_clap": False},
    "linn": {"kick_vel": 110, "snare_vel": 108, "hat_vel": 65, "use_clap": True},
}

PATTERN_DEFS: dict[str, list[tuple[int, float, int, float]]] = {
    "four_on_floor": [
        (KICK, 0.0, 115, 0.3),
        (HH_CLOSED, 0.5, 65, 0.12),
        (KICK, 1.0, 110, 0.3),
        (HH_CLOSED, 1.5, 60, 0.12),
        (KICK, 2.0, 115, 0.3),
        (HH_CLOSED, 2.5, 65, 0.12),
        (KICK, 3.0, 110, 0.3),
        (HH_CLOSED, 3.5, 60, 0.12),
    ],
    "breakbeat": [
        (KICK, 0.0, 115, 0.3),
        (HH_CLOSED, 0.0, 65, 0.1),
        (HH_CLOSED, 0.5, 50, 0.1),
        (SNARE, 1.0, 110, 0.25),
        (HH_CLOSED, 1.0, 60, 0.1),
        (KICK, 1.5, 95, 0.25),
        (HH_CLOSED, 1.5, 50, 0.1),
        (KICK, 2.0, 110, 0.3),
        (HH_CLOSED, 2.0, 65, 0.1),
        (SNARE, 2.5, 90, 0.25),
        (HH_CLOSED, 2.75, 45, 0.1),
        (SNARE, 3.0, 100, 0.25),
        (KICK, 3.5, 90, 0.25),
        (HH_CLOSED, 3.5, 55, 0.1),
    ],
    "minimal": [
        (KICK, 0.0, 115, 0.35),
        (HH_CLOSED, 1.0, 60, 0.1),
        (KICK, 2.0, 110, 0.35),
        (HH_CLOSED, 3.0, 55, 0.1),
    ],
    "techno": [
        (KICK, 0.0, 120, 0.3),
        (HH_CLOSED, 0.25, 55, 0.08),
        (HH_CLOSED, 0.5, 60, 0.08),
        (HH_CLOSED, 0.75, 50, 0.08),
        (KICK, 1.0, 115, 0.3),
        (HH_CLOSED, 1.25, 55, 0.08),
        (HH_CLOSED, 1.5, 60, 0.08),
        (HH_CLOSED, 1.75, 50, 0.08),
        (KICK, 2.0, 120, 0.3),
        (CLAP, 2.0, 90, 0.2),
        (HH_CLOSED, 2.25, 55, 0.08),
        (HH_CLOSED, 2.5, 60, 0.08),
        (KICK, 3.0, 115, 0.3),
        (HH_CLOSED, 3.25, 55, 0.08),
        (HH_OPEN, 3.5, 65, 0.3),
        (HH_CLOSED, 3.75, 50, 0.08),
    ],
}


@dataclass
class ElectronicDrumsGenerator(PhraseGenerator):
    """
    Electronic drum patterns (909/808 style).

    kit:
        "909", "808", "cr78", "linn"
    pattern:
        "four_on_floor", "breakbeat", "minimal", "techno"
    sidechain:
        If True, simulate sidechain ducking by reducing velocity on
        non-kick hits that coincide with kick onsets.
    """

    name: str = "Electronic Drums Generator"
    kit: str = "909"
    pattern: str = "four_on_floor"
    sidechain: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        kit: str = "909",
        pattern: str = "four_on_floor",
        sidechain: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.kit = kit
        self.pattern = pattern
        self.sidechain = sidechain
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
        char = KIT_CHARACTER.get(self.kit, KIT_CHARACTER["909"])
        pattern_def = PATTERN_DEFS.get(self.pattern, PATTERN_DEFS["four_on_floor"])

        t = 0.0
        while t < duration_beats:
            kick_onsets: set[float] = set()
            for pitch, offset, base_vel, dur in pattern_def:
                onset = t + offset
                if onset >= duration_beats:
                    continue
                vel = base_vel
                # Kit character adjustments
                if pitch == KICK:
                    vel = char["kick_vel"]
                    kick_onsets.add(round(offset, 2))
                elif pitch == SNARE:
                    vel = char["snare_vel"]
                elif pitch in (HH_CLOSED, HH_OPEN):
                    vel = char["hat_vel"]
                elif pitch == CLAP and not char["use_clap"]:
                    pitch = SNARE
                    vel = char["snare_vel"]

                vel = max(1, min(127, vel + random.randint(-5, 5)))

                # Sidechain ducking
                if self.sidechain and pitch != KICK:
                    for kick_off in kick_onsets:
                        if abs(offset - kick_off) < 0.25:
                            vel = max(1, int(vel * 0.5))

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=dur,
                        velocity=vel,
                    )
                )
            t += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes
