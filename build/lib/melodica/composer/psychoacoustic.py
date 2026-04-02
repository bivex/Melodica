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
_MIN_AUDIBLE_DURATION = 0.03  # 30ms — below this, notes blur together

# Velocity thresholds for masking
_MASKING_VELOCITY_DIFF = 20  # loud note must be this much louder to mask
_TEMPORAL_VELOCITY_DIFF = 30  # temporal masking needs bigger difference

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
    interval = abs(a.pitch - b.pitch) % 13  # 0-12
    return interval in _FUSION_INTERVALS


def _is_blurry(note: NoteInfo) -> bool:
    """Check if note is too short to be individually perceived."""
    return note.duration < _MIN_AUDIBLE_DURATION


def detect_frequency_masking(
    tracks: dict[str, list[NoteInfo]],
) -> list[PsychoEvent]:
    """Detect frequency masking across track pairs."""
    events = []
    valid = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    names = list(valid.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ta, tb = names[i], names[j]
            for na in valid[ta]:
                for nb in valid[tb]:
                    # Check overlap
                    if not (
                        na.start < nb.start + nb.duration and nb.start < na.start + na.duration
                    ):
                        continue

                    if _freq_masked(na, nb):
                        events.append(
                            PsychoEvent(
                                beat=nb.start,
                                track_a=ta,
                                note_a=na,
                                track_b=tb,
                                note_b=nb,
                                issue="freq_mask",
                                severity="strong",
                            )
                        )
                    elif _freq_masked(nb, na):
                        events.append(
                            PsychoEvent(
                                beat=na.start,
                                track_a=tb,
                                note_a=nb,
                                track_b=ta,
                                note_b=na,
                                issue="freq_mask",
                                severity="strong",
                            )
                        )
    return events


def detect_temporal_masking(
    tracks: dict[str, list[NoteInfo]],
) -> list[PsychoEvent]:
    """Detect temporal masking across track pairs."""
    events = []
    valid = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    names = list(valid.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ta, tb = names[i], names[j]
            for na in valid[ta]:
                for nb in valid[tb]:
                    if _temporal_masked(na, nb):
                        events.append(
                            PsychoEvent(
                                beat=nb.start,
                                track_a=ta,
                                note_a=na,
                                track_b=tb,
                                note_b=nb,
                                issue="temporal_mask",
                                severity="mild",
                            )
                        )
                    elif _temporal_masked(nb, na):
                        events.append(
                            PsychoEvent(
                                beat=na.start,
                                track_a=tb,
                                note_a=nb,
                                track_b=ta,
                                note_b=na,
                                issue="temporal_mask",
                                severity="mild",
                            )
                        )
    return events


def detect_fusion(
    tracks: dict[str, list[NoteInfo]],
) -> list[PsychoEvent]:
    """Detect harmonic fusion (octave/unison/fifth with same onset)."""
    events = []
    valid = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    names = list(valid.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ta, tb = names[i], names[j]
            for na in valid[ta]:
                for nb in valid[tb]:
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
    return events


def detect_blur(
    tracks: dict[str, list[NoteInfo]],
) -> list[PsychoEvent]:
    """Detect notes that are too short to perceive."""
    events = []
    for tname, notes in tracks.items():
        for n in notes:
            if _is_blurry(n):
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
    events = []
    valid = {k: v for k, v in tracks.items() if v and isinstance(v[0], NoteInfo)}
    names = list(valid.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ta, tb = names[i], names[j]
            for na in valid[ta]:
                for nb in valid[tb]:
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


def _reduce_vel(note: NoteInfo, factor: float = 0.5) -> NoteInfo:
    return NoteInfo(
        pitch=note.pitch,
        start=note.start,
        duration=note.duration,
        velocity=max(10, int(note.velocity * factor)),
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
) -> tuple[dict[str, list[NoteInfo]], PsychoReport]:
    """
    Run psychoacoustic verification and fix detected issues.
    """
    if config is None:
        config = PsychoConfig()

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
        all_events.extend(detect_blur(note_tracks))
    if config.check_register_masking:
        all_events.extend(detect_register_masking(note_tracks))
    if config.check_brightness:
        all_events.extend(detect_brightness_overload(note_tracks))

    report.issues_detected = len(all_events)
    report.events = all_events[:50]

    if not all_events:
        return {**tracks, **note_tracks}, report

    # Phase 2: Fix issues
    fixed = {k: list(v) for k, v in note_tracks.items()}

    # Build index for fast lookup
    note_idx: dict[tuple[str, int], int] = {}
    for tname, notes in note_tracks.items():
        for idx, n in enumerate(notes):
            note_idx[(tname, id(n))] = idx

    for evt in all_events:
        ta = evt.track_a
        tb = evt.track_b

        if evt.issue in ("freq_mask", "temporal_mask"):
            # Reduce velocity of masked (quiet) note — it's note_b in track_b
            if evt.note_b and tb and (tb, id(evt.note_b)) in note_idx:
                idx = note_idx[(tb, id(evt.note_b))]
                if config.aggressive_fix:
                    del fixed[tb][idx]
                    report.notes_removed += 1
                else:
                    fixed[tb][idx] = _reduce_vel(evt.note_b, 0.3)
                    report.notes_velocity_reduced += 1
                report.issues_fixed += 1

        elif evt.issue == "fusion":
            # Transpose one note to different octave
            tb = evt.track_b
            if evt.note_b and (tb, id(evt.note_b)) in note_idx:
                idx = note_idx[(tb, id(evt.note_b))]
                fixed[tb][idx] = _transpose_octave(evt.note_b)
                report.notes_transposed += 1
                report.issues_fixed += 1

        elif evt.issue == "blur":
            # Shorten to minimum audible duration
            if (ta, id(evt.note_a)) in note_idx:
                idx = note_idx[(ta, id(evt.note_a))]
                fixed[ta][idx] = _shorten(evt.note_a, 0.05)
                report.notes_shortened += 1
                report.issues_fixed += 1

        elif evt.issue == "reg_mask":
            # Reduce velocity of the quieter note
            tb = evt.track_b
            if evt.note_b and (tb, id(evt.note_b)) in note_idx:
                idx = note_idx[(tb, id(evt.note_b))]
                fixed[tb][idx] = _reduce_vel(evt.note_b, 0.4)
                report.notes_velocity_reduced += 1
                report.issues_fixed += 1

        elif evt.issue == "brightness":
            # Remove or reduce bright notes
            if (ta, id(evt.note_a)) in note_idx:
                idx = note_idx[(ta, id(evt.note_a))]
                if config.aggressive_fix:
                    del fixed[ta][idx]
                    report.notes_removed += 1
                else:
                    fixed[ta][idx] = _reduce_vel(evt.note_a, 0.3)
                    report.notes_velocity_reduced += 1
                report.issues_fixed += 1

    # Re-sort
    for k in fixed:
        fixed[k] = sorted(fixed[k], key=lambda n: n.start)

    # Merge back non-note tracks
    result = {**tracks}
    for k, v in fixed.items():
        result[k] = v

    return result, report
