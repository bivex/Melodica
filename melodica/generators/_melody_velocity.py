"""Melody velocity & dynamics — accent patterns and phrase contour.

Responsibilities:
  - Apply accent patterns (strong_weak, syncopated)
  - Apply phrase contour dynamics (crescendo/diminuendo to climax)
  - Scale by continuous beat strength from GrooveProfile
  - Add humanized micro-variation with accent bursts and ghost notes
"""

from __future__ import annotations

import random

from melodica.rhythm import RhythmEvent


ACCENT_PATTERN_OPTIONS = frozenset({"natural", "strong_weak", "syncopated"})


def _velocity_from_density(density: float) -> int:
    """Base velocity from overall density (0.0-1.0)."""
    return int(50 + density * 50)


class VelocityProcessor:
    """Computes note velocities with accent patterns and phrase contour."""

    def __init__(
        self,
        accent_pattern: str = "natural",
        phrase_contour: str = "arch",
        phrase_length: float = 0.0,
    ) -> None:
        if accent_pattern not in ACCENT_PATTERN_OPTIONS:
            raise ValueError(
                f"accent_pattern must be one of {sorted(ACCENT_PATTERN_OPTIONS)}; got {accent_pattern!r}"
            )
        self.accent_pattern = accent_pattern
        self.phrase_contour = phrase_contour
        self.phrase_length = phrase_length

    def apply(
        self,
        base_vel: int,
        event: RhythmEvent,
        phrase_pos: float,
        global_progress: float,
        beat_strength: float = 1.0,
    ) -> int:
        """Apply accents and contour to base velocity."""
        vel = base_vel * event.velocity_factor

        # Beat strength scaling (from GrooveProfile)
        vel *= 0.7 + 0.3 * beat_strength

        # Accent pattern (supplementary to beat strength)
        is_downbeat = event.onset % 1.0 < 0.1
        is_offbeat = event.onset % 0.5 >= 0.1

        if self.accent_pattern == "strong_weak":
            if is_downbeat:
                vel *= 1.10
            elif is_offbeat:
                vel *= 0.88
        elif self.accent_pattern == "syncopated":
            if is_offbeat:
                vel *= 1.08
            elif is_downbeat:
                vel *= 0.93

        # Phrase contour dynamics
        if self.phrase_contour != "flat" and self.phrase_length > 0:
            if phrase_pos < 0.6:
                contour_factor = 0.85 + 0.15 * (phrase_pos / 0.6)
            else:
                contour_factor = 1.0 - 0.25 * ((phrase_pos - 0.6) / 0.4)
            vel *= contour_factor

        # Humanized micro-variation
        # Accent burst: occasional emphasis on random notes
        if random.random() < 0.05:
            vel *= 1.15
        # Ghost note: occasional very quiet note on weak beats
        elif beat_strength < 0.4 and random.random() < 0.03:
            vel *= 0.6
        else:
            vel *= random.uniform(0.92, 1.08)

        return max(1, min(127, int(vel)))
