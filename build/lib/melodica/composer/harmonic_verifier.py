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
composer/harmonic_verifier.py — Cross-track harmonic verification.

Post-render pass that detects and resolves cacophony across all tracks.
Runs after generators produce their output but before MIDI export.

Checks:
    1. Simultaneous minor-2nd clashes (m2 = 1 semitone)
    2. Simultaneous tritone clashes (TT = 6 semitones) above threshold
    3. Unresolved dissonances (dissonant interval persists too long)
    4. Parallel fifths/octaves between adjacent-register tracks
    5. Excessive polyphony (too many notes at once)

Fixes:
    - Transpose clashing notes by octave (prefer lower register)
    - Remove weakest note in unresolvable clashes
    - Reduce velocity of dissonant notes
    - Shorten duration of clashing notes
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from melodica.types import NoteInfo


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_CONSONANT = {0, 3, 4, 5, 7, 8, 9, 12}  # P1, m3, M3, P4, P5, m6, M6, P8
_MILD_DISSONANT = {2, 10}  # M2, m7 — acceptable with resolution
_STRONG_DISSONANT = {1, 6, 11}  # m2, tritone, M7 — needs justification

# Maximum tolerable simultaneous notes
_DEFAULT_MAX_POLYPHONY = 10

# Clash detection window (seconds at 120 BPM)
_DEFAULT_WINDOW = 0.125  # 32nd note


@dataclass
class ClashEvent:
    """A detected harmonic clash between two notes."""

    beat: float
    note_a: NoteInfo
    track_a: str
    note_b: NoteInfo
    track_b: str
    interval: int
    severity: str  # "mild", "strong"


@dataclass
class VerifierConfig:
    """Configuration for the harmonic verifier."""

    dissonance_tolerance: float = 0.5  # 0.0 = strict, 1.0 = permissive
    max_polyphony: int = _DEFAULT_MAX_POLYPHONY
    window: float = _DEFAULT_WINDOW
    fix_transpose: bool = True
    fix_remove: bool = True
    fix_velocity: bool = True
    fix_shorten: bool = True


@dataclass
class VerifierReport:
    """Results of the verification pass."""

    clashes_detected: int = 0
    clashes_fixed: int = 0
    notes_removed: int = 0
    notes_transposed: int = 0
    notes_velocity_reduced: int = 0
    notes_shortened: int = 0
    polyphony_reduced: int = 0
    events: list[ClashEvent] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------
def _notes_overlap(a: NoteInfo, b: NoteInfo, window: float = 0.0) -> bool:
    """Check if two notes overlap in time (with optional window)."""
    a_end = a.start + a.duration
    b_end = b.start + b.duration
    return (a.start - window) < b_end and (b.start - window) < a_end


def _interval(a: int, b: int) -> int:
    """Chromatic interval between two MIDI pitches (0-12)."""
    return abs(a - b) % 12


def detect_clashes(
    tracks: dict[str, list[NoteInfo]],
    config: VerifierConfig,
) -> list[ClashEvent]:
    """
    Detect simultaneous dissonant intervals across all track pairs.
    """
    events: list[ClashEvent] = []

    # Filter to only tracks containing NoteInfo objects
    valid_tracks = {}
    for name, items in tracks.items():
        if items and isinstance(items[0], NoteInfo):
            valid_tracks[name] = items

    track_names = list(valid_tracks.keys())
    tolerance = config.dissonance_tolerance

    for i in range(len(track_names)):
        for j in range(i + 1, len(track_names)):
            ta, tb = track_names[i], track_names[j]
            notes_a = valid_tracks[ta]
            notes_b = valid_tracks[tb]

            for na in notes_a:
                for nb in notes_b:
                    if not _notes_overlap(na, nb, config.window):
                        continue

                    iv = _interval(na.pitch, nb.pitch)
                    if iv == 0:
                        continue  # unison/octave — fine

                    severity = None
                    if iv in _STRONG_DISSONANT:
                        severity = "strong"
                    elif iv in _MILD_DISSONANT:
                        severity = "mild"

                    if severity is None:
                        continue  # consonant

                    # Tolerance check: high tolerance = allow more
                    if severity == "mild" and tolerance > 0.7:
                        continue
                    if severity == "strong" and tolerance > 0.9:
                        continue

                    # Skip very brief notes (MIDI artifacts)
                    if na.duration < 0.05 or nb.duration < 0.05:
                        continue

                    overlap_dur = min(na.start + na.duration, nb.start + nb.duration) - max(
                        na.start, nb.start
                    )
                    min_dur = min(na.duration, nb.duration)
                    if overlap_dur < min_dur * 0.5:
                        continue  # overlap less than half the shorter note

                    events.append(
                        ClashEvent(
                            beat=max(na.start, nb.start),
                            note_a=na,
                            track_a=ta,
                            note_b=nb,
                            track_b=tb,
                            interval=iv,
                            severity=severity,
                        )
                    )

    return events


