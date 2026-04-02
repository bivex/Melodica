# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import math

from melodica.types import NoteInfo

@dataclass
class AutomationPoint:
    time: float # relative to phrase onset
    value: int # 0-127

@dataclass
class ExpressionCurve:
    """
    A curve for MIDI CC data or special parameters (Velocity, Pitch Bend).
    Supports CC number or special strings like 'velocity', 'pitch_bend', 'sustain', 'pan', 'volume'.
    """

    target: str | int  # CC number or 'velocity', 'pitch_bend', 'sustain', 'pan', 'volume'
    points: List[AutomationPoint] = field(default_factory=list)

    @classmethod
    def linear(cls, target: str | int, start_val: int, end_val: int, duration: float, steps: int = 4):
        """Creates a smooth linear ramp."""
        pts = []
        for i in range(steps + 1):
            t = (i / steps) * duration
            v = int(start_val + (end_val - start_val) * (i / steps))
            pts.append(AutomationPoint(t, v))
        return cls(target, pts)

    @classmethod
    def surge(cls, target: str | int, peak_val: int, duration: float):
        """Creates a triangle shape (0 -> peak -> 0)."""
        mid = duration / 2
        return cls(target, [
            AutomationPoint(0.0, 0),
            AutomationPoint(mid, peak_val),
            AutomationPoint(duration, 0)
        ])

    @classmethod
    def sinusoidal(cls, target: str | int, start_val: int, end_val: int, duration: float, freq: float = 1.0):
        """Creates a sine wave for vibrato/panning."""
        pts = []
        steps = 20
        for i in range(steps + 1):
            t = (i / steps) * duration
            v = int(start_val + (end_val - start_val) * (0.5 + 0.5 * math.sin(2 * math.pi * freq * t)))
            pts.append(AutomationPoint(t, v))
        return cls(target, pts)

def apply_automation(notes: list[NoteInfo], curves: List[ExpressionCurve], track_volume: int = 100):
    """
    Embed expression data into NoteInfo objects and apply velocity modifications.

    curve.target can be:
      - An int (MIDI CC number): e.g. 11 for Expression, 1 for Modulation
      - "velocity": scales note velocity
      - "pitch_bend": writes pitchwheel value (-8192 to +8191)
      - A CC name string: "modulation"(1), "volume"(7), "pan"(10),
        "expression"(11), "sustain"(64), "hold"(64)
    """
    # Name → CC number lookup (convenience only; prefer int directly)
    _CC_NAMES = {
        "modulation": 1, "volume": 7, "pan": 10,
        "expression": 11, "sustain": 64, "hold": 64,
    }

    for note in notes:
        for curve in curves:
            val = _interpolate_curve(curve.points, note.start)
            if val is None:
                continue

            target = curve.target

            if isinstance(target, int):
                # Direct CC number — the primary API
                note.expression[target] = val
            elif isinstance(target, str):
                t = target.lower()
                if t == "velocity":
                    note.velocity = int(note.velocity * (val / 127.0))
                elif t == "pitch_bend":
                    note.expression["pitch_bend"] = int((val / 127.0) * 16383 - 8192)
                elif t in _CC_NAMES:
                    note.expression[_CC_NAMES[t]] = val
                # Unknown string targets are silently ignored

    return notes

def _interpolate_curve(points: List[AutomationPoint], time: float) -> Optional[int]:
    if not points: return None
    if time <= points[0].time: return points[0].value
    if time >= points[-1].time: return points[-1].value
    
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        if p1.time <= time <= p2.time:
            ratio = (time - p1.time) / (p2.time - p1.time)
            return int(p1.value + (p2.value - p1.value) * ratio)
    return None
