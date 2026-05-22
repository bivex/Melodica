# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/texture_manager.py — Orchestrates gradual texture evolution over time.

Maps beats to texture levels, handles crossfades between levels (instruments
entering/exiting), and provides per-instrument density curves for smooth
orchestral swells.

Utility class used by OrchestralScoreGenerator — NOT a PhraseGenerator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Texture level ordering (low to high)
# ---------------------------------------------------------------------------

_TEXTURE_ORDER = ["thin", "solo", "chamber", "small", "full"]


def _texture_rank(texture: str) -> int:
    try:
        return _TEXTURE_ORDER.index(texture)
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Instrument membership per texture level
# ---------------------------------------------------------------------------

_TEXTURE_INSTRUMENTS: dict[str, dict[str, str]] = {
    "thin": {
        "violin": "melody",
        "cello": "bass",
    },
    "solo": {
        "violin": "melody",
    },
    "chamber": {
        "violin": "melody",
        "viola": "harmony",
        "cello": "bass",
    },
    "small": {
        "violin": "melody",
        "viola": "harmony",
        "cello": "bass",
        "contrabass": "bass",
        "flute": "countermelody",
        "harp": "pad",
    },
    "full": {
        "violin": "melody",
        "viola": "harmony",
        "cello": "bass",
        "contrabass": "bass",
        "flute": "countermelody",
        "oboe": "countermelody",
        "clarinet": "harmony",
        "bassoon": "bass",
        "french_horn": "pad",
        "trumpet": "melody",
        "trombone": "harmony",
        "choir_aahs": "pad",
        "harp": "pad",
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TextureControlPoint:
    beat: float
    texture: str  # "thin", "solo", "chamber", "small", "full"


@dataclass
class InstrumentState:
    active: bool
    role: str
    density_scale: float  # 0.0–1.0 for gradual entry/exit


# ---------------------------------------------------------------------------
# TextureManager
# ---------------------------------------------------------------------------

class TextureManager:

    def __init__(
        self,
        control_points: list[TextureControlPoint] | None = None,
        crossfade_beats: float = 4.0,
    ) -> None:
        self._points: list[TextureControlPoint] = sorted(
            control_points or [],
            key=lambda p: p.beat,
        )
        self.crossfade_beats = crossfade_beats

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def texture_at(self, beat: float) -> str:
        """Return the interpolated texture level at *beat*."""
        if not self._points:
            return "chamber"

        # Before the first control point — hold its texture.
        if beat <= self._points[0].beat:
            return self._points[0].texture

        # After the last control point — hold its texture.
        if beat >= self._points[-1].beat:
            return self._points[-1].texture

        # Find the surrounding control points.
        prev = self._points[0]
        for i in range(1, len(self._points)):
            nxt = self._points[i]
            if prev.beat <= beat <= nxt.beat:
                break
            prev = nxt
        else:
            return prev.texture

        # Step interpolation — hard cut at the later control point.
        mid = (prev.beat + nxt.beat) / 2
        return nxt.texture if beat >= mid else prev.texture

    def instruments_at(self, beat: float) -> dict[str, InstrumentState]:
        """Return per-instrument state at *beat*, including crossfade densities."""
        texture = self.texture_at(beat)
        current_set = _TEXTURE_INSTRUMENTS.get(texture, {})

        # Determine previous and next textures for crossfade calculation.
        prev_texture = texture
        next_texture = texture
        in_crossfade = False
        progress = 1.0

        if self._points:
            prev_cp = self._points[0]
            for i in range(1, len(self._points)):
                nxt_cp = self._points[i]
                if prev_cp.beat <= beat <= nxt_cp.beat:
                    # We're between two control points — check for crossfade.
                    prev_texture = prev_cp.texture
                    next_texture = nxt_cp.texture
                    span = nxt_cp.beat - prev_cp.beat
                    if span > 0:
                        progress = (beat - prev_cp.beat) / span
                    if prev_texture != next_texture:
                        in_crossfade = True
                    break
                prev_cp = nxt_cp

        prev_set = _TEXTURE_INSTRUMENTS.get(prev_texture, {})
        next_set = _TEXTURE_INSTRUMENTS.get(next_texture, {})

        result: dict[str, InstrumentState] = {}

        # All instruments that appear in either texture.
        all_instruments = set(prev_set) | set(next_set)

        for inst in all_instruments:
            in_prev = inst in prev_set
            in_next = inst in next_set

            if in_crossfade:
                if in_prev and in_next:
                    # Sustained instrument — always full density.
                    result[inst] = InstrumentState(
                        active=True,
                        role=next_set[inst],
                        density_scale=1.0,
                    )
                elif in_next and not in_prev:
                    # Entering — ramp 0→1.
                    result[inst] = InstrumentState(
                        active=True,
                        role=next_set[inst],
                        density_scale=progress,
                    )
                elif in_prev and not in_next:
                    # Exiting — ramp 1→0.
                    result[inst] = InstrumentState(
                        active=progress > 0.0,
                        role=prev_set[inst],
                        density_scale=1.0 - progress,
                    )
            else:
                if in_next:
                    result[inst] = InstrumentState(
                        active=True,
                        role=next_set.get(inst, current_set.get(inst, "")),
                        density_scale=1.0,
                    )

        return result

    def add_control_point(self, beat: float, texture: str) -> None:
        """Append a control point and re-sort the list."""
        self._points.append(TextureControlPoint(beat=beat, texture=texture))
        self._points.sort(key=lambda p: p.beat)

    def build_curve(
        self,
        duration_beats: float,
        start_texture: str = "chamber",
        end_texture: str = "full",
        shape: str = "linear",
    ) -> None:
        """Auto-generate control points for a smooth texture evolution."""
        start_rank = _texture_rank(start_texture)
        end_rank = _texture_rank(end_texture)

        if start_rank == end_rank:
            self.add_control_point(0.0, start_texture)
            return

        if shape == "step":
            self.add_control_point(0.0, start_texture)
            self.add_control_point(duration_beats, end_texture)
            return

        step = 1 if end_rank > start_rank else -1
        ranks = list(range(start_rank, end_rank + step, step))
        n = len(ranks)

        if n == 0:
            return

        for i, rank in enumerate(ranks):
            if shape == "exponential":
                # Stays at lower texture longer, then accelerates.
                t = (i / max(n - 1, 1)) ** 2
            else:
                t = i / max(n - 1, 1)

            beat = t * duration_beats
            self.add_control_point(beat, _TEXTURE_ORDER[rank])

    @staticmethod
    def from_sections(
        sections: list[tuple[str, float, float]],
        section_textures: dict[str, str] | None = None,
        crossfade_beats: float = 4.0,
    ) -> TextureManager:
        """Factory: create from a section list (name, start_beat, duration_beats)."""
        section_textures = section_textures or {}
        default_textures = {
            "intro": "thin",
            "verse": "chamber",
            "chorus": "full",
            "bridge": "small",
            "outro": "chamber",
            "interlude": "solo",
        }

        points: list[TextureControlPoint] = []
        for name, start, duration in sections:
            texture = (
                section_textures.get(name)
                or default_textures.get(name, "chamber")
            )
            points.append(TextureControlPoint(beat=start, texture=texture))

        return TextureManager(
            control_points=points,
            crossfade_beats=crossfade_beats,
        )