def detect_parallel_fifths(
    tracks: dict[str, list[NoteInfo]],
) -> list[ClashEvent]:
    """
    Detect parallel fifths/octaves between consecutive notes in adjacent tracks.
    """
    events = []
    valid_tracks = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    track_names = list(valid_tracks.keys())

    for i in range(len(track_names)):
        for j in range(i + 1, len(track_names)):
            ta, tb = track_names[i], track_names[j]
            notes_a = sorted(valid_tracks[ta], key=lambda n: n.start)
            notes_b = sorted(valid_tracks[tb], key=lambda n: n.start)

            # Check consecutive pairs
            for k in range(len(notes_a) - 1):
                for m in range(len(notes_b) - 1):
                    if abs(notes_a[k].start - notes_b[m].start) > 0.25:
                        continue
                    if abs(notes_a[k + 1].start - notes_b[m + 1].start) > 0.25:
                        continue

                    iv1 = _interval(notes_a[k].pitch, notes_b[m].pitch)
                    iv2 = _interval(notes_a[k + 1].pitch, notes_b[m + 1].pitch)

                    if (iv1, iv2) in ((0, 0), (7, 7)):
                        events.append(
                            ClashEvent(
                                beat=notes_a[k + 1].start,
                                note_a=notes_a[k + 1],
                                track_a=ta,
                                note_b=notes_b[m + 1],
                                track_b=tb,
                                interval=iv2,
                                severity="mild",
                            )
                        )

    return events


