# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-05-23
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
    6. Low-end spacing (Acoustic series rules)

Fixes:
    - Transpose clashing notes by octave (prefer lower register)
    - Remove weakest note in unresolvable clashes
    - Reduce velocity of dissonant notes
    - Shorten duration of clashing notes
    - Velocity shading (reinforce stability)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from typing import Any
from melodica.types import NoteInfo


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_CONSONANT = {0, 3, 4, 5, 7, 8, 9, 12}  # P1, m3, M3, P4, P5, m6, M6, P8
_MILD_DISSONANT = {2, 10}  # M2, m7 — acceptable with resolution
_STRONG_DISSONANT = {1, 6, 11}  # m2, tritone, M7 — needs justification

# Register thresholds for Ideal Harmony
BASS_THRESHOLD = 48  # Below C3: strict consonance required
MID_THRESHOLD = 60   # C3 to C4: standard balance

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
    severity: str  # "mild", "strong", "critical" (for bass)


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
    apply_shading: bool = True  # Subtle velocity adjustments for stability


@dataclass
class VerifierReport:
    """Results of the verification pass."""

    clashes_detected: int = 0
    clashes_fixed: int = 0
    notes_removed: int = 0
    notes_transposed: int = 0
    notes_velocity_reduced: int = 0
    notes_shortened: int = 0
    notes_shaded: int = 0
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
    chords: list[Any] | None = None,
) -> list[ClashEvent]:
    """
    Detect simultaneous dissonant intervals across all track pairs.
    """
    import bisect
    from melodica.types import Quality
    events: list[ClashEvent] = []

    # Filter to only tracks containing NoteInfo objects
    valid_tracks = {}
    for name, items in tracks.items():
        if items and isinstance(items[0], NoteInfo):
            valid_tracks[name] = items

    track_names = list(valid_tracks.keys())
    tolerance = config.dissonance_tolerance

    # Pre-build active track density array for mid-range (36-60)
    mid_range_events = []
    for tname, notes in valid_tracks.items():
        for n in notes:
            if 36 <= n.pitch <= 60:
                mid_range_events.append((n.start, 1))
                mid_range_events.append((n.start + n.duration, -1))
    
    mid_range_events.sort(key=lambda x: (x[0], x[1]))
    density_times = []
    density_values = []
    current_density = 0
    for time, change in mid_range_events:
        current_density += change
        if not density_times or density_times[-1] != time:
            density_times.append(time)
            density_values.append(current_density)
        else:
            density_values[-1] = current_density

    # Find overlapping notes using sweep-line
    all_events = []
    for tname, notes in valid_tracks.items():
        for n in notes:
            all_events.append((n.start - config.window, 1, tname, id(n), n))
            all_events.append((n.start + n.duration, -1, tname, id(n), n))
            
    all_events.sort(key=lambda x: (x[0], x[1]))
    
    active_notes = {}

    for _, event_type, ta, na_id, na in all_events:
        if event_type == 1:
            for (tb, nb_id), nb in active_notes.items():
                if ta == tb:
                    continue

                iv = _interval(na.pitch, nb.pitch)
                if iv == 0:
                    continue

                severity = None
                
                # Register-aware severity (Bass Rule)
                is_low_clash = (na.pitch < BASS_THRESHOLD or nb.pitch < BASS_THRESHOLD)
                if is_low_clash:
                    if iv not in {0, 5, 7}: # P1, P4, P5 only
                        severity = "critical"
                    elif iv in {3, 4} and (na.pitch < 36 or nb.pitch < 36):
                        severity = "strong" # Thirds in sub-bass
                
                if severity is None:
                    if iv in _STRONG_DISSONANT:
                        severity = "strong"
                    elif iv in _MILD_DISSONANT:
                        severity = "mild"

                if severity is None:
                    continue

                beat = max(na.start, nb.start)
                current_tolerance = tolerance

                # Dynamic Mid-Range Penalty
                if 36 <= na.pitch <= 60 and 36 <= nb.pitch <= 60:
                    if density_times:
                        idx = bisect.bisect_right(density_times, beat) - 1
                        mid_active_tracks = density_values[idx] if idx >= 0 else 0
                    else:
                        mid_active_tracks = 0
                    if mid_active_tracks > 3:
                        current_tolerance = max(0.0, tolerance - 0.3)

                # Functional Awareness
                if chords:
                    from melodica.utils import chord_at
                    active_chord = chord_at(chords, beat)
                    
                    if active_chord:
                        pc_a, pc_b = na.pitch % 12, nb.pitch % 12
                        chord_pcs = active_chord.pitch_classes() if hasattr(active_chord, "pitch_classes") else []
                        
                        if pc_a in chord_pcs and pc_b in chord_pcs:
                            if not is_low_clash:
                                continue
                            else:
                                current_tolerance = max(0.0, current_tolerance - 0.2)
                            
                        if iv == 6 and getattr(active_chord, "quality", None) == Quality.DOMINANT7:
                            if (pc_a == (active_chord.root + 4) % 12 and pc_b == (active_chord.root + 10) % 12) or \
                               (pc_b == (active_chord.root + 4) % 12 and pc_a == (active_chord.root + 10) % 12):
                                if not is_low_clash:
                                    continue

                if severity == "mild" and current_tolerance > 0.7:
                    continue
                if severity == "strong" and current_tolerance > 0.9:
                    continue
                if severity == "critical" and current_tolerance > 0.1:
                    # Critical (bass) clashes are very strictly enforced
                    pass

                if na.duration < 0.05 or nb.duration < 0.05:
                    continue

                events.append(
                    ClashEvent(
                        beat=beat, note_a=na, track_a=ta,
                        note_b=nb, track_b=tb,
                        interval=iv, severity=severity,
                    )
                )
            active_notes[(ta, na_id)] = na
        else:
            active_notes.pop((ta, na_id), None)

    return events

