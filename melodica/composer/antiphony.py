# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
composer/antiphony.py — Antiphonal section coordinator.
Coordinates call-and-response (antiphony) between instrument/track groups.
Splits tracks into two groups, alternates their active periods, and supports
overlap and echo delays.
"""

from __future__ import annotations

import copy
from typing import Any
from melodica.types import NoteInfo

DEFAULT_GROUPS: dict[str, str] = {
    # Strings
    "violin": "strings", "viola": "strings", "cello": "strings", "double_bass": "strings", 
    "contrabass": "strings", "strings": "strings", "orchestral_strings": "strings", "pizzicato": "strings",
    # Winds
    "flute": "winds", "oboe": "winds", "clarinet": "winds", "bassoon": "winds",
    "piccolo": "winds", "recorder": "winds", "woodwinds": "winds",
    # Brass
    "trumpet": "brass", "trombone": "brass", "horn": "brass", "french_horn": "brass",
    "tuba": "brass", "brass": "brass", "orchestral_brass": "brass",
    # Percussion
    "drums": "perc", "percussion": "perc", "tympani": "perc", "timpani": "perc",
    "cymbals": "perc", "snare": "perc", "kick": "perc",
}


class AntiphonySectionBuilder:
    """Coordinates call-and-response (antiphony) between groups of tracks."""

    def __init__(
        self,
        group_a: list[str] | None = None,
        group_b: list[str] | None = None,
        bars_a: float = 2.0,
        bars_b: float = 2.0,
        overlap_beats: float = 0.0,
        echo_delay_beats: float = 0.0,
        echo_velocity_factor: float = 0.5,
        echo_transpose: int = 12,
    ) -> None:
        self.group_a = group_a or ["strings"]
        self.group_b = group_b or ["winds", "brass"]
        self.bars_a = bars_a
        self.bars_b = bars_b
        self.overlap_beats = overlap_beats
        self.echo_delay_beats = echo_delay_beats
        self.echo_velocity_factor = echo_velocity_factor
        self.echo_transpose = echo_transpose

    def _resolve_track_group(self, track_name: str, instrument: str) -> str:
        """Resolve which group ('A', 'B', or 'none') a track belongs to."""
        name_lower = track_name.lower()
        inst_lower = instrument.lower()

        # Helper to check matching pattern in list
        def matches(patterns: list[str]) -> bool:
            for p in patterns:
                p_low = p.lower()
                if p_low in name_lower or p_low in inst_lower:
                    return True
                # Check mapping
                grp = DEFAULT_GROUPS.get(inst_lower)
                if grp and grp == p_low:
                    return True
            return False

        if matches(self.group_a):
            return "A"
        if matches(self.group_b):
            return "B"
        return "none"

    def process(
        self,
        tracks_notes: dict[str, list[NoteInfo]],
        tracks_instruments: dict[str, str],
        start_beat: float,
        duration_beats: float,
        time_sig_numerator: int = 4,
    ) -> dict[str, list[NoteInfo]]:
        """Filter and process notes within the time window to apply call-and-response."""
        end_beat = start_beat + duration_beats
        beats_per_bar = float(time_sig_numerator)

        beats_a = self.bars_a * beats_per_bar
        beats_b = self.bars_b * beats_per_bar
        cycle_beats = beats_a + beats_b
        if cycle_beats <= 0:
            return {k: list(v) for k, v in tracks_notes.items()}

        result: dict[str, list[NoteInfo]] = {}

        for name, notes in tracks_notes.items():
            inst = tracks_instruments.get(name, "piano")
            group = self._resolve_track_group(name, inst)

            if group == "none":
                result[name] = list(notes)
                continue

            # Separate notes inside vs outside the part window
            part_notes: list[NoteInfo] = []
            outside_notes: list[NoteInfo] = []
            for n in notes:
                if start_beat <= n.start < end_beat:
                    part_notes.append(n)
                else:
                    outside_notes.append(n)

            kept_notes: list[NoteInfo] = []
            echo_notes: list[NoteInfo] = []

            for n in part_notes:
                # Find position relative to start of the part
                rel_start = n.start - start_beat
                t_cycle = rel_start % cycle_beats

                if group == "A":
                    # Group A plays in the first phase
                    is_active = t_cycle < (beats_a + self.overlap_beats)
                else:
                    # Group B plays in the second phase
                    is_active = t_cycle >= (beats_a - self.overlap_beats)

                if is_active:
                    kept_notes.append(n)
                    # Generate echo copy if requested
                    if self.echo_delay_beats > 0:
                        echo_start = n.start + self.echo_delay_beats
                        # Check that the echo doesn't overshoot the part boundary
                        if echo_start < end_beat:
                            echo_n = copy.copy(n)
                            echo_n.start = echo_start
                            echo_n.pitch = max(0, min(127, n.pitch + self.echo_transpose))
                            echo_n.velocity = max(1, min(127, int(n.velocity * self.echo_velocity_factor)))
                            echo_notes.append(echo_n)

            # Combine outside notes, kept notes, and echoes
            combined = outside_notes + kept_notes + echo_notes
            result[name] = sorted(combined, key=lambda x: x.start)

        return result
