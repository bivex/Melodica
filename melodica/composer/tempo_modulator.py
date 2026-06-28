# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
composer/tempo_modulator.py — Tempo Modulation Generator.
Generates dynamic set_tempo events for MIDI export, supporting ritardando
transitions at part boundaries and accelerando/decelerando along TensionCurve profiles.
"""

from __future__ import annotations

from melodica.types import Scale
from melodica.idea_tool import IdeaPart
from melodica.composer.tension_curve import TensionCurve


class TempoModulator:
    """Generates dynamic tempo events (ritardando, accelerando) across structural parts."""

    def __init__(
        self,
        default_tempo: float = 120.0,
        ritardando_beats: float = 4.0,
        ritardando_factor: float = 0.85,
        use_tension_tempo: bool = False,
        tension_tempo_range: float = 15.0,  # max BPM adjustment based on tension
    ) -> None:
        self.default_tempo = default_tempo
        self.ritardando_beats = ritardando_beats
        self.ritardando_factor = ritardando_factor
        self.use_tension_tempo = use_tension_tempo
        self.tension_tempo_range = tension_tempo_range

    def _get_tension_value(self, beat: float, tension_curve: TensionCurve | None) -> float:
        """Get tension value from curve at specific beat."""
        if tension_curve is None:
            return 0.5
        points = tension_curve.generate()
        if not points:
            return 0.5
        # Find nearest point
        nearest = min(points, key=lambda p: abs(p.beat - beat))
        return nearest.tension

    def generate_events(
        self,
        parts: list[IdeaPart],
        tension_curve: TensionCurve | None = None,
    ) -> list[tuple[float, float]]:
        """
        Generate a list of (beat_position, tempo_bpm) events.
        """
        events: list[tuple[float, float]] = []
        if not parts:
            return events

        current_beat = 0.0

        # Initial tempo
        initial_tempo = parts[0].tempo if parts[0].tempo is not None else self.default_tempo
        events.append((0.0, float(initial_tempo)))

        for idx, part in enumerate(parts):
            ts = part.time_signature or (4, 4)
            part_beats = part.bars * ts[0]
            part_end = current_beat + part_beats
            part_tempo = part.tempo if part.tempo is not None else self.default_tempo

            # 1. Apply baseline tempo change at the start of the part
            if idx > 0 and part_tempo != (parts[idx - 1].tempo or self.default_tempo):
                events.append((current_beat, float(part_tempo)))

            # 2. Tension-based tempo variation (accelerando / decelerando)
            if self.use_tension_tempo and tension_curve is not None:
                # Sample every 2 beats
                step = 2.0
                t_beat = current_beat
                # Do not apply tension tempo adjustment in the ritardando zone
                adjustment_end = part_end - self.ritardando_beats if self.ritardando_beats > 0 else part_end
                while t_beat < adjustment_end:
                    tension = self._get_tension_value(t_beat, tension_curve)
                    # Higher tension -> faster tempo (accelerando)
                    adjusted_tempo = part_tempo + (tension - 0.5) * self.tension_tempo_range
                    events.append((t_beat, float(adjusted_tempo)))
                    t_beat += step

            # 3. Ritardando at the end of the part
            if self.ritardando_beats > 0 and part_beats >= self.ritardando_beats:
                rit_start = part_end - self.ritardando_beats
                # Smoothly decelerate across 4 steps
                steps = 4
                step_duration = self.ritardando_beats / steps
                for s in range(1, steps + 1):
                    t = rit_start + (s - 1) * step_duration
                    factor = 1.0 - (1.0 - self.ritardando_factor) * (s / steps)
                    events.append((t, float(part_tempo * factor)))

            current_beat = part_end

        # Ensure events are sorted and remove duplicates on the same beat (keep last)
        events.sort(key=lambda x: x[0])
        unique_events: dict[float, float] = {}
        for beat, bpm in events:
            unique_events[beat] = bpm

        return sorted(unique_events.items())
