"""VelocityEnvelope — dynamic automation over time.

Maps beats to target velocities via control points, then applies proportional
scaling to a list of NoteInfo. Supports crescendo, diminuendo, swell, subito,
terrace dynamics, and custom curves (linear, exponential, logarithmic).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from melodica.types_pkg._notes import NoteInfo


@dataclass(slots=True)
class VelocityEnvelope:
    """Control-point envelope for velocity automation."""

    _points: list[tuple[float, float]] = field(default_factory=list)
    _ref_velocity: float = 80.0

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def add_point(self, beat: float, velocity: float) -> VelocityEnvelope:
        self._points.append((beat, velocity))
        return self

    def crescendo(
        self,
        start_beat: float,
        end_beat: float,
        start_vel: float,
        end_vel: float,
        curve: str = "linear",
        steps: int = 16,
    ) -> VelocityEnvelope:
        span = end_beat - start_beat
        for i in range(steps + 1):
            t = i / steps
            v = self._interpolate_value(start_vel, end_vel, t, curve)
            self._points.append((start_beat + span * t, v))
        return self

    def diminuendo(
        self,
        start_beat: float,
        end_beat: float,
        start_vel: float,
        end_vel: float,
        curve: str = "linear",
        steps: int = 16,
    ) -> VelocityEnvelope:
        return self.crescendo(start_beat, end_beat, start_vel, end_vel, curve, steps)

    def swell(
        self,
        peak_beat: float,
        start_vel: float,
        peak_vel: float,
        end_vel: float,
        start_beat: float = 0.0,
        end_beat: float | None = None,
        curve: str = "linear",
    ) -> VelocityEnvelope:
        end = end_beat if end_beat is not None else peak_beat * 2
        self.crescendo(start_beat, peak_beat, start_vel, peak_vel, curve)
        self.diminuendo(peak_beat, end, peak_vel, end_vel, curve)
        return self

    def subito(self, beat: float, velocity: float) -> VelocityEnvelope:
        self._points.append((beat, velocity))
        return self

    def terrace(self, levels: list[tuple[float, float]]) -> VelocityEnvelope:
        for beat, vel in levels:
            self._points.append((beat, vel))
        return self

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def velocity_at(self, beat: float) -> float:
        """Linear interpolation between control points."""
        if not self._points:
            return self._ref_velocity
        sorted_pts = sorted(self._points, key=lambda p: p[0])
        if beat <= sorted_pts[0][0]:
            return sorted_pts[0][1]
        if beat >= sorted_pts[-1][0]:
            return sorted_pts[-1][1]
        for i in range(len(sorted_pts) - 1):
            b0, v0 = sorted_pts[i]
            b1, v1 = sorted_pts[i + 1]
            if b0 <= beat <= b1:
                t = (beat - b0) / (b1 - b0) if b1 != b0 else 0.0
                return v0 + (v1 - v0) * t
        return self._ref_velocity

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def apply(self, notes: list[NoteInfo]) -> list[NoteInfo]:
        """Return NEW notes with velocities scaled by the envelope."""
        if not self._points:
            return [
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute,
                    articulation=n.articulation,
                    expression=n.expression,
                )
                for n in notes
            ]
        result: list[NoteInfo] = []
        for n in notes:
            env_vel = self.velocity_at(n.start)
            scale = env_vel / self._ref_velocity if self._ref_velocity > 0 else 1.0
            new_vel = max(1, min(127, round(n.velocity * scale)))
            result.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=new_vel,
                    absolute=n.absolute,
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _interpolate_value(
        start: float, end: float, t: float, curve: str = "linear"
    ) -> float:
        if curve == "linear":
            return start + (end - start) * t
        elif curve == "exponential":
            return start + (end - start) * (t ** 2)
        elif curve == "logarithmic":
            return start + (end - start) * (1 - (1 - t) ** 2)
        return start + (end - start) * t
