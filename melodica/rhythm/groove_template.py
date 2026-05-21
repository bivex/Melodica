# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
rhythm/groove_template.py — DAW-style groove templates.

Provides per-note timing and velocity offsets that shift events
away from the grid for humanized, style-specific feel.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.rhythm import RhythmEvent


@dataclass(frozen=True)
class GrooveSlot:
    """A single timing/velocity offset at a fractional beat position."""

    position: float       # 0.0–1.0 fractional position within a beat
    timing_offset: float  # seconds (positive = late)
    velocity_factor: float


@dataclass
class GrooveTemplate:
    """Named groove that shifts rhythm events off the grid."""

    name: str
    beats_per_bar: int = 4
    slots: list[GrooveSlot] = field(default_factory=list)

    def apply(self, events: list[RhythmEvent]) -> list[RhythmEvent]:
        """Apply groove offsets to a list of rhythm events."""
        if not self.slots:
            return list(events)

        result: list[RhythmEvent] = []
        for ev in events:
            frac = ev.onset % 1.0
            applied = False
            for slot in self.slots:
                if abs(frac - slot.position) < 0.05:
                    result.append(RhythmEvent(
                        onset=round(ev.onset + slot.timing_offset * 0.01, 6),
                        duration=ev.duration,
                        velocity_factor=ev.velocity_factor * slot.velocity_factor,
                    ))
                    applied = True
                    break
            if not applied:
                result.append(ev)
        return result


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

STRAIGHT = GrooveTemplate(name="straight")

SWING_60 = GrooveTemplate(
    name="swing_60",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.5, timing_offset=3.5, velocity_factor=0.88),
    ],
)

HARD_SWING = GrooveTemplate(
    name="hard_swing",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.5, timing_offset=7.0, velocity_factor=0.82),
    ],
)

SHUFFLE = GrooveTemplate(
    name="shuffle",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.5, velocity_factor=1.0),
        GrooveSlot(position=0.33, timing_offset=5.0, velocity_factor=0.85),
        GrooveSlot(position=0.66, timing_offset=2.0, velocity_factor=0.90),
    ],
)

LAID_BACK = GrooveTemplate(
    name="laid_back",
    slots=[
        GrooveSlot(position=0.0, timing_offset=4.0, velocity_factor=0.95),
        GrooveSlot(position=0.25, timing_offset=3.0, velocity_factor=0.88),
        GrooveSlot(position=0.5, timing_offset=5.0, velocity_factor=0.82),
        GrooveSlot(position=0.75, timing_offset=3.5, velocity_factor=0.86),
    ],
)

GROOVE_PRESETS: dict[str, GrooveTemplate] = {
    "straight": STRAIGHT,
    "swing_60": SWING_60,
    "hard_swing": HARD_SWING,
    "shuffle": SHUFFLE,
    "laid_back": LAID_BACK,
}