def detect_parallel_fifths(
    tracks: dict[str, list[NoteInfo]],
) -> list[ClashEvent]:
    """
    Detect parallel fifths/octaves between consecutive notes in adjacent tracks.
    """
    import bisect
    events = []
    valid_tracks = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    track_names = list(valid_tracks.keys())

    for i in range(len(track_names)):
        for j in range(i + 1, len(track_names)):
            ta, tb = track_names[i], track_names[j]
            from operator import attrgetter
            start_getter = attrgetter("start")
            notes_a = sorted(valid_tracks[ta], key=start_getter)
            notes_b = sorted(valid_tracks[tb], key=start_getter)
            starts_b = [n.start for n in notes_b]

            # Check consecutive pairs
            for k in range(len(notes_a) - 1):
                na1, na2 = notes_a[k], notes_a[k + 1]
                # We need notes_b[m] starting near na1
                lo = bisect.bisect_left(starts_b, na1.start - 0.25)
                hi = bisect.bisect_right(starts_b, na1.start + 0.25)
                
                for m in range(lo, min(hi, len(notes_b) - 1)):
                    nb1, nb2 = notes_b[m], notes_b[m + 1]
                    
                    if abs(na1.start - nb1.start) > 0.25:
                        continue
                    if abs(na2.start - nb2.start) > 0.25:
                        continue

                    iv1 = _interval(na1.pitch, nb1.pitch)
                    iv2 = _interval(na2.pitch, nb2.pitch)

                    if (iv1, iv2) in ((0, 0), (7, 7)):
                        # Check direction
                        dir_a = 1 if na2.pitch > na1.pitch else (-1 if na2.pitch < na1.pitch else 0)
                        dir_b = 1 if nb2.pitch > nb1.pitch else (-1 if nb2.pitch < nb1.pitch else 0)
                        if dir_a == dir_b and dir_a != 0:
                            events.append(
                                ClashEvent(
                                    beat=na2.start,
                                    note_a=na2,
                                    track_a=ta,
                                    note_b=nb2,
                                    track_b=tb,
                                    interval=iv2,
                                    severity="mild",
                                )
                            )

    return events


