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
rhythm/__init__.py — Rhythm Engine Core.

Layer: Application / Domain

This module isolates rhythm generation from pitch generation. Rhythm generators
produce sequences of `RhythmEvent` (onset and duration) without knowing anything
about chords or scales.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass


@dataclass(frozen=True)
class RhythmEvent:
    """An abstract timing event independent of pitch."""

    onset: float  # Beat position relative to phrase start (0.0 = start)
    duration: float  # Length in beats
    velocity_factor: float = 1.0  # 0.0-1.0 modulation for velocity (1.0 = normal)


class RhythmGenerator(typing.Protocol):
    """
    Protocol for all rhythm generators.
    Takes a total duration in beats and returns a list of rhythm events.
    """

    def generate(self, duration_beats: float) -> list[RhythmEvent]: ...


class RhythmCoordinator:
    """
    Shares a single rhythm pattern across multiple tracks.

    Generates rhythm events once and distributes cached copies to
    all registered tracks, ensuring bass, drums, etc. hit at the same time.

    Usage:
        coord = RhythmCoordinator(EuclideanRhythmGenerator(hits_per_bar=8))
        coord.register("Bass")
        coord.register("Drums")
        # Later, in arrange():
        bass_events = coord.get_rhythm("Bass", duration)
        drum_events = coord.get_rhythm("Drums", duration)
    """

    def __init__(self, source: RhythmGenerator) -> None:
        self._source = source
        self._tracks: list[str] = []
        self._cache: dict[float, list[RhythmEvent]] = {}

    def register(self, track_name: str) -> None:
        if track_name not in self._tracks:
            self._tracks.append(track_name)

    @property
    def tracks(self) -> list[str]:
        return list(self._tracks)

    def get_rhythm(self, track_name: str, duration_beats: float) -> list[RhythmEvent]:
        """Return the shared rhythm for a track. Cached by duration."""
        key = round(duration_beats, 2)
        if key not in self._cache:
            self._cache[key] = self._source.generate(duration_beats)
        return list(self._cache[key])

    def clear_cache(self) -> None:
        self._cache.clear()


from melodica.rhythm.euclidean import EuclideanRhythmGenerator
from melodica.rhythm.probabilistic import ProbabilisticRhythmGenerator
from melodica.rhythm.subdivision import SubdivisionGenerator
from melodica.rhythm.schillinger import SchillingerGenerator
from melodica.rhythm.motif import MotifRhythmGenerator
from melodica.rhythm.library import StaticRhythmGenerator, RHYTHM_LIBRARY, get_rhythm
from melodica.rhythm.rhythm_lab import RhythmLab
from melodica.rhythm.polyrhythm import PolyrhythmGenerator
from melodica.rhythm.smooth import SmoothRhythmGenerator
from melodica.rhythm.bass_rhythm import BassRhythmGenerator
from melodica.rhythm.markov_rhythm import MarkovRhythmGenerator

__all__ = [
    "RhythmEvent",
    "RhythmGenerator",
    "RhythmCoordinator",
    "EuclideanRhythmGenerator",
    "ProbabilisticRhythmGenerator",
    "SubdivisionGenerator",
    "SchillingerGenerator",
    "MotifRhythmGenerator",
    "StaticRhythmGenerator",
    "RHYTHM_LIBRARY",
    "get_rhythm",
    "RhythmLab",
    "PolyrhythmGenerator",
    "SmoothRhythmGenerator",
    "BassRhythmGenerator",
    "MarkovRhythmGenerator",
]
