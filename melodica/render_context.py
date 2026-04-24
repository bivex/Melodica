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
render_context.py -- Cross-phrase state for connected rendering.

Layer: Domain
Rules:
  - Carries the ending state of one phrase into the start of the next.
  - Enables melodic continuity, dynamic shaping, and voice leading
    between phrases.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.types import ChordLabel, Scale


@dataclass
class RenderContext:
    """State passed between consecutive render() calls."""

    prev_pitch: int | None = None
    prev_velocity: int | None = None
    phrase_position: float = 0.0  # 0.0 to 1.0, where in the full arrangement
    prev_chord: ChordLabel | None = None
    prev_pitches: list[int] = field(default_factory=list)  # for polyphonic generators
    current_scale: Scale | None = None  # active key; set by MusicDirector on modulation

    def with_end_state(
        self,
        last_pitch: int | None = None,
        last_velocity: int | None = None,
        last_chord: ChordLabel | None = None,
        last_pitches: list[int] | None = None,
        current_scale: Scale | None = None,
        duration_beats: float = 0.0,
        total_duration: float = 0.0,
    ) -> RenderContext:
        """Return a new context with updated state for the next phrase."""
        # Update phrase position based on duration
        new_phrase_position = self.phrase_position
        if total_duration > 0 and duration_beats > 0:
            new_phrase_position = min(1.0, self.phrase_position + duration_beats / total_duration)
        return RenderContext(
            prev_pitch=last_pitch if last_pitch is not None else self.prev_pitch,
            prev_velocity=last_velocity if last_velocity is not None else self.prev_velocity,
            phrase_position=new_phrase_position,
            prev_chord=last_chord if last_chord is not None else self.prev_chord,
            prev_pitches=last_pitches if last_pitches is not None else self.prev_pitches,
            current_scale=current_scale if current_scale is not None else self.current_scale,
        )
