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


@dataclass(frozen=True)
class Tuplet:
    """Represents a tuplet grouping (e.g. triplet = 3 in the time of 2).

    Attributes:
        count: Number of notes in the tuplet (e.g. 3 for triplet)
        in_place_of: Number of notes being replaced (e.g. 2 for triplet)
        unit: Base note duration in beats (1.0 = quarter note)
    """

    count: int = 3
    in_place_of: int = 2
    unit: float = 1.0

    @property
    def ratio(self) -> float:
        """Compression ratio: in_place_of / count."""
        return self.in_place_of / self.count

    def subdivide(self) -> list[float]:
        """Return list of equal-duration slots that fill the tuplet span."""
        slot = self.unit * self.ratio
        return [slot] * self.count


TRIPLET = Tuplet(3, 2, 1.0)


class RhythmGenerator(typing.Protocol):
    """
    Protocol for all rhythm generators.
    Takes a total duration in beats and returns a list of rhythm events.
    """

    def generate(self, duration_beats: float) -> list[RhythmEvent]: ...


class RhythmProcessor:
    """
    Post-processing tools for RhythmEvent sequences.
    """

    @staticmethod
    def rotate(events: list[RhythmEvent], total_beats: float, offset_percent: float) -> list[RhythmEvent]:
        """Circularly shift events in time by a percentage of total_beats (-1.0 to 1.0)."""
        if not events or offset_percent == 0:
            return events
            
        shift = total_beats * offset_percent
        shifted = []
        for e in events:
            new_onset = (e.onset + shift) % total_beats
            shifted.append(RhythmEvent(onset=round(new_onset, 6), duration=e.duration, velocity_factor=e.velocity_factor))
            
        return sorted(shifted, key=lambda x: x.onset)

    @staticmethod
    def apply_dotted(events: list[RhythmEvent]) -> list[NoteInfo]:
        """Transform pairs of equal adjacent notes into dotted-rhythm pairs (3:1 length ratio)."""
        if len(events) < 2:
            return events
            
        processed = []
        i = 0
        while i < len(events):
            if i + 1 < len(events):
                e1, e2 = events[i], events[i+1]
                # If they are adjacent and equal length
                if abs(e1.duration - e2.duration) < 0.01 and abs((e1.onset + e1.duration) - e2.onset) < 0.01:
                    total_dur = e1.duration + e2.duration
                    processed.append(RhythmEvent(onset=e1.onset, duration=total_dur * 0.75, velocity_factor=e1.velocity_factor))
                    processed.append(RhythmEvent(onset=e1.onset + total_dur * 0.75, duration=total_dur * 0.25, velocity_factor=e2.velocity_factor))
                    i += 2
                    continue
            processed.append(events[i])
            i += 1
        return processed

    @staticmethod
    def apply_rests(events: list[RhythmEvent], keep_probability: float) -> list[RhythmEvent]:
        """Randomly drop notes to create rests (structural density setting)."""
        import random
        if keep_probability >= 1.0:
            return events
        return [e for e in events if random.random() < keep_probability]

    @staticmethod
    def apply_swing(events: list[RhythmEvent], amount: float = 0.6) -> list[RhythmEvent]:
        """Apply swing (0.5 = straight, 0.66 = triplet swing) to 8th/16th note grids."""
        if amount == 0.5:
            return events
            
        processed = []
        for e in events:
            # Simple 8th note swing logic: if it's on an off-beat (X.5), delay it
            # Works best for grids. 
            beat_pos = e.onset % 1.0
            if 0.4 <= beat_pos <= 0.6: # Approximate X.5
                offset = (amount - 0.5) * 1.0 # shift
                new_onset = (e.onset // 1.0) + amount
                processed.append(RhythmEvent(onset=round(new_onset, 6), duration=e.duration, velocity_factor=e.velocity_factor))
            else:
                processed.append(e)
        return processed


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


def apply_rhythm_events(notes: list, events: list[RhythmEvent]) -> list:
    """Re-rhythmize an existing note list onto a new onset/duration grid.

    For each ``RhythmEvent`` the closest-in-time source note is picked and its
    pitch/articulation/expression are reused; velocity is scaled by the event's
    ``velocity_factor``. This mirrors :class:`FollowRhythmModifier` but consumes
    ``RhythmEvent`` objects directly instead of another track's notes.

    Returns a fresh, start-sorted ``list[NoteInfo]``. Empty/missing input is
    passed through unchanged.
    """
    if not notes or not events:
        return notes

    from melodica.types import NoteInfo  # local import keeps rhythm/pitch decoupled

    # Pre-sort once for the repeated nearest-onset lookups below.
    sorted_notes = sorted(notes, key=lambda n: n.start)

    result: list[NoteInfo] = []
    for ev in events:
        # Nearest source note by start time.
        best = min(sorted_notes, key=lambda n: abs(n.start - ev.onset))
        new_vel = max(1, min(127, int(round(best.velocity * ev.velocity_factor))))
        result.append(
            NoteInfo(
                pitch=best.pitch,
                start=ev.onset,
                duration=max(0.05, ev.duration),
                velocity=new_vel,
                articulation=best.articulation,
                expression=dict(best.expression) if best.expression else {},
            )
        )

    result.sort(key=lambda n: n.start)
    return result


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
from melodica.rhythm.markov_rhythm import (
    MarkovRhythmGenerator,
    STYLE_MATRICES,
    TRANSITION_STRAIGHT, TRANSITION_SWING, TRANSITION_BALLAD, TRANSITION_DRIVING,
    TRANSITION_FUNK, TRANSITION_LATIN, TRANSITION_WALTZ,
    TRANSITION_HIP_HOP, TRANSITION_DNB, TRANSITION_AFRO,
)
from melodica.rhythm.groove_template import (
    GrooveSlot, GrooveTemplate, GROOVE_PRESETS,
    STRAIGHT, SWING_60, HARD_SWING, SHUFFLE, LAID_BACK,
    PUSH, REGGAE, BOSSA_NOVA, HIP_HOP, DRUM_AND_BASS,
    WALTZ_RUBATO, MAZURKA, BOLERO, SAMBA, FUNK, AFRO_6_8,
)

__all__ = [
    "RhythmEvent",
    "Tuplet",
    "TRIPLET",
    "RhythmGenerator",
    "RhythmCoordinator",
    "apply_rhythm_events",
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
    "STYLE_MATRICES",
    "TRANSITION_STRAIGHT",
    "TRANSITION_SWING",
    "TRANSITION_BALLAD",
    "TRANSITION_DRIVING",
    "TRANSITION_FUNK",
    "TRANSITION_LATIN",
    "TRANSITION_WALTZ",
    "TRANSITION_HIP_HOP",
    "TRANSITION_DNB",
    "TRANSITION_AFRO",
    "GrooveSlot",
    "GrooveTemplate",
    "GROOVE_PRESETS",
    "STRAIGHT",
    "SWING_60",
    "HARD_SWING",
    "SHUFFLE",
    "LAID_BACK",
    "PUSH",
    "REGGAE",
    "BOSSA_NOVA",
    "HIP_HOP",
    "DRUM_AND_BASS",
    "WALTZ_RUBATO",
    "MAZURKA",
    "BOLERO",
    "SAMBA",
    "FUNK",
    "AFRO_6_8",
]
