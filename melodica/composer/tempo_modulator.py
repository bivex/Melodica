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
        tempo_profile: str = "default",
    ) -> None:
        self.default_tempo = default_tempo
        self.ritardando_beats = ritardando_beats
        self.ritardando_factor = ritardando_factor
        self.use_tension_tempo = use_tension_tempo
        self.tension_tempo_range = tension_tempo_range
        self.tempo_profile = tempo_profile

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

            # Determine profile for this part
            profile = "default"
            if hasattr(part, "tempo_profile") and part.tempo_profile is not None:
                profile = part.tempo_profile
            else:
                profile = self.tempo_profile

            if profile == "default":
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
            else:
                # Custom profiles. We generate events every 0.5 beats.
                from melodica.types import BarGrid
                import random
                import math

                grid = BarGrid(ts[0], ts[1])
                bpb = grid.beats_per_bar
                step = 0.5
                total_steps = int(part_beats / step)

                for step_idx in range(total_steps):
                    beat_offset = step_idx * step
                    t_beat = current_beat + beat_offset
                    bar_in_part = beat_offset / bpb
                    pct = beat_offset / part_beats if part_beats > 0 else 0.0

                    if profile == "rubato":
                        # Rubato phrasing: 8-bar cycles
                        phrase_len_bars = 8.0
                        phrase_bar = bar_in_part % phrase_len_bars
                        if phrase_bar < 3.0:
                            t = phrase_bar / 3.0
                            bpm = (part_tempo - 3.0) + t * 7.0
                        elif phrase_bar < 6.0:
                            t = (phrase_bar - 3.0) / 3.0
                            bpm = (part_tempo + 4.0) - t * 4.0
                        else:
                            t = (phrase_bar - 6.0) / 2.0
                            bpm = part_tempo - t * 7.0
                        # Jitter
                        rng = random.Random(int(t_beat * 100))
                        jitter = rng.uniform(-0.3, 0.3)
                        bpm += jitter

                    elif profile == "agitato":
                        # Galloping fluctuation + macro build + ending ritardando
                        wave = 2.0 * math.sin(2 * math.pi * bar_in_part / 4.0)
                        if pct < 0.5:
                            macro = part_tempo
                        elif pct < 0.875:
                            t = (pct - 0.5) / (0.875 - 0.5)
                            macro = part_tempo + t * 8.0
                        else:
                            t = (pct - 0.875) / (1.0 - 0.875)
                            macro = (part_tempo + 8.0) + t * (-12.0)
                        bpm = macro + wave

                    elif profile == "industrial":
                        # Heavy mechanical steps with solid drops
                        if pct < 0.3:
                            bpm = part_tempo
                        elif pct < 0.6:
                            bpm = part_tempo - 2.0
                        elif pct < 0.85:
                            t = (pct - 0.6) / (0.85 - 0.6)
                            bpm = (part_tempo - 2.0) + t * 8.0
                        elif pct < 0.92:
                            bpm = part_tempo - 6.0
                        else:
                            t = (pct - 0.92) / (1.0 - 0.92)
                            bpm = (part_tempo - 6.0) - t * 6.0

                    elif profile == "chaotic":
                        # Unstable magical swings + micro-jitter
                        if pct < 0.95:
                            wave = 6.0 * math.sin(2 * math.pi * bar_in_part / 12.0)
                            bpm = part_tempo + wave
                        else:
                            wave_at_95 = 6.0 * math.sin(2 * math.pi * (0.95 * part_beats / bpb) / 12.0)
                            start_bpm = part_tempo + wave_at_95
                            t = (pct - 0.95) / (1.0 - 0.95)
                            bpm = start_bpm + t * ((part_tempo - 20.0) - start_bpm)
                        rng = random.Random(int(t_beat * 100))
                        jitter = rng.uniform(-0.8, 0.8)
                        bpm += jitter

                    elif profile == "combat":
                        # Sudden battle shifts: build, active fight fluctuation, breathers, peak climax
                        if pct < 0.22:
                            bpm = part_tempo - 2.0
                        elif pct < 0.55:
                            wave = 4.0 * math.sin(2 * math.pi * bar_in_part / 2.0)
                            bpm = part_tempo + 2.0 + wave
                        elif pct < 0.66:
                            bpm = part_tempo - 10.0
                        elif pct < 0.94:
                            t = (pct - 0.66) / (0.94 - 0.66)
                            bpm = (part_tempo - 2.0) + t * 12.0
                        else:
                            t = (pct - 0.94) / (1.0 - 0.94)
                            bpm = (part_tempo + 10.0) - t * 14.0

                    elif profile == "madness":
                        # Cyclic madness in 16-bar cycles
                        cycle_len_bars = 16.0
                        cycle_bar = bar_in_part % cycle_len_bars
                        if cycle_bar < 8.0:
                            t = cycle_bar / 8.0
                            bpm = (part_tempo - 4.0) + t * 10.0
                        elif cycle_bar < 12.0:
                            t = (cycle_bar - 8.0) / 4.0
                            bpm = 68.0 + t * 8.0
                        else:
                            t = (cycle_bar - 12.0) / 4.0
                            bpm = 76.0 - t * 20.0

                    elif profile == "requiem":
                        # Solemn breathing every 8 bars with a long fading ritardando at the outro
                        if pct < 0.75:
                            phrase_bar = bar_in_part % 8.0
                            if phrase_bar < 6.0:
                                bpm = part_tempo
                            else:
                                t = (phrase_bar - 6.0) / 2.0
                                bpm = part_tempo - t * 6.0
                        else:
                            t = (pct - 0.75) / (1.0 - 0.75)
                            bpm = part_tempo - t * 16.0

                    else:
                        bpm = part_tempo

                    events.append((t_beat, round(bpm, 2)))

            current_beat = part_end

        # Ensure events are sorted and remove duplicates on the same beat (keep last)
        events.sort(key=lambda x: x[0])
        unique_events: dict[float, float] = {}
        for beat, bpm in events:
            unique_events[beat] = bpm

        return sorted(unique_events.items())
