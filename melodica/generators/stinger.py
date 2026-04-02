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
generators/stinger.py — Game audio stinger/mnemonic generator.

Layer: Application / Domain
Style: AAA game audio, UI sounds, event cues.

Short musical cues (1-4 beats) for game events:
  - Discovery (ascending major)
  - Achievement (fanfare)
  - Danger (descending minor, tritone)
  - Death (descending chromatic)
  - Save point (gentle major arpeggio)
  - Level up (ascending major arpeggio)
  - Item get (quick major riff)
  - Quest complete (triumphant)
  - Fail/Error (dissonant cluster)
  - Stealth alert (sudden minor stab)

Each stinger type has characteristic:
  - Interval patterns
  - Velocity curves
  - Duration profiles
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch


STINGER_DEFS: dict[str, dict] = {
    "discovery": {
        "intervals": [0, 4, 7, 12],  # Major arpeggio up
        "durs": [0.25, 0.25, 0.25, 0.5],
        "vel_curve": "crescendo",
        "base_vel": 70,
    },
    "achievement": {
        "intervals": [0, 4, 7, 12, 16],  # Extended major
        "durs": [0.15, 0.15, 0.15, 0.15, 0.8],
        "vel_curve": "crescendo",
        "base_vel": 80,
    },
    "danger": {
        "intervals": [0, -1, -6],  # Tritone + minor second down
        "durs": [0.3, 0.3, 0.8],
        "vel_curve": "accent",
        "base_vel": 95,
    },
    "death": {
        "intervals": [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12],  # Chromatic descend
        "durs": [0.12] * 12 + [1.0],
        "vel_curve": "decrescendo",
        "base_vel": 90,
    },
    "save": {
        "intervals": [0, 7, 12],  # Root + fifth + octave
        "durs": [0.4, 0.4, 0.8],
        "vel_curve": "gentle",
        "base_vel": 55,
    },
    "level_up": {
        "intervals": [0, 2, 4, 5, 7, 9, 11, 12],  # Major scale run up
        "durs": [0.1] * 7 + [0.6],
        "vel_curve": "crescendo",
        "base_vel": 75,
    },
    "item_get": {
        "intervals": [0, 4, 7],  # Simple major triad
        "durs": [0.15, 0.15, 0.4],
        "vel_curve": "accent",
        "base_vel": 80,
    },
    "quest_complete": {
        "intervals": [0, 4, 7, 11, 14, 16],  # Maj7 + 9th arpeggio
        "durs": [0.2, 0.2, 0.2, 0.2, 0.2, 1.0],
        "vel_curve": "crescendo",
        "base_vel": 85,
    },
    "fail": {
        "intervals": [0, 1, 6],  # Minor 2nd + tritone
        "durs": [0.3, 0.3, 0.6],
        "vel_curve": "accent",
        "base_vel": 90,
    },
    "stealth_alert": {
        "intervals": [0, 3],  # Minor third stab
        "durs": [0.1, 0.8],
        "vel_curve": "sudden",
        "base_vel": 100,
    },
    "checkpoint": {
        "intervals": [0, 5, 7],  # 4th + 5th (open, peaceful)
        "durs": [0.3, 0.3, 0.6],
        "vel_curve": "gentle",
        "base_vel": 60,
    },
    "combo": {
        "intervals": [0, 7, 12, 19],  # Stacked fifths
        "durs": [0.08, 0.08, 0.08, 0.3],
        "vel_curve": "crescendo",
        "base_vel": 70,
    },
}


@dataclass
class StingerGenerator(PhraseGenerator):
    """
    Game audio stinger/mnemonic generator.

    stinger_type:
        "discovery", "achievement", "danger", "death", "save",
        "level_up", "item_get", "quest_complete", "fail",
        "stealth_alert", "checkpoint", "combo"
    root_note:
        Root pitch class (0=C, 5=F, etc.) for the stinger.
    register:
        Octave for the stinger (3-6).
    velocity_multiplier:
        Global velocity adjustment (0.5-1.5).
    variation:
        Whether to add random variation to timing and velocity.
    """

    name: str = "Stinger Generator"
    stinger_type: str = "discovery"
    root_note: int = 0
    register: int = 5
    velocity_multiplier: float = 1.0
    variation: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        stinger_type: str = "discovery",
        root_note: int = 0,
        register: int = 5,
        velocity_multiplier: float = 1.0,
        variation: bool = True,
    ) -> None:
        super().__init__(params)
        self.stinger_type = stinger_type
        self.root_note = root_note % 12
        self.register = max(3, min(6, register))
        self.velocity_multiplier = max(0.5, min(1.5, velocity_multiplier))
        self.variation = variation

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        defn = STINGER_DEFS.get(self.stinger_type, STINGER_DEFS["discovery"])
        base_pitch = self.root_note + self.register * 12
        intervals = defn["intervals"]
        durs = defn["durs"]
        vel_curve = defn["vel_curve"]
        base_vel = defn["base_vel"]

        notes: list[NoteInfo] = []
        t = 0.0
        total_notes = min(len(intervals), len(durs))

        for i in range(total_notes):
            pitch = base_pitch + intervals[i]
            pitch = max(24, min(108, pitch))
            dur = durs[i]
            if self.variation:
                dur += random.gauss(0, 0.02)
                dur = max(0.05, dur)

            # Velocity curve
            if vel_curve == "crescendo":
                vel = int(base_vel + (i / max(1, total_notes - 1)) * 30)
            elif vel_curve == "decrescendo":
                vel = int(base_vel - (i / max(1, total_notes - 1)) * 40)
            elif vel_curve == "accent":
                vel = base_vel if i == 0 else int(base_vel * 0.7)
            elif vel_curve == "sudden":
                vel = base_vel
            else:  # gentle
                vel = base_vel

            vel = int(vel * self.velocity_multiplier)
            if self.variation:
                vel += random.randint(-5, 5)
            vel = max(1, min(MIDI_MAX, vel))

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=max(0.05, dur),
                    velocity=vel,
                )
            )
            t += dur

        last_chord = chords[-1] if chords else None
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes
