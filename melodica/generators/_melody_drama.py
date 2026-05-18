"""Melody dramatic arc — global tension shaping over the full duration.

Responsibilities:
  - Compute tension level (0.0-1.0) at any point in the piece
  - Shape register, velocity, density, rhythm based on tension
  - Place dramatic pauses at structurally important moments
  - Control motivic development strategy (full → fragment → return)
"""

from __future__ import annotations

import math
import random


DRAMA_SHAPE_OPTIONS = frozenset({
    "none",
    "crescendo",       # steady build to peak at ~70%, then resolve
    "dramatic",        # slow start, steep build, sharp peak, gentle fall
    "tension_release", # two peaks: build at 40%, bigger peak at 75%
    "epic",            # slow build, late peak at 80%, powerful resolution
})


class DramaticArc:
    """Computes per-event dramatic shaping based on global position."""

    def __init__(
        self,
        shape: str = "dramatic",
        total_duration: float = 32.0,
        peak_position: float = 0.70,
        global_offset: float = 0.0,
    ) -> None:
        if shape not in DRAMA_SHAPE_OPTIONS:
            raise ValueError(
                f"drama_shape must be one of {sorted(DRAMA_SHAPE_OPTIONS)}; got {shape!r}"
            )
        self.shape = shape
        self.total_duration = max(1.0, total_duration)
        self.peak_position = max(0.3, min(0.9, peak_position))
        self.global_offset = max(0.0, min(1.0, global_offset))

    def tension(self, onset: float) -> float:
        """Return tension level (0.0-1.0) at the given onset."""
        if self.shape == "none":
            # Even with no shape, global position adds slight buildup
            return min(1.0, 0.4 + self.global_offset * 0.3)

        t = min(1.0, onset / self.total_duration)
        pk = self.peak_position

        if self.shape == "crescendo":
            local_tension = _crescendo_curve(t, pk)
        elif self.shape == "dramatic":
            local_tension = _dramatic_curve(t, pk)
        elif self.shape == "tension_release":
            local_tension = _two_peak_curve(t, pk)
        elif self.shape == "epic":
            local_tension = _epic_curve(t, pk)
        else:
            local_tension = 0.5

        # Global buildup: later sections are more intense
        # We mix local section tension with global song progress
        effective_tension = local_tension * (0.8 + 0.2 * self.global_offset) + (self.global_offset * 0.1)
        return min(1.0, effective_tension)

    def register_shift(self, onset: float, range_span: int) -> int:
        """Extra register offset in semitones based on tension."""
        ten = self.tension(onset)
        # At peak tension, shift up by up to 40% of range
        return int(ten * range_span * 0.4)

    def velocity_scale(self, onset: float) -> float:
        """Velocity multiplier from dramatic arc (0.8-1.4)."""
        ten = self.tension(onset)
        return 0.8 + ten * 0.6

    def density_mult(self, onset: float) -> float:
        """Density multiplier — more notes at higher tension."""
        ten = self.tension(onset)
        return 0.7 + ten * 0.6

    def rhythm_compression(self, onset: float) -> float:
        """Rhythm compression factor (1.0=normal, 0.5=half duration=fast)."""
        ten = self.tension(onset)
        # Before peak: compress. After peak: expand back.
        t = min(1.0, onset / self.total_duration)
        if t < self.peak_position:
            return 1.0 - ten * 0.35
        else:
            return 0.65 + (1.0 - ten) * 0.35

    def is_dramatic_pause(self, onset: float, last_interval: int, event_idx: int, total_events: int) -> bool:
        """Should we insert a dramatic pause here?"""
        if self.shape == "none":
            return False

        t = onset / self.total_duration
        ten = self.tension(onset)

        # 1) Pause before the big climax (just before peak)
        if abs(t - self.peak_position) < 0.03 and last_interval == 0:
            if random.random() < 0.6:
                return True

        # 2) Pause after a big leap during high tension
        if ten > 0.6 and abs(last_interval) >= 7:
            if random.random() < 0.35:
                return True

        # 3) Breathing pause in the final resolution zone (last 10%)
        if t > 0.90 and random.random() < 0.12:
            return True

        return False

    def pause_duration(self, onset: float) -> float:
        """How long should a dramatic pause be?"""
        t = onset / self.total_duration
        pk = self.peak_position

        # Before climax: longer pause (anticipation)
        if abs(t - pk) < 0.05:
            return random.choice([1.0, 1.5, 2.0])
        # After big leap: medium
        return random.choice([0.5, 0.75, 1.0])

    def motif_strategy(self, onset: float) -> str:
        """What kind of motivic development should we use at this point?

        Returns: "full", "fragment", "sequence", "invert", "return"
        """
        if self.shape == "none":
            return "full"

        t = onset / self.total_duration
        ten = self.tension(onset)

        # Opening: full motifs
        if t < 0.15:
            return "full"

        # Rising tension: fragments and sequences (building energy)
        if ten > 0.7 and t < self.peak_position:
            return random.choices(
                ["fragment", "sequence", "fragment", "invert"],
                weights=[4, 3, 4, 1],
            )[0]

        # At peak: fragments and inversions (dramatic)
        if t >= self.peak_position - 0.05 and t <= self.peak_position + 0.1:
            return random.choices(
                ["fragment", "invert", "sequence"],
                weights=[3, 3, 2],
            )[0]

        # Resolution (after peak): return to original motif
        if t > self.peak_position + 0.15:
            return random.choices(
                ["full", "return", "sequence"],
                weights=[5, 3, 1],
            )[0]

        # Middle: mixed development
        return random.choices(
            ["full", "sequence", "fragment", "invert"],
            weights=[3, 2, 2, 1],
        )[0]

    def leap_probability(self, onset: float, base_prob: float) -> float:
        """Shape leap probability: more leaps at high tension, fewer in resolution."""
        ten = self.tension(onset)
        t = onset / self.total_duration

        if t > self.peak_position + 0.2:
            # Resolving: stepwise motion
            return base_prob * 0.5
        if ten > 0.7:
            # High tension: allow more leaps
            return min(0.8, base_prob * 1.5)
        return base_prob

    def cadence_strength(self, onset: float) -> float:
        """How strongly to pull toward cadence (0.0-1.0)."""
        t = onset / self.total_duration

        # Strong cadence at the very end
        if t > 0.92:
            return 0.95
        # Medium cadence at phrase boundaries during resolution
        if t > self.peak_position + 0.15:
            return 0.6
        # Weak cadence during buildup
        return 0.3


