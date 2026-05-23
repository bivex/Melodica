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
composer/psychoacoustic.py — Psychoacoustic verification.

Post-render pass that detects perceptual issues invisible to MIDI but
audible to humans. Based on psychoacoustic models of auditory masking,
fusion, and temporal resolution.

Checks:
    1. Frequency masking — loud note masks quiet note nearby in pitch
    2. Temporal masking — quiet note before/after loud note is masked
    3. Harmonic fusion — octave/fifth with same onset fuses into one sound
    4. Rhythmic blur — notes too fast to be individually perceived
    5. Register masking — bass masks melody in same low register
    6. Brightness overload — too many notes in high register at once

Fixes:
    - Remove masked notes (inaudible)
    - Shorten blurry notes to minimum audible duration
    - Transpose fusion notes to different octave
    - Reduce velocity of competing register notes
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.types import NoteInfo


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Critical bandwidth in semitones (approximation of Bark scale)
_CRITICAL_BANDWIDTH = 5  # semitones — notes within this compete

# Temporal masking window (seconds)
_PRE_MASKING = 0.05  # 50ms before a loud sound
_POST_MASKING = 0.10  # 100ms after a loud sound

# Minimum audible duration (seconds) at typical tempos
# Velocity thresholds for masking
_MASKING_VELOCITY_DIFF = 20  # loud note must be this much louder to mask
_TEMPORAL_VELOCITY_DIFF = 30  # temporal masking needs bigger difference

# Minimum audible duration at 120 BPM (half of a 1/32 note)
# Recomputed at runtime from bpm via _min_audible_duration(bpm)
_MIN_AUDIBLE_DURATION_120 = 0.03  # seconds at 120 BPM


def _min_audible_duration(bpm: float) -> float:
    """[FIX 2] BPM-adaptive blur threshold.

    Returns half the duration of a 1/32 note at the given BPM in seconds.
    At 120 BPM: 0.5 × (60/120) / 8 = 0.031s  ≈ original 0.03 constant.
    At 160 BPM: 0.5 × (60/160) / 8 = 0.023s  → more notes detected as blur.
    At  60 BPM: 0.5 × (60/ 60) / 8 = 0.062s  → threshold relaxed appropriately.
    """
    return max(0.015, 0.5 * (60.0 / max(bpm, 20.0)) / 8.0)


# Fusion intervals (unison, octave, fifth)
_FUSION_INTERVALS = {0, 7, 12}

# Low register boundary (MIDI pitch)
_LOW_REGISTER = 60  # C4 — below this, bass and melody compete

# High register for brightness check
_HIGH_REGISTER = 84  # C6 — above this, too many notes = harsh


@dataclass
class PsychoEvent:
    """A detected psychoacoustic issue."""

    beat: float
    track_a: str
    note_a: NoteInfo
    track_b: str
    note_b: NoteInfo | None
    issue: str  # "freq_mask", "temporal_mask", "fusion", "blur", "reg_mask", "brightness"
    severity: str  # "mild", "strong"


@dataclass
class PsychoConfig:
    """Configuration for psychoacoustic verification."""

    check_freq_masking: bool = True
    check_temporal_masking: bool = True
    check_fusion: bool = True
    check_blur: bool = True
    check_register_masking: bool = True
    check_brightness: bool = True
    aggressive_fix: bool = False  # if True, remove masked notes; else just reduce velocity


@dataclass
class PsychoReport:
    """Results of psychoacoustic verification."""

    issues_detected: int = 0
    issues_fixed: int = 0
    notes_removed: int = 0
    notes_shortened: int = 0
    notes_transposed: int = 0
    notes_velocity_reduced: int = 0
    events: list[PsychoEvent] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------


def _freq_masked(loud: NoteInfo, quiet: NoteInfo) -> bool:
    """Check if loud note masks quiet note in frequency domain."""
    interval = abs(loud.pitch - quiet.pitch)
    if interval > _CRITICAL_BANDWIDTH or interval == 0:
        return False
    return loud.velocity - quiet.velocity >= _MASKING_VELOCITY_DIFF


def _temporal_masked(loud: NoteInfo, quiet: NoteInfo) -> bool:
    """Check if quiet note is temporally masked by loud note."""
    loud_end = loud.start + loud.duration

    # Pre-masking: quiet note starts just before loud note
    if loud.start - _PRE_MASKING <= quiet.start <= loud.start:
        return loud.velocity - quiet.velocity >= _TEMPORAL_VELOCITY_DIFF

    # Post-masking: quiet note starts just after loud note
    if loud_end <= quiet.start <= loud_end + _POST_MASKING:
        return loud.velocity - quiet.velocity >= _TEMPORAL_VELOCITY_DIFF

    return False


