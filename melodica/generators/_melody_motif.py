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

        # Anchor pitch for transpose/invert/retrograde/fragment. Set once at the
        # start of each motif cycle (i==0) so the stored contour is reproduced
        # from a fixed reference instead of compounding off the drifting
        # prev_pitch (which is itself the previous motif note → runaway upward).
        self._motif_anchor: int | None = None
        self._frag_len: int | None = None

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

    def set_variation(self, variation: str) -> None:
        """Force the next motif application to use a specific variation.

        Maps a variation name to the index used by ``apply``. Used by the
        drama-arc strategy in MelodyGenerator. Resets after one use.
        """
        _VARIATIONS = ["transpose", "invert", "retrograde", "sequence", "fragment"]
        if variation not in _VARIATIONS:
            return
        self._variation_idx = _VARIATIONS.index(variation)

    def boost_probability(self, amount: float) -> None:
        """Temporarily increase the motif trigger probability for the next use."""
        self._motif_probability_boost = max(0.0, amount)

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

    def _fit_anchor(self, anchor: int, span_lo: int, span_hi: int, low: int, high: int) -> int:
        """Octave-fold the anchor so a motif spanning [span_lo, span_hi] above it
        stays within [low, high]. Prevents the motif climbing to the register
        ceiling each cycle (ascending motifs would otherwise stack upward)."""
        # anchor + span_hi must be <= high, anchor + span_lo must be >= low
        while anchor + span_hi > high and anchor - 12 >= low - span_lo:
            anchor -= 12
        while anchor + span_lo < low and anchor + 12 + span_hi <= high:
            anchor += 12
        return anchor

    def _apply_transpose(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Transpose the stored motif so its first note lands on the anchor.

        The anchor is captured at the start of each motif cycle (i==0) from
        prev_pitch, then held for the rest of the cycle so the stored contour
        is reproduced verbatim instead of compounding off each emitted note.
        The anchor is octave-folded to keep the motif body in range.
        """
        motif = self._stored_motif
        i = idx % len(motif)
        if i == 0 or self._motif_anchor is None:
            # span of motif relative to its first note
            rel = [m - motif[0] for m in motif]
            self._motif_anchor = self._fit_anchor(prev_pitch, min(rel), max(rel), low, high)
        offset = self._motif_anchor - motif[0]
        pitch = motif[i] + offset
        return snap_to_scale(max(low, min(high, pitch)), key)

    def _apply_invert(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Invert intervals around the cycle anchor (negate each interval)."""
        intervals = self._stored_intervals
        n = len(intervals)
        i = idx % n
        if i == 0 or self._motif_anchor is None:
            self._motif_anchor = prev_pitch
        pitch = self._motif_anchor
        for step in range(i):
            pitch -= intervals[step]  # cumulative inverted contour from anchor
        return snap_to_scale(max(low, min(high, pitch)), key)

    def _apply_retrograde(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Play motif backwards, anchored at cycle start."""
        reversed_motif = list(reversed(self._stored_motif))
        i = idx % len(reversed_motif)
        if i == 0 or self._motif_anchor is None:
            self._motif_anchor = prev_pitch
        offset = self._motif_anchor - reversed_motif[0]
        pitch = reversed_motif[i] + offset
        return snap_to_scale(max(low, min(high, pitch)), key)

    def _apply_sequence(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Replay the stored interval contour transposed by a scale degree.

        A musical sequence repeats the figure at a new pitch level. The anchor
        and the degree-transposition are fixed once at the start of each cycle,
        then the contour is built additively from that anchor — NOT recomputed
        off the drifting prev_pitch (which double-compounded: prev moved AND the
        cumulative contour re-summed from zero, sending the line to the ceiling).
        """
        intervals = self._stored_intervals
        motif_len = len(intervals)
        i = idx % motif_len

        # Start of a new sequence cycle: pick transposition and anchor once.
        if i == 0 or self._seq_degree_shift is None or self._motif_anchor is None:
            self._seq_degree_shift = random.choice(_SEQUENCE_DEGREES)
            self._seq_motif_idx = idx

            degree_shift = self._seq_degree_shift
            scale_pcs = key.degrees()
            base_pc = prev_pitch % 12
            base_idx = next((si for si, pc in enumerate(scale_pcs) if pc == base_pc), None) if scale_pcs else None
            if scale_pcs and base_idx is not None:
                target_idx = (base_idx + degree_shift) % len(scale_pcs)
                semitone_shift = scale_pcs[target_idx] - scale_pcs[base_idx]
                if degree_shift > 0 and semitone_shift < 0:
                    semitone_shift += 12
                elif degree_shift < 0 and semitone_shift > 0:
                    semitone_shift -= 12
            else:
                semitone_shift = degree_shift * 2

            # Anchor = transposed start, octave-folded so the contour fits range.
            rel = [0]
            run = 0
            for iv in intervals:
                run += iv
                rel.append(run)
            self._motif_anchor = self._fit_anchor(
                int(prev_pitch + semitone_shift), min(rel), max(rel), low, high
            )

        cumulative = sum(intervals[:i])  # contour offset from anchor (i notes in)
        pitch = self._motif_anchor + cumulative
        return snap_to_scale(max(low, min(high, pitch)), key)

    def _apply_fragment(self, prev_pitch: int, low: int, high: int, key: Scale, idx: int) -> int:
        """Use only the first 2-3 intervals of the motif, anchored per cycle."""
        intervals = self._stored_intervals
        if self._frag_len is None:
            self._frag_len = min(random.choice([2, 2, 3]), len(intervals))
        frag_len = self._frag_len
        i = idx % frag_len
        if i == 0:
            self._motif_anchor = prev_pitch
            # re-pick fragment length each new cycle for variety
            self._frag_len = min(random.choice([2, 2, 3]), len(intervals))
            frag_len = self._frag_len
            i = idx % frag_len
        anchor = self._motif_anchor if self._motif_anchor is not None else prev_pitch
        cumulative = sum(intervals[:i])
        pitch = anchor + cumulative
        return snap_to_scale(max(low, min(high, pitch)), key)
