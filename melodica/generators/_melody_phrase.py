"""Melody phrase & contour — register target computation.

Responsibilities:
  - Compute target register center based on phrase position (arch, rise_fall, rise, flat)
  - Climax pitch calculation
"""

from __future__ import annotations

from melodica.generators import GeneratorParams


PHRASE_CONTOUR_OPTIONS = frozenset({"arch", "rise_fall", "flat", "rise"})
CLIMAX_OPTIONS = frozenset({"first_plus_maj3", "up_3rd", "up_5th", "up_octave", "none"})


class PhraseContour:
    """Manages phrase-level melodic contour and register targeting."""

    def __init__(
        self,
        phrase_contour: str = "arch",
        phrase_length: float = 0.0,
        climax: str = "first_plus_maj3",
        penultimate_step_above: bool = True,
    ) -> None:
        if phrase_contour not in PHRASE_CONTOUR_OPTIONS:
            raise ValueError(
                f"phrase_contour must be one of {sorted(PHRASE_CONTOUR_OPTIONS)}; got {phrase_contour!r}"
            )
        self.phrase_contour = phrase_contour
        self.phrase_length = max(0.0, phrase_length)
        self.climax = climax
        self.penultimate_step_above = penultimate_step_above

    def compute_climax(self, first_pitch: int, low: int, high: int) -> int:
        """Compute base climax pitch from first note."""
        if self.climax == "none":
            return first_pitch

        offset_map = {
            "first_plus_maj3": 4,
            "up_3rd": 4,
            "up_5th": 7,
            "up_octave": 12,
        }
        offset = offset_map.get(self.climax, 4)
        return min(high, first_pitch + offset)

    def register_target(
        self, phrase_pos: float, global_progress: float, low: int, high: int, climax_pitch: int
    ) -> int:
        """Compute target register center at current phrase position."""
        mid = (low + high) // 2

        if self.climax == "none" and self.phrase_contour == "flat":
            return mid

        if self.phrase_contour == "arch":
            # Rise to 60%, peak, fall to 100%
            if phrase_pos < 0.6:
                frac = phrase_pos / 0.6
                return int(mid + (climax_pitch - mid) * frac)
            else:
                frac = (phrase_pos - 0.6) / 0.4
                return int(climax_pitch - (climax_pitch - mid) * frac * 0.7)

        elif self.phrase_contour == "rise_fall":
            # Symmetric: rise first half, fall second half
            if phrase_pos < 0.5:
                frac = phrase_pos / 0.5
                return int(mid + (climax_pitch - mid) * frac)
            else:
                frac = (phrase_pos - 0.5) / 0.5
                return int(climax_pitch - (climax_pitch - low) * frac * 0.5)

        elif self.phrase_contour == "rise":
            # Only rise, no fall
            return int(mid + (climax_pitch - mid) * phrase_pos)

        return mid  # "flat"