def _is_fusion(a: NoteInfo, b: NoteInfo) -> bool:
    """Check if two notes with same onset fuse into one percept."""
    if abs(a.start - b.start) > 0.02:
        return False
    interval = abs(a.pitch - b.pitch) % 12  # 0-11
    return interval in {0, 7}


def _is_blurry(note: NoteInfo, min_dur: float) -> bool:
    """[FIX 2] Check if note is too short to be individually perceived (BPM-aware)."""
    return note.duration < min_dur


def detect_frequency_masking(
    tracks: dict[str, list[NoteInfo]],
) -> list[PsychoEvent]:
    """Detect frequency masking across track pairs."""
    events = []
    valid = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    
    all_events = []
    for tname, notes in valid.items():
        for n in notes:
            all_events.append((n.start, 1, tname, id(n), n))
            all_events.append((n.start + n.duration, -1, tname, id(n), n))
            
    all_events.sort(key=lambda x: (x[0], x[1]))
    active_notes = {}

    for _, event_type, ta, na_id, na in all_events:
        if event_type == 1:
            for (tb, nb_id), nb in active_notes.items():
                if ta == tb:
                    continue
                
                if _freq_masked(na, nb):
                    events.append(PsychoEvent(
                        beat=nb.start, track_a=ta, note_a=na,
                        track_b=tb, note_b=nb,
                        issue="freq_mask", severity="strong",
                    ))
                elif _freq_masked(nb, na):
                    events.append(PsychoEvent(
                        beat=na.start, track_a=tb, note_a=nb,
                        track_b=ta, note_b=na,
                        issue="freq_mask", severity="strong",
                    ))
            active_notes[(ta, na_id)] = na
        else:
            active_notes.pop((ta, na_id), None)
            
    return events


def detect_temporal_masking(
    tracks: dict[str, list[NoteInfo]],
) -> list[PsychoEvent]:
    """Detect temporal masking across track pairs."""
    _WINDOW = _PRE_MASKING + _POST_MASKING
    events = []
    valid = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    
    all_events = []
    for tname, notes in valid.items():
        for n in notes:
            # We must be active if we could MASK or BE MASKED.
            # Masking range for loud note: [start - PRE, end + POST]
            # Being masked range for quiet note: [start, start] (actually we only care about quiet note start)
            # So expanding everything by _WINDOW is safe.
            all_events.append((n.start - _WINDOW, 1, tname, id(n), n))
            all_events.append((n.start + n.duration + _WINDOW, -1, tname, id(n), n))
            
    all_events.sort(key=lambda x: (x[0], x[1]))
    active_notes = {}

    for _, event_type, ta, na_id, na in all_events:
        if event_type == 1:
            for (tb, nb_id), nb in active_notes.items():
                if ta == tb:
                    continue
                
                if _temporal_masked(na, nb):
                    events.append(PsychoEvent(
                        beat=nb.start, track_a=ta, note_a=na,
                        track_b=tb, note_b=nb,
                        issue="temporal_mask", severity="mild",
                    ))
                elif _temporal_masked(nb, na):
                    events.append(PsychoEvent(
                        beat=na.start, track_a=tb, note_a=nb,
                        track_b=ta, note_b=na,
                        issue="temporal_mask", severity="mild",
                    ))
            active_notes[(ta, na_id)] = na
        else:
            active_notes.pop((ta, na_id), None)
            
    return events


def detect_fusion(
    tracks: dict[str, list[NoteInfo]],
) -> list[PsychoEvent]:
    """Detect harmonic fusion (octave/unison/fifth with same onset)."""
    events = []
    valid = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    
    all_events = []
    for tname, notes in valid.items():
        for n in notes:
            # interval: [start - 0.02, start + 0.02]
            all_events.append((n.start - 0.02, 1, tname, id(n), n))
            all_events.append((n.start + 0.02, -1, tname, id(n), n))
            
    all_events.sort(key=lambda x: (x[0], x[1]))
    active_notes = {}

    for _, event_type, ta, na_id, na in all_events:
        if event_type == 1:
            for (tb, nb_id), nb in active_notes.items():
                if ta == tb:
                    continue
                
                if _is_fusion(na, nb):
                    events.append(
                        PsychoEvent(
                            beat=na.start,
                            track_a=ta,
                            note_a=na,
                            track_b=tb,
                            note_b=nb,
                            issue="fusion",
                            severity="mild",
                        )
                    )
            active_notes[(ta, na_id)] = na
        else:
            active_notes.pop((ta, na_id), None)
            
    return events