# ---------------------------------------------------------------------------
# Shading: Ideal Harmony dynamic depth
# ---------------------------------------------------------------------------

def apply_harmonic_shading(
    tracks: dict[str, list[NoteInfo]],
    chords: list[Any] | None = None,
    report: VerifierReport | None = None
) -> dict[str, list[NoteInfo]]:
    """
    Subtly adjust note velocities based on harmonic stability.
    Stable (root, fifth) -> +3-5% velocity.
    Dissonant (m2, tritone) -> -5-10% velocity.
    """
    from melodica.utils import chord_at
    
    result = {}
    for tname, notes in tracks.items():
        shaded_notes = []
        for n in notes:
            chord = chord_at(chords, n.start) if chords else None
            pc = n.pitch % 12
            factor = 1.0
            
            if chord:
                # 1. Relation to underlying chord
                chord_pcs = chord.pitch_classes() if hasattr(chord, "pitch_classes") else []
                if pc == chord.root % 12:
                    factor *= 1.05 # Boost root
                elif pc == (chord.root + 7) % 12:
                    factor *= 1.03 # Boost fifth
                elif pc not in chord_pcs:
                    factor *= 0.95 # Slights soften non-chord tones
            
            # 2. Velocity shading based on pitch height (Airiness)
            if n.pitch > 84: # High register
                factor *= 0.98 # Subtly soften piercing highs
            elif n.pitch < 36: # Deep bass
                factor *= 1.02 # Subtly boost fundamental warmth
                
            new_vel = int(n.velocity * factor)
            if new_vel != n.velocity:
                if report: report.notes_shaded += 1
                
            shaded_notes.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=max(1, min(127, new_vel)),
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[tname] = shaded_notes
    return result


# ---------------------------------------------------------------------------
# Fix strategies
# ---------------------------------------------------------------------------
# Global lookup table for transpositions: (current_pc, other_pc) -> list of consonant pitch classes
_TRANSPOSE_LOOKUP: dict[tuple[int, int], list[int]] = {}

def _get_consonant_pcs(current_pc: int, other_pc: int) -> list[int]:
    key = (current_pc, other_pc)
    if key in _TRANSPOSE_LOOKUP:
        return _TRANSPOSE_LOOKUP[key]
    
    res = []
    # Find all pitch classes that are consonant or mild dissonant with other_pc
    for pc in range(12):
        iv = abs(pc - other_pc) % 12
        if iv in _CONSONANT or iv in _MILD_DISSONANT:
            res.append(pc)
            
    # Sort by distance from current_pc (modulo 12)
    res.sort(key=lambda pc: min(abs(pc - current_pc), 12 - abs(pc - current_pc)))
    _TRANSPOSE_LOOKUP[key] = res
    return res

