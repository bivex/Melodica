"""
BarGrid — immutable value object representing a time signature's bar structure.
All computations are pure functions of quarter-note beats.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BarGrid:
    """Bar-aware time grid derived from a time signature.

    ``numerator`` is the top number (beats per bar),
    ``denominator`` is the bottom number (beat unit).
    """

    numerator: int = 4
    denominator: int = 4

    # ------------------------------------------------------------------
    # Core properties
    # ------------------------------------------------------------------

    @property
    def beats_per_bar(self) -> float:
        """Quarter-note beats per bar.

        4/4 -> 4.0, 3/4 -> 3.0, 6/8 -> 3.0, 5/4 -> 5.0, 7/8 -> 3.5
        """
        if self.denominator == 4:
            return float(self.numerator)
        if self.denominator == 8:
            return self.numerator * 0.5
        return self.numerator * (4.0 / self.denominator)

    # ------------------------------------------------------------------
    # Beat <-> Bar conversion
    # ------------------------------------------------------------------

    def bar_of(self, beat: float) -> int:
        """0-indexed bar number at *beat*."""
        return int(beat / self.beats_per_bar)

    def beat_in_bar(self, beat: float) -> float:
        """Offset within the current bar [0, beats_per_bar)."""
        return beat % self.beats_per_bar

    def is_downbeat(self, beat: float) -> bool:
        """True if *beat* falls on a bar-line (first beat of a bar)."""
        return self.beat_in_bar(beat) < 0.01

    def bar_start(self, bar_index: int) -> float:
        """Beat position of the start of bar *bar_index*."""
        return bar_index * self.beats_per_bar

    # ------------------------------------------------------------------
    # Alignment
    # ------------------------------------------------------------------

    def align_up(self, beat: float) -> float:
        """Round *beat* up to the next bar boundary."""
        bpb = self.beats_per_bar
        return math.ceil(beat / bpb) * bpb

    def align_down(self, beat: float) -> float:
        """Round *beat* down to the previous bar boundary."""
        bpb = self.beats_per_bar
        return math.floor(beat / bpb) * bpb

    # ------------------------------------------------------------------
    # Chord change points
    # ------------------------------------------------------------------

    def change_points(self, duration: float, mode: str = "bars") -> list[float]:
        """Generate chord-change beat positions for *duration* beats.

        *mode*:
          ``"bars"``         — every bar (default)
          ``"strong_beats"`` — every half-bar
          ``"beats"``        — every beat
        """
        bpb = self.beats_per_bar
        if mode == "bars":
            step = bpb
        elif mode == "strong_beats":
            step = bpb / 2.0
        else:
            step = 1.0
        pts: list[float] = []
        t = 0.0
        while t < duration - 0.01:
            pts.append(round(t, 6))
            t += step
        return pts
