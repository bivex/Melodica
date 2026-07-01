"""Melody phrase & contour — register target computation.

Responsibilities:
  - Compute target register center based on phrase position
  - Climax pitch calculation (fixed offsets + auto range-based)
  - Cadence targeting for phrase endings
  - Non-linear easing curves for natural contour shapes
"""

from __future__ import annotations

import math

from melodica.easing import ease_in_out, ease_in, ease_out
from melodica.generators import GeneratorParams
from melodica.utils import nearest_pitch


PHRASE_CONTOUR_OPTIONS = frozenset({"arch", "rise_fall", "flat", "rise", "wave", "spiral",
                                    "descent", "zigzag"})
CLIMAX_OPTIONS = frozenset({"auto", "first_plus_maj3", "up_3rd", "up_5th", "up_octave", "none"})


class PhraseContour:
    """Manages phrase-level melodic contour and register targeting."""

    def __init__(
        self,
        phrase_contour: str = "arch",
        phrase_length: float = 0.0,
        climax: str = "auto",
        penultimate_step_above: bool = True,
    ) -> None:
        if phrase_contour not in PHRASE_CONTOUR_OPTIONS:
            raise ValueError(
                f"phrase_contour must be one of {sorted(PHRASE_CONTOUR_OPTIONS)}; got {phrase_contour!r}"
            )
        if climax not in CLIMAX_OPTIONS:
            raise ValueError(
                f"climax must be one of {sorted(CLIMAX_OPTIONS)}; got {climax!r}"
            )
        self.phrase_contour = phrase_contour
        self.phrase_length = max(0.0, phrase_length)
        self.climax = climax
        self.penultimate_step_above = penultimate_step_above

    def compute_climax(self, first_pitch: int, low: int, high: int) -> int:
        """Compute base climax pitch from first note and range."""
        if self.climax == "none":
            return first_pitch

        if self.climax == "auto":
            mid = (low + high) // 2
            return min(high, int(mid + (high - low) * 0.35))

        offset_map = {
            "first_plus_maj3": 4,
            "up_3rd": 4,
            "up_5th": 7,
            "up_octave": 12,
        }
        offset = offset_map.get(self.climax, 4)
        return min(high, first_pitch + offset)

    def register_target(
        self, phrase_pos: float, _global_progress: float, low: int, high: int, climax_pitch: int
    ) -> int:
        """Compute target register center at current phrase position using easing curves."""
        mid = (low + high) // 2

        if self.climax == "none" and self.phrase_contour == "flat":
            return mid

        if self.phrase_contour == "arch":
            return self._arch_curve(phrase_pos, mid, climax_pitch, low)
        elif self.phrase_contour == "rise_fall":
            return self._rise_fall_curve(phrase_pos, mid, climax_pitch, low)
        elif self.phrase_contour == "rise":
            return int(mid + (climax_pitch - mid) * ease_out(phrase_pos))
        elif self.phrase_contour == "wave":
            return self._wave_curve(phrase_pos, mid, climax_pitch, low)
        elif self.phrase_contour == "spiral":
            return self._spiral_curve(phrase_pos, mid, climax_pitch)
        elif self.phrase_contour == "descent":
            return self._descent_curve(phrase_pos, mid, low)
        elif self.phrase_contour == "zigzag":
            return self._zigzag_curve(phrase_pos, mid, climax_pitch, low)

        return mid  # "flat"

    def cadence_target(
        self, phrase_pos: float, chord, key, prev_pitch: int, low: int, high: int
    ) -> int | None:
        """Return a target pitch for the last 10% of a phrase, or None."""
        if phrase_pos < 0.90 or chord is None:
            return None
        # Resolve to chord root
        return nearest_pitch(chord.root, prev_pitch)

    # ------------------------------------------------------------------
    # Easing curves
    # ------------------------------------------------------------------

    def _arch_curve(self, pos: float, mid: int, climax: int, low: int) -> int:
        """Sine arch: smooth rise to ~60%, then smooth fall."""
        if pos < 0.6:
            frac = ease_in_out(pos / 0.6)
            return int(mid + (climax - mid) * frac)
        else:
            frac = ease_in_out((pos - 0.6) / 0.4)
            return int(climax - (climax - mid) * frac * 0.7)

    def _rise_fall_curve(self, pos: float, mid: int, climax: int, low: int) -> int:
        """Exponential rise + logarithmic fall."""
        if pos < 0.5:
            frac = ease_in(pos / 0.5)
            return int(mid + (climax - mid) * frac)
        else:
            frac = ease_out((pos - 0.5) / 0.5)
            return int(climax - (climax - low) * frac * 0.5)

    def _wave_curve(self, pos: float, mid: int, climax: int, low: int) -> int:
        """Two arches per phrase (half-wave at 0-0.5, full arch at 0.5-1.0)."""
        amplitude = (climax - mid) * 0.5
        return int(mid + amplitude * math.sin(pos * 2 * math.pi))

    def _spiral_curve(self, pos: float, mid: int, climax: int) -> int:
        """Ascending with periodic dips — grows toward climax over time."""
        base_ascent = (climax - mid) * ease_out(pos)
        dip = math.sin(pos * 4 * math.pi) * (climax - mid) * 0.15
        return int(mid + base_ascent + dip)

    def _descent_curve(self, pos: float, mid: int, low: int) -> int:
        """Mirror of 'rise': starts high, falls toward low end of range.
        Suited for weary, exhausted, or fading melodic lines."""
        # Begin near mid+range/4, fall toward low by phrase end.
        high_start = mid + (mid - low) // 2
        return int(high_start - (high_start - low) * ease_in_out(pos))

    def _zigzag_curve(self, pos: float, mid: int, climax: int, low: int) -> int:
        """Alternates up/down each quarter-phrase (4 peaks per phrase).
        Creates restless, uncertain melodic motion."""
        import math as _math
        # Triangle wave with 2 cycles: rises and falls quickly.
        cycle = (pos * 4.0) % 1.0  # 0..1 within each quarter
        if cycle < 0.5:
            frac = cycle * 2.0
        else:
            frac = (1.0 - cycle) * 2.0
        amplitude = (climax - low) * 0.4
        return int(mid - amplitude * 0.5 + amplitude * frac)



