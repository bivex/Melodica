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

"""
rhythm/bass_rhythm.py — BassRhythmGenerator.

Rhythm patterns designed for bass lines.
Root emphasis on beat 1, syncopation on beat 3.
"""

from __future__ import annotations

from dataclasses import dataclass

from melodica.rhythm import RhythmEvent


BASS_PATTERNS: dict[str, list[tuple[float, float, float]]] = {
    # (beat_offset, duration, velocity_factor)
    "straight": [
        (0.0, 0.95, 1.1),
        (1.0, 0.95, 0.9),
        (2.0, 0.95, 1.0),
        (3.0, 0.95, 0.9),
    ],
    "syncopated": [
        (0.0, 0.95, 1.1),
        (1.0, 0.45, 0.8),
        (1.5, 0.45, 0.7),
        (2.0, 0.95, 1.0),
        (3.0, 0.45, 0.8),
        (3.5, 0.45, 0.7),
    ],
    "walking": [
        (0.0, 0.95, 1.0),
        (1.0, 0.95, 0.95),
        (2.0, 0.95, 0.9),
        (3.0, 0.95, 0.95),
    ],
    "reggae": [
        (0.5, 0.45, 1.0),
        (1.5, 0.45, 0.9),
        (2.5, 0.45, 1.0),
        (3.5, 0.45, 0.9),
    ],
    "dotted": [
        (0.0, 1.45, 1.1),
        (1.5, 0.45, 0.8),
        (2.0, 1.45, 1.0),
        (3.5, 0.45, 0.8),
    ],
}


@dataclass
class BassRhythmGenerator:
    """
    Bass-specific rhythm patterns.

    pattern_name: named bass rhythm pattern
    """

    pattern_name: str = "syncopated"

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        pattern = BASS_PATTERNS.get(self.pattern_name, BASS_PATTERNS["straight"])
        events: list[RhythmEvent] = []
        t = 0.0
        while t < duration_beats:
            for offset, dur, vel in pattern:
                onset = t + offset
                if onset < duration_beats:
                    actual_dur = min(dur, duration_beats - onset)
                    events.append(
                        RhythmEvent(
                            onset=round(onset, 6),
                            duration=round(actual_dur, 6),
                            velocity_factor=vel,
                        )
                    )
            t += 4.0
        return events
