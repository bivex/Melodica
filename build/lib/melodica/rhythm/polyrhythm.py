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
rhythm/polyrhythm.py — PolyrhythmGenerator.

Overlapping polyrhythmic patterns (e.g. 3 against 4).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from melodica.rhythm import RhythmEvent


@dataclass
class PolyrhythmGenerator:
    """
    Generates polyrhythmic patterns.

    ratio_a: pulses in the first layer (e.g. 3)
    ratio_b: pulses in the second layer (e.g. 4)
    include_both: if True, emit events from both layers
    """

    ratio_a: int = 3
    ratio_b: int = 4
    include_both: bool = True

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        events: list[RhythmEvent] = []
        bar_dur = 4.0  # one bar

        t = 0.0
        while t < duration_beats:
            dur = min(bar_dur, duration_beats - t)

            # Layer A: ratio_a evenly spaced
            for i in range(self.ratio_a):
                onset = t + (i / self.ratio_a) * dur
                if onset < duration_beats:
                    events.append(
                        RhythmEvent(
                            onset=round(onset, 6),
                            duration=round(dur / self.ratio_a * 0.9, 6),
                            velocity_factor=1.1 if i == 0 else 0.8,
                        )
                    )

            # Layer B: ratio_b evenly spaced
            if self.include_both:
                for i in range(self.ratio_b):
                    onset = t + (i / self.ratio_b) * dur
                    if onset < duration_beats:
                        events.append(
                            RhythmEvent(
                                onset=round(onset, 6),
                                duration=round(dur / self.ratio_b * 0.9, 6),
                                velocity_factor=0.7,
                            )
                        )

            t += bar_dur

        # Sort by onset and deduplicate
        events.sort(key=lambda e: e.onset)
        return events
