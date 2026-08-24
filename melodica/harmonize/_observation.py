# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
harmonize/_observation.py — Shared segmentation and observation extraction for harmonization engines.

Layer: Application / Domain
Rules:
  - Eliminates duplicate change point segmentation and pitch observation extraction across HMM/Genetic engines.
"""

from __future__ import annotations

from typing import Sequence
from melodica.types import BarGrid, NoteInfo


class HarmonizationSegmentation:
    """
    Centralized utility for harmonization timeline segmentation and melody observation extraction.
    """

    @staticmethod
    def get_change_points(
        duration: float,
        chord_change: str = "bars",
        bar_grid: BarGrid | None = None,
    ) -> list[float]:
        """Compute chord change timestamp boundaries across total duration."""
        bpb = bar_grid.beats_per_bar if bar_grid is not None else 4.0
        if chord_change == "bars":
            step = float(bpb)
        elif chord_change == "strong_beats":
            step = float(bpb) / 2.0
        elif chord_change == "half_bars":
            step = float(bpb) / 2.0
        elif chord_change == "half_beats":
            step = 0.5
        elif chord_change == "beats":
            step = 1.0
        else:
            step = 1.0

        points: list[float] = []
        t = 0.0
        while t < duration:
            points.append(t)
            t += step
        return points

    @staticmethod
    def extract_observations(
        melody: Sequence[NoteInfo],
        change_points: Sequence[float],
        default_pc: int = 0,
    ) -> list[list[int]]:
        """
        Extract pitch classes for each chord change interval [cp, next_cp).
        Returns a list of pitch class lists per interval.
        """
        if not change_points:
            return []

        sorted_m = sorted(melody, key=lambda n: n.start)
        observations: list[list[int]] = []
        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")
            pcs = [n.pitch % 12 for n in sorted_m if cp <= n.start < next_cp]
            observations.append(pcs if pcs else [default_pc])
        return observations
