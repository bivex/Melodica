"""
composer/tension_curve.py — Macro tension/drama planner.

Controls the overall arc of musical tension across 8-32 bars:
- Build-up
- Climax
- Resolution
- Rest
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class TensionPhase(Enum):
    REST = "rest"  # calm, stable
    BUILD = "build"  # increasing tension
    CLIMAX = "climax"  # peak tension
    RESOLUTION = "resolution"  # releasing tension
    SUSTAIN = "sustain"  # holding tension


@dataclass
class TensionPoint:
    """A point on the tension curve."""

    beat: float
    tension: float  # 0.0 = rest, 1.0 = maximum tension
    phase: TensionPhase


@dataclass
class TensionCurve:
    """
    Macro tension curve for a musical section.

    Generates a list of TensionPoints that can be used to modulate:
    - chord density (more chords = more tension)
    - dissonance level
    - velocity dynamics
    - register (higher = more tension)
    """

    total_beats: float = 32.0
    curve_type: str = "classical"  # "classical", "edm", "ambient", "build_release"
    peak_position: float = 0.7  # 0.0-1.0, where climax happens
    peak_intensity: float = 0.9  # 0.0-1.0, how intense the climax is
    resolution_length: float = 0.25  # fraction of total for resolution

    def generate(self) -> list[TensionPoint]:
        """Generate tension points along the curve."""
        points = []
        steps = max(8, int(self.total_beats / 2.0))

        for i in range(steps + 1):
            t = i / steps  # 0.0 to 1.0
            beat = t * self.total_beats

            if self.curve_type == "classical":
                tension = self._classical_curve(t)
            elif self.curve_type == "edm":
                tension = self._edm_curve(t)
            elif self.curve_type == "ambient":
                tension = self._ambient_curve(t)
            elif self.curve_type == "build_release":
                tension = self._build_release_curve(t)
            else:
                tension = self._classical_curve(t)

            phase = self._classify_phase(tension, t)
            points.append(TensionPoint(beat=round(beat, 6), tension=round(tension, 4), phase=phase))

        return points

    def tension_at(self, beat: float) -> float:
        """Get tension value at a specific beat."""
        points = self.generate()
        for i in range(len(points) - 1):
            if points[i].beat <= beat <= points[i + 1].beat:
                # Linear interpolation
                frac = (beat - points[i].beat) / (points[i + 1].beat - points[i].beat)
                return points[i].tension + (points[i + 1].tension - points[i].tension) * frac
        return 0.5

    def phase_at(self, beat: float) -> TensionPhase:
        """Get tension phase at a specific beat."""
        points = self.generate()
        for p in points:
            if p.beat >= beat:
                return p.phase
        return TensionPhase.SUSTAIN

    def _classical_curve(self, t: float) -> float:
        """Classical arc: rest → build → climax → resolution."""
        peak = self.peak_position
        if t < peak * 0.3:
            # Rest phase
            return 0.2
        elif t < peak:
            # Build-up (exponential)
            build_t = (t - peak * 0.3) / (peak - peak * 0.3)
            return 0.2 + build_t**1.5 * (self.peak_intensity - 0.2)
        elif t < peak + 0.05:
            # Climax
            return self.peak_intensity
        else:
            # Resolution
            res_t = (t - peak - 0.05) / (1.0 - peak - 0.05)
            return self.peak_intensity * (1.0 - res_t**0.7)

    def _edm_curve(self, t: float) -> float:
        """EDM: build → drop → build → drop."""
        # Sawtooth-like
        cycle = (t * 4) % 1.0  # 4 cycles
        if cycle < 0.8:
            return cycle / 0.8 * self.peak_intensity
        else:
            return self.peak_intensity * (1.0 - (cycle - 0.8) / 0.2 * 0.5)

    def _ambient_curve(self, t: float) -> float:
        """Ambient: gentle oscillation."""
        return 0.3 + 0.2 * math.sin(t * math.pi * 2)

    def _build_release_curve(self, t: float) -> float:
        """Build and release: rise then fall."""
        if t < 0.5:
            return t * 2 * self.peak_intensity
        else:
            return self.peak_intensity * (1.0 - (t - 0.5) * 2)

    def _classify_phase(self, tension: float, t: float) -> TensionPhase:
        if tension < 0.3:
            return TensionPhase.REST
        elif t < self.peak_position - 0.1:
            return TensionPhase.BUILD
        elif tension > self.peak_intensity - 0.2:
            return TensionPhase.CLIMAX
        elif t > self.peak_position + 0.1:
            return TensionPhase.RESOLUTION
        else:
            return TensionPhase.SUSTAIN
