"""
rhythm/schillinger.py — SchillingerGenerator.

Layer: Application / Domain
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from melodica.rhythm import RhythmEvent, RhythmGenerator


@dataclass
class SchillingerGenerator(RhythmGenerator):
    """
    Generates rhythms by interference of two numbers (binomials).
    A: First divisor (e.g. 3)
    B: Second divisor (e.g. 4)
    Result: interference of 3 against 4 creates a pattern of 12 units.
    """

    a: int = 3
    b: int = 4
    units_per_beat: int = 4  # Resolution

    def __init__(self, a: int = 3, b: int = 4, units_per_beat: int = 4) -> None:
        super().__init__()
        self.a = max(1, a)
        self.b = max(1, b)
        self.units_per_beat = max(1, units_per_beat)

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        # Calculate Least Common Multiple
        lcm = (self.a * self.b) // math.gcd(self.a, self.b)

        # Build the series (interference)
        # Marking onsets for a and b
        series = [False] * (lcm + 1)
        for i in range(0, lcm + 1, self.a):
            series[i] = True
        for i in range(0, lcm + 1, self.b):
            series[i] = True

        # Convert series of onsets into durations
        onsets = [i for i, hit in enumerate(series) if hit]
        intervals = []
        for j in range(len(onsets) - 1):
            intervals.append(onsets[j + 1] - onsets[j])

        # Normalize to beats
        unit_size = 1.0 / self.units_per_beat
        events = []
        total_time = 0.0

        # Repeat pattern to cover duration
        while total_time < duration_beats:
            for duration_units in intervals:
                if total_time >= duration_beats:
                    break

                onset = total_time
                dur = duration_units * unit_size

                events.append(
                    RhythmEvent(
                        onset=round(onset, 6),
                        duration=round(dur * 0.9, 6),  # slight gap
                        velocity_factor=1.0,
                    )
                )
                total_time += dur

        return events