def detect_blur(
    tracks: dict[str, list[NoteInfo]],
    min_dur: float = _MIN_AUDIBLE_DURATION_120,
) -> list[PsychoEvent]:
    """[FIX 2] Detect notes shorter than the BPM-adaptive minimum audible duration."""
    events = []
    for tname, notes in tracks.items():
        for n in notes:
            if _is_blurry(n, min_dur):
                events.append(
                    PsychoEvent(
                        beat=n.start,
                        track_a=tname,
                        note_a=n,
                        track_b="",
                        note_b=None,
                        issue="blur",
                        severity="mild",
                    )
                )
    return events


def detect_register_masking(
    tracks: dict[str, list[NoteInfo]],
) -> list[PsychoEvent]:
    """Detect when bass and melody compete in the same low register."""
    import bisect
    events = []
    valid = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    names = list(valid.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ta, tb = names[i], names[j]
            notes_b = valid[tb]
            starts_b = [n.start for n in notes_b]
            for na in valid[ta]:
                lo = bisect.bisect_left(starts_b, na.start - na.duration)
                hi = bisect.bisect_right(starts_b, na.start + na.duration)
                for nb in notes_b[lo:hi]:
                    # Both in low register
                    if na.pitch >= _LOW_REGISTER or nb.pitch >= _LOW_REGISTER:
                        continue
                    # Overlap in time
                    if not (
                        na.start < nb.start + nb.duration and nb.start < na.start + na.duration
                    ):
                        continue
                    # Too close in pitch (< octave apart)
                    if abs(na.pitch - nb.pitch) < 12:
                        events.append(
                            PsychoEvent(
                                beat=na.start,
                                track_a=ta,
                                note_a=na,
                                track_b=tb,
                                note_b=nb,
                                issue="reg_mask",
                                severity="mild",
                            )
                        )
    return events


def detect_brightness_overload(
    tracks: dict[str, list[NoteInfo]],
) -> list[PsychoEvent]:
    """Detect when too many high-register notes play simultaneously (harsh)."""
    events = []
    valid = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}

    # Build grid of high-register note counts
    grid: dict[int, list[tuple[str, NoteInfo]]] = {}
    for tname, notes in valid.items():
        for n in notes:
            if n.pitch >= _HIGH_REGISTER:
                key = int(n.start * 4)
                if key not in grid:
                    grid[key] = []
                grid[key].append((tname, n))

    for key, entries in grid.items():
        if len(entries) >= 3:
            # Too many high notes at once — mark the quietest for removal
            entries.sort(key=lambda e: e[1].velocity)
            for tname, n in entries[: len(entries) - 2]:
                events.append(
                    PsychoEvent(
                        beat=n.start,
                        track_a=tname,
                        note_a=n,
                        track_b="",
                        note_b=None,
                        issue="brightness",
                        severity="mild",
                    )
                )
    return events


# ---------------------------------------------------------------------------
# Fix functions
# ---------------------------------------------------------------------------


def _reduce_vel(note: NoteInfo, factor: float = 0.5, min_velocity: int = 45) -> NoteInfo:
    return NoteInfo(
        pitch=note.pitch,
        start=note.start,
        duration=note.duration,
        velocity=max(min_velocity, min(note.velocity, int(note.velocity * factor))),
        articulation=note.articulation,
        expression=note.expression,
    )


def _shorten(note: NoteInfo, min_dur: float = 0.05) -> NoteInfo:
    return NoteInfo(
        pitch=note.pitch,
        start=note.start,
        duration=max(min_dur, note.duration),
        velocity=note.velocity,
        articulation=note.articulation,
        expression=note.expression,
    )


def _transpose_octave(note: NoteInfo) -> NoteInfo:
    for shift in [-12, 12]:
        new_pitch = note.pitch + shift
        if 0 <= new_pitch <= 127:
            return NoteInfo(
                pitch=new_pitch,
                start=note.start,
                duration=note.duration,
                velocity=note.velocity,
                articulation=note.articulation,
                expression=note.expression,
            )
    return note


# ---------------------------------------------------------------------------
# Main verifier
# ---------------------------------------------------------------------------


