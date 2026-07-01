"""Shared easing curves used across Melodica generators."""
from __future__ import annotations
import math


def ease_in_out(t: float) -> float:
    """Sine-based ease-in-out."""
    return (1.0 - math.cos(t * math.pi)) / 2.0


def ease_in(t: float) -> float:
    """Quadratic ease-in (slow start, fast end)."""
    return t * t


def ease_out(t: float) -> float:
    """Quadratic ease-out (fast start, slow end)."""
    return 1.0 - (1.0 - t) * (1.0 - t)