# ------------------------------------------------------------------
# Tension curves
# ------------------------------------------------------------------


def _crescendo_curve(t: float, pk: float) -> float:
    """Steady build, smooth peak, gentle fall."""
    if t < pk:
        return _ease_in_out(t / pk)
    else:
        return 1.0 - 0.5 * _ease_in_out((t - pk) / (1.0 - pk))


def _dramatic_curve(t: float, pk: float) -> float:
    """Slow start, steep build, sharp peak, gentle fall with dip."""
    if t < pk * 0.5:
        # Slow start (low tension)
        return _ease_in(t / (pk * 0.5)) * 0.25
    elif t < pk:
        # Steep build
        frac = (t - pk * 0.5) / (pk * 0.5)
        return 0.25 + 0.75 * _ease_in(frac)
    else:
        # Sharp fall with small secondary dip
        frac = (t - pk) / (1.0 - pk)
        base = 1.0 - 0.7 * _ease_out(frac)
        # Small re-rise at ~85% (false resolution)
        if 0.6 < frac < 0.8:
            base += 0.08 * math.sin((frac - 0.6) / 0.2 * math.pi)
        return base


def _two_peak_curve(t: float, pk: float) -> float:
    """Two peaks: first at ~40%, bigger at pk."""
    first_peak = pk * 0.55

    if t < first_peak:
        return _ease_in_out(t / first_peak) * 0.65
    elif t < pk * 0.75:
        # Dip between peaks
        frac = (t - first_peak) / (pk * 0.75 - first_peak)
        return 0.65 - 0.25 * math.sin(frac * math.pi)
    elif t < pk:
        # Second, bigger build
        frac = (t - pk * 0.75) / (pk * 0.25)
        return 0.4 + 0.6 * _ease_in(frac)
    else:
        frac = (t - pk) / (1.0 - pk)
        return 1.0 - 0.8 * _ease_out(frac)


def _epic_curve(t: float, pk: float) -> float:
    """Very slow build, late peak, powerful resolution."""
    if t < pk * 0.6:
        return _ease_in(t / (pk * 0.6)) * 0.15
    elif t < pk * 0.85:
        frac = (t - pk * 0.6) / (pk * 0.25)
        return 0.15 + 0.45 * _ease_in_out(frac)
    elif t < pk:
        frac = (t - pk * 0.85) / (pk * 0.15)
        return 0.6 + 0.4 * _ease_in(frac)
    else:
        frac = (t - pk) / (1.0 - pk)
        return 1.0 - 0.6 * _ease_out(frac)


def _ease_in_out(t: float) -> float:
    return (1.0 - math.cos(t * math.pi)) / 2.0


def _ease_in(t: float) -> float:
    return t * t


def _ease_out(t: float) -> float:
    return 1.0 - (1.0 - t) * (1.0 - t)