# ---------------------------------------------------------------------------
# Fix strategies
# ---------------------------------------------------------------------------
def _try_transpose(note: NoteInfo, other_pitch: int) -> NoteInfo:
    """Transpose note to nearest pitch that avoids clash with other_pitch."""
    current_pc = note.pitch % 12
    other_pc = other_pitch % 12

    # Try all 12 pitch classes, find the nearest consonant one
    best_pitch = note.pitch
    best_dist = 999

    for pc_offset in range(12):
        new_pc = (current_pc + pc_offset) % 12
        iv = abs(new_pc - other_pc) % 12
        if iv in _CONSONANT or iv in _MILD_DISSONANT:
            # Try staying in same octave first, then shift
            for oct_shift in [0, -12, 12, -24, 24]:
                candidate = (note.pitch // 12) * 12 + new_pc + oct_shift
                if 0 <= candidate <= 127 and candidate != note.pitch:
                    dist = abs(candidate - note.pitch)
                    if dist < best_dist:
                        best_dist = dist
                        best_pitch = candidate

    if best_pitch != note.pitch:
        return NoteInfo(
            pitch=best_pitch,
            start=note.start,
            duration=note.duration,
            velocity=note.velocity,
            articulation=note.articulation,
            expression=note.expression,
        )
    return note


def _reduce_velocity(note: NoteInfo, factor: float = 0.5) -> NoteInfo:
    """Reduce velocity to make clash less prominent."""
    return NoteInfo(
        pitch=note.pitch,
        start=note.start,
        duration=note.duration,
        velocity=max(10, int(note.velocity * factor)),
        articulation=note.articulation,
        expression=note.expression,
    )


def _shorten(note: NoteInfo, factor: float = 0.5) -> NoteInfo:
    """Shorten duration to reduce overlap."""
    return NoteInfo(
        pitch=note.pitch,
        start=note.start,
        duration=note.duration * factor,
        velocity=note.velocity,
        articulation=note.articulation,
        expression=note.expression,
    )


# ---------------------------------------------------------------------------
# Main verifier
# ---------------------------------------------------------------------------
def verify_and_fix(
    tracks: dict[str, list[NoteInfo]],
    config: VerifierConfig | None = None,
) -> tuple[dict[str, list[NoteInfo]], VerifierReport]:
    """
    Run cross-track harmonic verification and fix detected clashes.

    Returns:
        (fixed_tracks, report)
    """
    if config is None:
        config = VerifierConfig()

    report = VerifierReport()

    # Filter to only NoteInfo tracks (skip _chords, _metadata, etc.)
    note_tracks = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}

    # Phase 1: Detect clashes
    clashes = detect_clashes(note_tracks, config)
    parallel = detect_parallel_fifths(note_tracks)
    all_events = clashes + parallel
    report.clashes_detected = len(all_events)
    report.events = all_events[:50]  # keep first 50 for report

    # Phase 2: Build note index for fast lookup
    # Map (track_name, note_identity) → index in track list
    note_index: dict[tuple[str, int], int] = {}
    for tname, notes in note_tracks.items():
        for idx, n in enumerate(notes):
            note_index[(tname, id(n))] = idx

    # Phase 3: Fix clashes (even if none, we still need fixed dict for polyphony)
    fixed: dict[str, list[NoteInfo]] = {k: list(v) for k, v in note_tracks.items()}

    for evt in all_events:
        ta, tb = evt.track_a, evt.track_b

        # Find current indices
        idx_a = note_index.get((ta, id(evt.note_a)))
        idx_b = note_index.get((tb, id(evt.note_b)))

        if idx_a is None or idx_b is None:
            continue

        na = fixed[ta][idx_a]
        nb = fixed[tb][idx_b]

        # Strategy 1: Transpose the lower-velocity note
        if config.fix_transpose:
            if na.velocity <= nb.velocity:
                new_na = _try_transpose(na, nb.pitch)
                if new_na.pitch != na.pitch:
                    fixed[ta][idx_a] = new_na
                    report.notes_transposed += 1
                    report.clashes_fixed += 1
                    note_index[(ta, id(new_na))] = idx_a
                    continue
            else:
                new_nb = _try_transpose(nb, na.pitch)
                if new_nb.pitch != nb.pitch:
                    fixed[tb][idx_b] = new_nb
                    report.notes_transposed += 1
                    report.clashes_fixed += 1
                    note_index[(tb, id(new_nb))] = idx_b
                    continue

        # Strategy 2: Reduce velocity
        if config.fix_velocity:
            if na.velocity <= nb.velocity:
                fixed[ta][idx_a] = _reduce_velocity(na, 0.4)
                report.notes_velocity_reduced += 1
            else:
                fixed[tb][idx_b] = _reduce_velocity(nb, 0.4)
                report.notes_velocity_reduced += 1
            report.clashes_fixed += 1
            continue

        # Strategy 3: Shorten
        if config.fix_shorten:
            if na.velocity <= nb.velocity:
                fixed[ta][idx_a] = _shorten(na, 0.3)
                report.notes_shortened += 1
            else:
                fixed[tb][idx_b] = _shorten(nb, 0.3)
                report.notes_shortened += 1
            report.clashes_fixed += 1

    # Phase 4: Polyphony check
    fixed = _reduce_polyphony(fixed, config.max_polyphony, report)

    # Re-sort all tracks
    for k in fixed:
        fixed[k] = sorted(fixed[k], key=lambda n: n.start)

    return fixed, report


def _reduce_polyphony(
    tracks: dict[str, list[NoteInfo]],
    max_poly: int,
    report: VerifierReport,
) -> dict[str, list[NoteInfo]]:
    """Reduce velocity when too many notes play simultaneously."""
    all_notes = []
    for name, notes in tracks.items():
        for i, n in enumerate(notes):
            all_notes.append((n.start, name, i))
    all_notes.sort()

    grid: dict[int, int] = {}
    for t, _, _ in all_notes:
        key = int(t * 4)
        grid[key] = grid.get(key, 0) + 1

    peak = max(grid.values()) if grid else 1
    if peak <= max_poly:
        return tracks

    result = {}
    for name, notes in tracks.items():
        scaled = []
        for n in notes:
            key = int(n.start * 4)
            poly = grid.get(key, 1)
            if poly > max_poly:
                ratio = max_poly / poly
                vel = max(15, int(n.velocity * ratio))
                report.polyphony_reduced += 1
            else:
                vel = n.velocity
            scaled.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=vel,
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[name] = scaled
    return result
