"""Melody motivic development — motif storage and variation.

Responsibilities:
  - Store motif from earlier phrase
  - Apply motif with transformation (transpose, invert, retrograde)
  - Motif probability-based referencing
"""

from __future__ import annotations

import random

from melodica.types import Scale
from melodica.utils import snap_to_scale


MOTIF_VARIATION_OPTIONS = frozenset({"transpose", "invert", "retrograde", "any"})


class MotifManager:
    """Manages motif storage and application."""

    def __init__(self, motif_probability: float = 0.0, motif_variation: str = "transpose") -> None:
        self.motif_probability = max(0.0, min(1.0, motif_probability))
        if motif_variation not in MOTIF_VARIATION_OPTIONS:
            raise ValueError(
                f"motif_variation must be one of {sorted(MOTIF_VARIATION_OPTIONS)}; got {motif_variation!r}"
            )
        self.motif_variation = motif_variation
        self._stored_motif: list[int] = []

    def store_motif(self, motif: list[int]) -> None:
        """Store a motif for future reuse."""
        if len(motif) >= 3:
            self._stored_motif = motif[-8:]  # keep last 8 notes max

    def clear(self) -> None:
        """Clear stored motif."""
        self._stored_motif.clear()

    def apply(self, prev_pitch: int, low: int, high: int, key: Scale, motif_idx: int) -> int:
        """Apply stored motif with variation, or return prev_pitch if not triggered."""
        if (
            self.motif_probability <= 0
            or len(self._stored_motif) < 3
            or random.random() >= self.motif_probability
        ):
            return prev_pitch

        # Pick variation
        variation = self.motif_variation
        if variation == "any":
            variation = random.choice(["transpose", "invert", "retrograde"])

        motif = self._stored_motif
        idx = motif_idx % len(motif)

        if variation == "transpose":
            offset = prev_pitch - motif[0]
            pitch = motif[idx] + offset
        elif variation == "invert":
            if idx == 0:
                pitch = prev_pitch
            else:
                center = sum(motif) // len(motif)
                interval = motif[idx] - center
                pitch = prev_pitch - interval
        elif variation == "retrograde":
            reversed_motif = list(reversed(motif))
            offset = prev_pitch - reversed_motif[0]
            pitch = reversed_motif[idx] + offset
        else:
            pitch = motif[idx]

        return snap_to_scale(max(low, min(high, pitch)), key)
