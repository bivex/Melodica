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
rhythm/subdivision.py — SubdivisionGenerator.

Layer: Application / Domain
"""

from __future__ import annotations

import random as _random
from dataclasses import dataclass

from melodica.rhythm import RhythmEvent, RhythmGenerator


@dataclass
class SubdivisionGenerator(RhythmGenerator):
    """
    Subdivides each beat uniformly (e.g., straight 8ths, triplets, or 16ths).

    divisions_per_beat: The core subdivision (1 = quarter, 2 = 8th, 3 = triplet, 4 = 16th).
    skip_chance: Chance to omit a note (creates rests).
    tie_chance: Chance to tie notes together (creates longer notes / syncopation).
    seed: RNG seed for reproducible output. None = non-deterministic.
    """

    divisions_per_beat: int = 4
    skip_chance: float = 0.0
    tie_chance: float = 0.0
    seed: int | None = None

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        if duration_beats <= 0:
            return []

        rng = _random.Random(self.seed)
        events: list[RhythmEvent] = []
        slot_duration = 1.0 / max(1, self.divisions_per_beat)
        total_slots = int(round(duration_beats * self.divisions_per_beat))

        current_onset = 0.0
        current_dur = 0.0

        for i in range(total_slots):
            onset = i * slot_duration

            # Should we skip this slot?
            if rng.random() < self.skip_chance:
                # Flush current event if tying
                if current_dur > 0:
                    velocity_mod = 1.0 if (current_onset % 1.0) == 0 else 0.8
                    events.append(RhythmEvent(current_onset, current_dur * 0.95, velocity_mod))
                    current_dur = 0.0
                continue
                
            # We have a note. Should we tie it to the *previous* running note?
            if current_dur > 0 and rng.random() < self.tie_chance:
                current_dur += slot_duration
            else:
                # Flush previous
                if current_dur > 0:
                    velocity_mod = 1.0 if (current_onset % 1.0) == 0 else 0.8
                    events.append(RhythmEvent(current_onset, current_dur * 0.95, velocity_mod))
                
                # Start new
                current_onset = onset
                current_dur = slot_duration
                
        # Flush tail
        if current_dur > 0:
            velocity_mod = 1.0 if (current_onset % 1.0) == 0 else 0.8
            events.append(RhythmEvent(current_onset, current_dur * 0.95, velocity_mod))
            
        return events
