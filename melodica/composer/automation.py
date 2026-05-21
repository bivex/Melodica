# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-21 12:45
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
composer/automation.py — AutomationCurve generators.

Static utility class to construct lists of CC event tuples (beat_position, cc_number, cc_value)
using linear, sine wave LFO, and exponential curves.
"""

from __future__ import annotations

import math

class AutomationCurve:
    """
    Utility class to generate standard MIDI Continuous Controller (CC) automation curves.
    All outputs are formatted as lists of (beat_position, cc_number, cc_value) tuples,
    sorted chronologically.
    """

    @staticmethod
    def linear(
        cc_num: int,
        start_val: int,
        end_val: int,
        start_beat: float,
        end_beat: float,
        steps: int = 20,
    ) -> list[tuple[float, int, int]]:
        """
        Generate a linear ramp from start_val to end_val.
        """
        if steps < 2:
            steps = 2
        events = []
        duration = end_beat - start_beat
        if duration <= 0:
            # Instant change
            return [
                (round(start_beat, 6), cc_num, max(0, min(127, start_val))),
                (round(end_beat, 6), cc_num, max(0, min(127, end_val))),
            ]

        for i in range(steps):
            t = start_beat + (duration * i / (steps - 1))
            val = start_val + (end_val - start_val) * i / (steps - 1)
            final_val = max(0, min(127, int(round(val))))
            events.append((round(t, 6), cc_num, final_val))
        return events

    @staticmethod
    def sine_lfo(
        cc_num: int,
        min_val: int,
        max_val: int,
        start_beat: float,
        end_beat: float,
        period: float,
        steps_per_period: int = 16,
    ) -> list[tuple[float, int, int]]:
        """
        Generate a sine wave LFO oscillating between min_val and max_val.
        period: cycle length in beats.
        """
        duration = end_beat - start_beat
        if duration <= 0 or period <= 0:
            return [(round(start_beat, 6), cc_num, max(0, min(127, (min_val + max_val) // 2)))]

        # Determine total steps based on duration and period
        num_cycles = duration / period
        total_steps = int(round(num_cycles * steps_per_period))
        if total_steps < 2:
            total_steps = 2

        events = []
        center = (min_val + max_val) / 2.0
        amplitude = (max_val - min_val) / 2.0

        for i in range(total_steps):
            t = start_beat + (duration * i / (total_steps - 1))
            # Calculate angle in radians
            phase = 2 * math.pi * (t - start_beat) / period
            val = center + amplitude * math.sin(phase)
            final_val = max(0, min(127, int(round(val))))
            events.append((round(t, 6), cc_num, final_val))
        return events

    @staticmethod
    def exponential(
        cc_num: int,
        start_val: int,
        end_val: int,
        start_beat: float,
        end_beat: float,
        exponent: float = 2.0,
        steps: int = 20,
    ) -> list[tuple[float, int, int]]:
        """
        Generate an exponential sweep from start_val to end_val.
        exponent > 1: slow start, fast end.
        exponent < 1: fast start, slow end.
        """
        if steps < 2:
            steps = 2
        events = []
        duration = end_beat - start_beat
        if duration <= 0:
            return [
                (round(start_beat, 6), cc_num, max(0, min(127, start_val))),
                (round(end_beat, 6), cc_num, max(0, min(127, end_val))),
            ]

        for i in range(steps):
            ratio = i / (steps - 1)
            t = start_beat + (duration * ratio)
            # exponential interpolation
            val = start_val + (end_val - start_val) * (ratio ** exponent)
            final_val = max(0, min(127, int(round(val))))
            events.append((round(t, 6), cc_num, final_val))
        return events
