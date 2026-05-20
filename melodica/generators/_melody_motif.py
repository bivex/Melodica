"""Melody motivic development — motif storage and variation.

Responsibilities:
  - Store motif from earlier phrase (pitches + intervals + rhythm)
  - Apply motif with transformation (transpose, invert, retrograde, sequence, fragment)
  - Motif probability-based referencing with thematic curve
"""

from __future__ import annotations

import random

from melodica.types import Scale
from melodica.utils import snap_to_scale


MOTIF_VARIATION_OPTIONS = frozenset({"transpose", "invert", "retrograde", "sequence", "fragment", "any"})

# Sequence transposition intervals (scale degrees up or down)
_SEQUENCE_DEGREES = [-5, -4, -3, -2, 2, 3, 4, 5]


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
        self._stored_intervals: list[int] = []  # signed intervals between consecutive pitches
        self._stored_rhythm: list[float] = []   # relative durations

        # Dramatic arc overrides (set externally by MelodyGenerator)
        self._variation_idx: int = -1       # forced variation index, -1 = use motif_variation
        self._motif_probability_boost: float = 0.0  # added to motif_probability

        # Sequence state: one transposition per sequence cycle
        self._seq_degree_shift: int | None = None
        self._seq_motif_idx: int = 0

    def store_motif(self, motif: list[int], rhythm: list[float] | None = None) -> None:
        """Store a motif for future reuse."""
        if len(motif) >= 3:
            self._stored_motif = motif[-8:]
            # Compute intervallic contour
            self._stored_intervals = [
                motif[i + 1] - motif[i] for i in range(len(motif) - 1)
            ]
            if rhythm and len(rhythm) >= 2:
                self._stored_rhythm = rhythm[-8:]
            else:
                self._stored_rhythm = []

    def clear(self) -> None:
        """Clear stored motif."""
        self._stored_motif.clear()
        self._stored_intervals.clear()
        self._stored_rhythm.clear()

    def apply(
        self, prev_pitch: int, low: int, high: int, key: Scale, motif_idx: int
    ) -> int:
        """Apply stored motif with variation, or return prev_pitch if not triggered."""
        effective_prob = min(1.0, self.motif_probability + self._motif_probability_boost)
        # Reset boost after use
        self._motif_probability_boost = 0.0

        if (
            effective_prob <= 0
            or len(self._stored_intervals) < 2
            or random.random() >= effective_prob
        ):
            self._variation_idx = -1  # reset forced variation
            return prev_pitch

        # Pick variation: forced override from dramatic arc, or configured
        _VARIATIONS = ["transpose", "invert", "retrograde", "sequence", "fragment"]
        if self._variation_idx >= 0 and self._variation_idx < len(_VARIATIONS):
            variation = _VARIATIONS[self._variation_idx]
            self._variation_idx = -1  # reset after use
        else:
            variation = self.motif_variation
            if variation == "any":
                variation = random.choice(_VARIATIONS)

        intervals = self._stored_intervals

        if variation == "sequence":
            return self._apply_sequence(prev_pitch, low, high, key, motif_idx)
        elif variation == "fragment":
            return self._apply_fragment(prev_pitch, low, high, key, motif_idx)
        elif variation == "transpose":
            return self._apply_transpose(prev_pitch, low, high, key, motif_idx)
        elif variation == "invert":
            return self._apply_invert(prev_pitch, low, high, key, motif_idx)
        elif variation == "retrograde":
            return self._apply_retrograde(prev_pitch, low, high, key, motif_idx)

        return prev_pitch

    def get_rhythm(self) -> list[float]:
        """Return stored rhythm pattern, if available."""
        return list(self._stored_rhythm) if self._stored_rhythm else []

    # ------------------------------------------------------------------
    # Variation implementations
    # ------------------------------------------------------------------

    def _apply_transpose(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Transpose motif to start from prev_pitch."""
        motif = self._stored_motif
        i = idx % len(motif)
        offset = prev_pitch - motif[0]
        pitch = motif[i] + offset
        return snap_to_scale(max(low, min(high, pitch)), key)

    def _apply_invert(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Invert intervals around prev_pitch."""
        intervals = self._stored_intervals
        i = idx % len(intervals)
        pitch = prev_pitch
        for step in range(min(i + 1, len(intervals))):
            pitch -= intervals[step]  # invert: negate each interval
        return snap_to_scale(max(low, min(high, pitch)), key)

    def _apply_retrograde(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Play motif backwards."""
        reversed_motif = list(reversed(self._stored_motif))
        i = idx % len(reversed_motif)
        offset = prev_pitch - reversed_motif[0]
        pitch = reversed_motif[i] + offset
        return snap_to_scale(max(low, min(high, pitch)), key)

    def _apply_sequence(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Replay interval pattern transposed by a consistent scale degree."""
        intervals = self._stored_intervals
        motif_len = len(intervals)
        i = idx % motif_len

        # Start of a new sequence cycle: pick transposition once
        if i == 0 or self._seq_degree_shift is None:
            self._seq_degree_shift = random.choice(_SEQUENCE_DEGREES)
            self._seq_motif_idx = idx

        degree_shift = self._seq_degree_shift
        cumulative = sum(intervals[: i + 1])
        scale_pcs = key.degrees()
        if scale_pcs:
            base_pc = prev_pitch % 12
            base_idx = None
            for si, pc in enumerate(scale_pcs):
                if pc == base_pc:
                    base_idx = si
                    break
            if base_idx is not None:
                target_idx = (base_idx + degree_shift) % len(scale_pcs)
                semitone_shift = scale_pcs[target_idx] - scale_pcs[base_idx]
                if degree_shift > 0 and semitone_shift < 0:
                    semitone_shift += 12
                elif degree_shift < 0 and semitone_shift > 0:
                    semitone_shift -= 12
            else:
                semitone_shift = degree_shift * 2
        else:
            semitone_shift = degree_shift * 2

        pitch = prev_pitch + semitone_shift + cumulative
        return snap_to_scale(max(low, min(high, pitch)), key)

    def _apply_fragment(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Use only the first 2-3 intervals of the motif."""
        intervals = self._stored_intervals
        frag_len = min(random.choice([2, 2, 3]), len(intervals))
        i = idx % frag_len
        cumulative = sum(intervals[: i + 1])
        offset = prev_pitch - (self._stored_motif[0] if self._stored_motif else prev_pitch)
        pitch = self._stored_motif[0] + offset + cumulative
        return snap_to_scale(max(low, min(high, pitch)), key)
