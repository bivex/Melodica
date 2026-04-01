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
    ) -> RenderContext:
        """Return a new context with updated state for the next phrase."""
        return RenderContext(
            prev_pitch=last_pitch if last_pitch is not None else self.prev_pitch,
            prev_velocity=last_velocity if last_velocity is not None else self.prev_velocity,
            phrase_position=self.phrase_position,
            prev_chord=last_chord if last_chord is not None else self.prev_chord,
            prev_pitches=last_pitches if last_pitches is not None else self.prev_pitches,
            current_scale=current_scale if current_scale is not None else self.current_scale,
        )