def _try_transpose(note: NoteInfo, other_pitch: int) -> NoteInfo:
    """Transpose note to nearest pitch that avoids clash with other_pitch."""
    current_pc = note.pitch % 12
    other_pc = other_pitch % 12

    consonant_pcs = _get_consonant_pcs(current_pc, other_pc)
    
    best_pitch = note.pitch
    best_dist = 999

    # Try only valid pitch classes
    for new_pc in consonant_pcs:
        # Optimization: if the closest possible note with this PC is already worse than best_dist, skip
        # Try staying in same octave first, then shift
        for oct_shift in [0, -12, 12, -24, 24]:
            candidate = (note.pitch // 12) * 12 + new_pc + oct_shift
            if 0 <= candidate <= 127 and candidate != note.pitch:
                dist = abs(candidate - note.pitch)
                if dist < best_dist:
                    best_dist = dist
                    best_pitch = candidate
                    
        # If we found a very close note (within a few semitones), we can stop
        if best_dist < 4:
            break

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


def _reduce_velocity(note: NoteInfo, factor: float = 0.5, min_velocity: int = 40) -> NoteInfo:
    """Reduce velocity to make clash less prominent, but stay above floor."""
    return NoteInfo(
        pitch=note.pitch,
        start=note.start,
        duration=note.duration,
        velocity=max(min_velocity, min(note.velocity, int(note.velocity * factor))),
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

    chords = tracks.get("_chords")
    clashes = detect_clashes(note_tracks, config, chords=chords)
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
                fixed[ta][idx_a] = _reduce_velocity(na, 0.7)
                report.notes_velocity_reduced += 1
            else:
                fixed[tb][idx_b] = _reduce_velocity(nb, 0.7)
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

    # Phase 4: Shading (Subtle reinforcement)
    if config.apply_shading:
        fixed = apply_harmonic_shading(fixed, chords=chords, report=report)

    # Phase 5: Polyphony check
    fixed = _reduce_polyphony(fixed, config.max_polyphony, report)

    # Re-sort all tracks in-place using fast native C-level attribute getter
    from operator import attrgetter
    start_getter = attrgetter("start")
    for k in fixed:
        fixed[k].sort(key=start_getter)

    return fixed, report


def detect_voice_crossing(
    tracks: dict[str, list[NoteInfo]],
) -> list[ClashEvent]:
    """Detect when a lower voice goes above a higher voice (e.g. Alto > Soprano)."""
    import bisect
    events = []
    # Standard SATB order for crossing check
    names = ["soprano", "alto", "tenor", "bass"]
    valid = {n: tracks[n] for n in names if n in tracks and tracks[n]}
    
    # We only check adjacent pairs in the hierarchy
    check_pairs = []
    if "soprano" in valid and "alto" in valid: check_pairs.append(("soprano", "alto"))
    if "alto" in valid and "tenor" in valid: check_pairs.append(("alto", "tenor"))
    if "tenor" in valid and "bass" in valid: check_pairs.append(("tenor", "bass"))

    for upper_name, lower_name in check_pairs:
        notes_u = valid[upper_name]
        notes_l = valid[lower_name]
        starts_l = [n.start for n in notes_l]

        for nu in notes_u:
            lo = bisect.bisect_left(starts_l, nu.start - 1.0)
            hi = bisect.bisect_right(starts_l, nu.start + nu.duration)
            for nl in notes_l[lo:hi]:
                if not _notes_overlap(nu, nl):
                    continue
                if nl.pitch > nu.pitch:
                    events.append(ClashEvent(
                        beat=max(nu.start, nl.start),
                        note_a=nu, track_a=upper_name,
                        note_b=nl, track_b=lower_name,
                        interval=nl.pitch - nu.pitch,
                        severity="mild"
                    ))
    return events


def detect_spacing_errors(
    tracks: dict[str, list[NoteInfo]],
    max_gap: int = 12
) -> list[ClashEvent]:
    """Detect when voices (except bass/tenor) are too far apart (> octave)."""
    import bisect
    events = []
    valid = {n: tracks[n] for n in ["soprano", "alto", "tenor"] if n in tracks and tracks[n]}
    
    check_pairs = []
    if "soprano" in valid and "alto" in valid: check_pairs.append(("soprano", "alto"))
    if "alto" in valid and "tenor" in valid: check_pairs.append(("alto", "tenor"))

    for upper_name, lower_name in check_pairs:
        notes_u = valid[upper_name]
        notes_l = valid[lower_name]
        starts_l = [n.start for n in notes_l]

        for nu in notes_u:
            lo = bisect.bisect_left(starts_l, nu.start - 1.0)
            hi = bisect.bisect_right(starts_l, nu.start + nu.duration)
            for nl in notes_l[lo:hi]:
                if not _notes_overlap(nu, nl):
                    continue
                gap = nu.pitch - nl.pitch
                if gap > max_gap:
                    events.append(ClashEvent(
                        beat=max(nu.start, nl.start),
                        note_a=nu, track_a=upper_name,
                        note_b=nl, track_b=lower_name,
                        interval=gap,
                        severity="mild"
                    ))
    return events


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
