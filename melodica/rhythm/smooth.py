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
rhythm/smooth.py — SmoothRhythmGenerator.

Legato/sustained rhythm patterns with overlapping notes.
Good for pad-like or flowing accompaniment.
"""

from __future__ import annotations

from dataclasses import dataclass

from melodica.rhythm import RhythmEvent


SMOOTH_PATTERNS: dict[str, list[float]] = {
    "whole": [4.0],
    "half": [2.0, 2.0],
    "quarter_legato": [0.95, 0.95, 0.95, 0.95],
    "dotted_half": [3.0, 1.0],
    "flowing": [1.5, 1.5, 1.0],
    "breath": [2.0, 1.0, 1.0],
}


@dataclass
class SmoothRhythmGenerator:
    """
    Legato/sustained rhythm generator for pad-like textures.

    pattern_name: named pattern or custom durations
    overlap: beats of overlap between notes (for smooth transitions)
    """

    pattern_name: str = "quarter_legato"
    overlap: float = 0.1

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        if self.pattern_name in SMOOTH_PATTERNS:
            durs = SMOOTH_PATTERNS[self.pattern_name]
        else:
            durs = [1.0]

        events: list[RhythmEvent] = []
        t = 0.0
        idx = 0
        while t < duration_beats:
            d = durs[idx % len(durs)]
            if t + d > duration_beats:
                d = duration_beats - t
            events.append(
                RhythmEvent(
                    onset=round(t, 6),
                    duration=round(d + self.overlap, 6),
                    velocity_factor=1.0,
                )
            )
            t += d
            idx += 1
        return events