def psycho_verify(
    tracks: dict[str, list[NoteInfo]],
    config: PsychoConfig | None = None,
    bpm: float = 120.0,
    destructive: bool = False,
) -> tuple[dict[str, list[NoteInfo]], PsychoReport]:
    """
    Run psychoacoustic verification and fix detected issues.

    Parameters
    ----------
    tracks : dict
        Multi-track note dictionary.
    config : PsychoConfig, optional
        Detection and fix configuration.
    bpm : float
        Tempo in BPM — used to compute the BPM-adaptive blur threshold [FIX 2].
    destructive : bool
        If False (default), pitch transposition and note removal are prohibited —
        only velocity reductions and duration shortening are applied.
        If True, the original aggressive behaviour is restored.
    """
    if config is None:
        config = PsychoConfig()

    # [FIX 2] BPM-adaptive minimum audible duration
    min_dur = _min_audible_duration(bpm)

    report = PsychoReport()

    # Filter to NoteInfo tracks only
    note_tracks = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}

    # Phase 1: Detect all issues
    all_events = []
    if config.check_freq_masking:
        all_events.extend(detect_frequency_masking(note_tracks))
    if config.check_temporal_masking:
        all_events.extend(detect_temporal_masking(note_tracks))
    if config.check_fusion:
        all_events.extend(detect_fusion(note_tracks))
    if config.check_blur:
        all_events.extend(detect_blur(note_tracks, min_dur=min_dur))
    if config.check_register_masking:
        all_events.extend(detect_register_masking(note_tracks))
    if config.check_brightness:
        all_events.extend(detect_brightness_overload(note_tracks))

    report.issues_detected = len(all_events)
    report.events = all_events[:50]

    if not all_events:
        return {**tracks, **note_tracks}, report

    # Phase 2: Fix issues — mark-and-sweep to avoid index invalidation
    # Map (track, note_id) → action to apply
    _REMOVE = object()
    actions: dict[tuple[str, int], object] = {}  # (track_name, id(note)) → replacement NoteInfo or _REMOVE

    for evt in all_events:
        ta = evt.track_a
        tb = evt.track_b

        if evt.issue in ("freq_mask", "temporal_mask"):
            if evt.note_b and tb:
                if config.aggressive_fix and destructive:
                    actions[(tb, id(evt.note_b))] = _REMOVE
                    report.notes_removed += 1
                else:
                    actions[(tb, id(evt.note_b))] = _reduce_vel(evt.note_b, 0.75)
                    report.notes_velocity_reduced += 1
            report.issues_fixed += 1

        elif evt.issue == "fusion":
            if evt.note_b and tb:
                if destructive:
                    actions[(tb, id(evt.note_b))] = _transpose_octave(evt.note_b)
                    report.notes_transposed += 1
                else:
                    actions[(tb, id(evt.note_b))] = _reduce_vel(evt.note_b, 0.8)
                    report.notes_velocity_reduced += 1
                report.issues_fixed += 1

        elif evt.issue == "blur":
            actions[(ta, id(evt.note_a))] = _shorten(evt.note_a, 0.05)
            report.notes_shortened += 1
            report.issues_fixed += 1

        elif evt.issue == "reg_mask":
            if evt.note_b and tb:
                actions[(tb, id(evt.note_b))] = _reduce_vel(evt.note_b, 0.7)
                report.notes_velocity_reduced += 1
                report.issues_fixed += 1

        elif evt.issue == "brightness":
            if config.aggressive_fix and destructive:
                actions[(ta, id(evt.note_a))] = _REMOVE
                report.notes_removed += 1
            else:
                actions[(ta, id(evt.note_a))] = _reduce_vel(evt.note_a, 0.75)
                report.notes_velocity_reduced += 1
            report.issues_fixed += 1

    # Apply actions: single pass per track, no index corruption
    fixed = {}
    for tname, notes in note_tracks.items():
        result_notes = []
        for n in notes:
            key = (tname, id(n))
            if key in actions:
                action = actions[key]
                if action is _REMOVE:
                    continue  # drop note
                result_notes.append(action)  # replacement NoteInfo
            else:
                result_notes.append(n)
        fixed[tname] = result_notes

    # Re-sort
    from operator import attrgetter
    start_getter = attrgetter("start")
    for k in fixed:
        fixed[k].sort(key=start_getter)

    # Merge back non-note tracks
    result = {**tracks}
    for k, v in fixed.items():
        result[k] = v

    return result, report
