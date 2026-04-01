"""
rhythm/rhythm_lab.py — RhythmLab.

Melodica's main modern rhythm generator. Works with a 16-step probability grid
per beat position. Three rhythms can be combined with operators.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.rhythm import RhythmEvent


@dataclass
class RhythmLab:
    """
    16-step probability grid rhythm generator.

    Each step has a probability (0.0-1.0) of being a hit.
    Three rhythms (A, B, C) can be combined with operators.
    """

    grid_a: list[float] = field(
        default_factory=lambda: [
            1.0,
            0.0,
            0.5,
            0.0,
            0.8,
            0.0,
            0.3,
            0.0,
            1.0,
            0.0,
            0.5,
            0.0,
            0.8,
            0.0,
            0.6,
            0.0,
        ]
    )
    grid_b: list[float] = field(default_factory=lambda: [0.0] * 16)
    grid_c: list[float] = field(default_factory=lambda: [0.0] * 16)
    operator: str = "A"  # "A", "B", "C", "A+B", "A-B", "A^B"
    accents: list[float] = field(
        default_factory=lambda: [
            1.2,
            0.8,
            0.9,
            0.8,
            1.1,
            0.8,
            0.9,
            0.8,
            1.2,
            0.8,
            0.9,
            0.8,
            1.1,
            0.8,
            0.9,
            0.8,
        ]
    )

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        step_dur = 0.25  # 16th notes
        events: list[RhythmEvent] = []
        t = 0.0
        while t < duration_beats:
            idx = int((t / step_dur)) % 16

            # Combine grids with operator
            prob = self._combine(idx)
            accent = self.accents[idx % len(self.accents)]

            if random.random() < prob:
                events.append(
                    RhythmEvent(
                        onset=round(t, 6),
                        duration=round(step_dur * 0.9, 6),
                        velocity_factor=accent,
                    )
                )
            t += step_dur
        return events

    def _combine(self, idx: int) -> float:
        a = self.grid_a[idx % len(self.grid_a)]
        b = self.grid_b[idx % len(self.grid_b)]
        c = self.grid_c[idx % len(self.grid_c)]

        match self.operator:
            case "A":
                return a
            case "B":
                return b
            case "C":
                return c
            case "A+B":
                return max(a, b)  # OR
            case "A-B":
                return max(0.0, a - b)  # difference
            case "A^B":
                return min(a, b)  # AND
            case _:
                return a
