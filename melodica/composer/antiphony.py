"""composer/antiphony.py — Call-and-response (antiphony) section builder.

Splits a set of tracks into two orchestral groups and alternates phrases
between them: group A "calls", group B "responds".

Orchestral groups (default assignment by GM program range):
  strings  — GM 40–55  (violin, viola, cello, contrabass, harp, etc.)
  winds    — GM 56–79  (flute, oboe, clarinet, bassoon, sax, etc.)
  brass    — GM 56–63  (trumpet, trombone, tuba, french horn)
  keys     — GM 0–8    (piano, harpsichord, celesta, etc.)
  perc     — GM 112–127

Usage
-----
    from melodica.composer.antiphony import AntiphonyBuilder, InstrumentGroup

    builder = AntiphonyBuilder(
        call_group=InstrumentGroup.STRINGS,
        response_group=InstrumentGroup.WINDS,
        phrase_bars=2,
        overlap_bars=0.0,
    )
    # notes_by_track: dict[track_name → list[NoteInfo]]
    result = builder.apply(notes_by_track, bars_per_beat=1.0)
    # result: same dict but notes muted outside each group's phrase windows
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from melodica.types_pkg._notes import NoteInfo


# ---------------------------------------------------------------------------
# Instrument group definitions (GM program ranges)
# ---------------------------------------------------------------------------

class InstrumentGroup(str, Enum):
    STRINGS = "strings"
    WINDS   = "winds"
    BRASS   = "brass"
    KEYS    = "keys"
    PERC    = "perc"
    ALL     = "all"


# GM program → group mapping
def _gm_group(program: int) -> InstrumentGroup:
    p = program % 128
    if p < 8:
        return InstrumentGroup.KEYS
    if 8 <= p <= 15:
        return InstrumentGroup.KEYS      # chromatic perc (bells, marimba)
    if 40 <= p <= 55:
        return InstrumentGroup.STRINGS
    if 56 <= p <= 63:
        return InstrumentGroup.BRASS
    if 64 <= p <= 79:
        return InstrumentGroup.WINDS
    if p >= 112:
        return InstrumentGroup.PERC
    return InstrumentGroup.ALL


# ---------------------------------------------------------------------------
# Antiphony window helpers
# ---------------------------------------------------------------------------

@dataclass
class PhraseWindow:
    """A time window assigned to one group."""
    start_beat: float
    end_beat: float
    group: InstrumentGroup


def build_windows(
    total_beats: float,
    phrase_beats: float,
    call_group: InstrumentGroup,
    response_group: InstrumentGroup,
    overlap_beats: float = 0.0,
    start_with: InstrumentGroup | None = None,
) -> list[PhraseWindow]:
    """Build alternating call/response windows over total_beats.

    Parameters
    ----------
    total_beats : float
        Total length of the section in beats.
    phrase_beats : float
        Duration of each call or response phrase.
    call_group : InstrumentGroup
        Group that calls first.
    response_group : InstrumentGroup
        Group that responds.
    overlap_beats : float
        How many beats the response overlaps with the end of the call
        (0 = strict alternation, >0 = overlapping phrases).
    start_with : InstrumentGroup | None
        Override which group starts (default: call_group).
    """
    windows: list[PhraseWindow] = []
    t = 0.0
    groups = [call_group, response_group]
    idx = 0 if (start_with is None or start_with == call_group) else 1

    while t < total_beats:
        g = groups[idx % 2]
        w_start = max(0.0, t - (overlap_beats if idx > 0 else 0.0))
        w_end   = min(total_beats, t + phrase_beats)
        windows.append(PhraseWindow(w_start, w_end, g))
        t += phrase_beats
        idx += 1

    return windows


# ---------------------------------------------------------------------------
# AntiphonyBuilder
# ---------------------------------------------------------------------------

@dataclass
class AntiphonyBuilder:
    """Apply call-and-response alternation to track note lists.

    Notes outside a track's assigned phrase windows are removed (silenced).
    Notes that overlap a window boundary are truncated to fit.

    Parameters
    ----------
    call_group : InstrumentGroup
        Orchestral group that leads (call).
    response_group : InstrumentGroup
        Orchestral group that answers (response).
    phrase_bars : float
        Number of bars per call/response phrase.
    beats_per_bar : float
        Beats per bar (default 4.0).
    overlap_bars : float
        Overlap between call end and response start in bars (default 0).
    echo_velocity_scale : float
        Velocity scale for the response group (0.8 = softer echo).
    track_group_map : dict[str, InstrumentGroup] | None
        Explicit track_name → group assignment.
        If None, groups are inferred from track GM program via _gm_group().
    track_programs : dict[str, int] | None
        track_name → GM program number, used when track_group_map is None.
    """

    call_group: InstrumentGroup = InstrumentGroup.STRINGS
    response_group: InstrumentGroup = InstrumentGroup.WINDS
    phrase_bars: float = 2.0
    beats_per_bar: float = 4.0
    overlap_bars: float = 0.0
    echo_velocity_scale: float = 0.85
    track_group_map: dict[str, InstrumentGroup] | None = None
    track_programs: dict[str, int] | None = None

    # ------------------------------------------------------------------

    def _resolve_group(self, track_name: str) -> InstrumentGroup:
        if self.track_group_map and track_name in self.track_group_map:
            return self.track_group_map[track_name]
        if self.track_programs and track_name in self.track_programs:
            return _gm_group(self.track_programs[track_name])
        return InstrumentGroup.ALL

    def _filter_notes(
        self,
        notes: list[NoteInfo],
        windows: list[PhraseWindow],
        group: InstrumentGroup,
        velocity_scale: float = 1.0,
    ) -> list[NoteInfo]:
        """Keep only notes that fall within any window assigned to this group."""
        group_windows = [w for w in windows if w.group == group or group == InstrumentGroup.ALL]
        if not group_windows:
            return []

        result: list[NoteInfo] = []
        for note in notes:
            note_end = note.start + note.duration
            for w in group_windows:
                # Note overlaps this window
                if note.start < w.end_beat and note_end > w.start_beat:
                    clipped_start = max(note.start, w.start_beat)
                    clipped_end   = min(note_end, w.end_beat)
                    clipped_dur   = clipped_end - clipped_start
                    if clipped_dur > 0.01:
                        c = copy.copy(note)
                        c.start    = clipped_start
                        c.duration = clipped_dur
                        if velocity_scale != 1.0:
                            c.velocity = max(1, min(127, int(c.velocity * velocity_scale)))
                        result.append(c)
                    break  # note handled

        return sorted(result, key=lambda n: n.start)

    def apply(
        self,
        notes_by_track: dict[str, list[NoteInfo]],
        total_beats: float | None = None,
    ) -> dict[str, list[NoteInfo]]:
        """Apply antiphony to all tracks.

        Parameters
        ----------
        notes_by_track : dict[str, list[NoteInfo]]
            Input notes per track.
        total_beats : float | None
            Total section length in beats. If None, inferred from max note end.

        Returns
        -------
        dict[str, list[NoteInfo]]
            Filtered notes per track.
        """
        if total_beats is None:
            total_beats = max(
                (n.start + n.duration for notes in notes_by_track.values() for n in notes),
                default=0.0,
            )

        phrase_beats  = self.phrase_bars * self.beats_per_bar
        overlap_beats = self.overlap_bars * self.beats_per_bar

        windows = build_windows(
            total_beats=total_beats,
            phrase_beats=phrase_beats,
            call_group=self.call_group,
            response_group=self.response_group,
            overlap_beats=overlap_beats,
        )

        result: dict[str, list[NoteInfo]] = {}
        for track_name, notes in notes_by_track.items():
            group = self._resolve_group(track_name)

            if group == InstrumentGroup.ALL:
                # Tracks not assigned to either group play through unchanged
                result[track_name] = list(notes)
                continue

            vel = self.echo_velocity_scale if group == self.response_group else 1.0
            result[track_name] = self._filter_notes(notes, windows, group, vel)

        return result

    def windows_summary(self, total_beats: float) -> str:
        """Return a human-readable summary of call/response windows."""
        phrase_beats  = self.phrase_bars * self.beats_per_bar
        overlap_beats = self.overlap_bars * self.beats_per_bar
        windows = build_windows(total_beats, phrase_beats,
                                self.call_group, self.response_group, overlap_beats)
        lines = [f"AntiphonyBuilder: {self.call_group.value} → {self.response_group.value}"]
        for w in windows:
            lines.append(f"  [{w.start_beat:.1f}–{w.end_beat:.1f}b]  {w.group.value}")
        return "\n".join(lines)
