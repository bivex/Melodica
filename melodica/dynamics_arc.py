# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica/dynamics_arc.py — Macro-dynamics velocity curve.
Interpolates dynamic multipliers across form sections.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
from melodica.form import MusicalForm

DYNAMICS_MAP = {
    "pp": 0.2,
    "p": 0.4,
    "mp": 0.55,
    "mf": 0.7,
    "f": 0.85,
    "ff": 1.0,
}


@dataclass
class DynamicsArc:
    """Dynamics curve across the entire duration of a piece."""

    curve_type: str  # "crescendo", "diminuendo", "swell", "terraced", "custom"
    # List of (beat, multiplier) control points
    control_points: list[tuple[float, float]]

    def velocity_at(self, beat: float) -> float:
        """Returns the velocity multiplier (0.0–1.0) at the given beat."""
        if not self.control_points:
            return 1.0

        # Sort control points just in case
        points = sorted(self.control_points, key=lambda x: x[0])

        # Out of bounds left
        if beat <= points[0][0]:
            return points[0][1]

        # Out of bounds right
        if beat >= points[-1][0]:
            return points[-1][1]

        # Binary search or linear scan to find surrounding points
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            if p1[0] <= beat <= p2[0]:
                # Linear interpolation
                denom = p2[0] - p1[0]
                if denom == 0.0:
                    return p1[1]
                t = (beat - p1[0]) / denom
                return p1[1] + t * (p2[1] - p1[1])

        return 1.0

    @staticmethod
    def from_form(form: MusicalForm) -> DynamicsArc:
        """Creates a smooth dynamics arc from a MusicalForm by interpolating between sections."""
        if not form.sections:
            return DynamicsArc(curve_type="flat", control_points=[(0.0, 1.0)])

        control_points: list[tuple[float, float]] = []
        prev_mult = DYNAMICS_MAP.get(form.sections[0].dynamics, 0.7)

        for i, sec in enumerate(form.sections):
            curr_mult = DYNAMICS_MAP.get(sec.dynamics, 0.7)
            
            if i == 0:
                # First section: starts immediately at its dynamic level
                control_points.append((sec.start_beat, curr_mult))
                control_points.append((sec.end_beat, curr_mult))
            else:
                # Transition window over the first portion of the new section
                transition_duration = min(4.0, sec.duration_beats * 0.2)
                
                if transition_duration > 0.0:
                    # Point at the boundary with previous section's level
                    control_points.append((sec.start_beat, prev_mult))
                    # Point at the end of the transition with the new section's level
                    control_points.append((sec.start_beat + transition_duration, curr_mult))
                else:
                    control_points.append((sec.start_beat, curr_mult))
                
                control_points.append((sec.end_beat, curr_mult))
                
            prev_mult = curr_mult

        # Remove duplicate beat entries, keeping the last one or sorting them properly
        # To avoid step conflicts, we filter carefully
        unique_points: list[tuple[float, float]] = []
        for p in sorted(control_points, key=lambda x: x[0]):
            if not unique_points or unique_points[-1][0] != p[0]:
                unique_points.append(p)
            else:
                # If there are two points at the same beat, keep the one matching the current flow
                # (e.g. if we have (40.0, 0.7) and (40.0, 0.4), they might create a vertical step,
                # but we've used a transition duration > 0, so this won't happen except for duration=0)
                unique_points[-1] = p

        return DynamicsArc(curve_type="custom", control_points=unique_points)
