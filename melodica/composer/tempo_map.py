"""TempoMap — tempo changes within a track (ritardando, accelerando, fermata, rubato).

Builder pattern.  Output is ``list[tuple[float, float]]`` (beat, bpm) directly
compatible with ``export_multitrack_midi(tempo_events=...)``.
"""

from __future__ import annotations

import math


class TempoMap:
    """Builder for tempo events with interpolation support."""

    def __init__(self, default_bpm: float = 120.0) -> None:
        self._events: list[tuple[float, float]] = [(0.0, default_bpm)]

    # ------------------------------------------------------------------
    # Mutations (return self for chaining)
    # ------------------------------------------------------------------

    def set_bpm(self, beat: float, bpm: float) -> TempoMap:
        self._events.append((beat, bpm))
        return self

    def ritardando(
        self,
        start_bpm: float,
        end_bpm: float,
        start_beat: float,
        end_beat: float,
        curve: str = "linear",
        steps: int = 16,
    ) -> TempoMap:
        span = end_beat - start_beat
        for i in range(steps + 1):
            t = i / steps
            bpm = _interpolate(start_bpm, end_bpm, t, curve)
            self._events.append((round(start_beat + span * t, 6), bpm))
        return self

    def accelerando(
        self,
        start_bpm: float,
        end_bpm: float,
        start_beat: float,
        end_beat: float,
        curve: str = "linear",
        steps: int = 16,
    ) -> TempoMap:
        return self.ritardando(start_bpm, end_bpm, start_beat, end_beat, curve, steps)

    def fermata(
        self,
        beat: float,
        hold_bpm: float = 20.0,
        duration_beats: float = 2.0,
        resume_bpm: float | None = None,
    ) -> TempoMap:
        resume = resume_bpm if resume_bpm is not None else self._last_bpm_before(beat)
        self._events.append((beat, hold_bpm))
        self._events.append((round(beat + duration_beats, 6), resume))
        return self

    def rubato(self, points: list[tuple[float, float]]) -> TempoMap:
        for beat, bpm in points:
            self._events.append((beat, bpm))
        return self

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def build(self) -> list[tuple[float, float]]:
        """Sorted, deduplicated tempo events."""
        seen: dict[float, float] = {}
        for beat, bpm in self._events:
            seen[beat] = bpm  # last write wins for duplicate beats
        return sorted(seen.items(), key=lambda x: x[0])

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _last_bpm_before(self, beat: float) -> float:
        before = [(b, bpm) for b, bpm in self._events if b <= beat]
        return before[-1][1] if before else self._events[0][1]


# ------------------------------------------------------------------
# Module-level interpolation
# ------------------------------------------------------------------

def _interpolate(start: float, end: float, t: float, curve: str = "linear") -> float:
    if curve == "linear":
        return start + (end - start) * t
    elif curve == "exponential":
        ratio = end / start if start != 0 else 1.0
        return start * (ratio ** t)
    elif curve == "sine":
        return start + (end - start) * (0.5 - 0.5 * math.cos(math.pi * t))
    return start + (end - start) * t
