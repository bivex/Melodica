"""composer/melodic_transforms.py — Diatonic melodic transformations.

Applies classical contrapuntal transformations to any melody (list[NoteInfo]):
  inversion      — mirror intervals around pivot, staying diatonic
  retrograde     — reverse note order (crab motion)
  augmentation   — multiply all durations by factor
  diminution     — divide all durations by factor
  retrograde_inversion — retrograde then inversion (RI)
  transposition  — shift all pitches by N semitones
  sequence       — repeat melodic fragment at successive scale degrees

These are the diatonic equivalents of ToneRow P/I/R/RI operations,
applicable to any tonal melody regardless of 12-tone context.

Usage
-----
    from melodica.types import Scale, Mode, NoteInfo
    from melodica.composer.melodic_transforms import (
        inversion, retrograde, augmentation, diminution,
        retrograde_inversion, sequence
    )

    c_major = Scale(0, Mode.MAJOR)
    melody  = [NoteInfo(pitch=60+i, start=float(i), duration=1.0) for i in range(5)]

    inv  = inversion(melody, c_major)
    ret  = retrograde(melody)
    aug  = augmentation(melody, factor=2.0)
    dim  = diminution(melody, factor=2.0)
    seq  = sequence(melody, c_major, steps=3)
"""

from __future__ import annotations

import copy
from typing import Literal

from melodica.types import Scale, Mode
from melodica.types_pkg._notes import NoteInfo


# ---------------------------------------------------------------------------
# Scale degree helpers
# ---------------------------------------------------------------------------

_MODE_INTERVALS: dict[Mode, list[int]] = {
    Mode.MAJOR:          [0, 2, 4, 5, 7, 9, 11],
    Mode.NATURAL_MINOR:  [0, 2, 3, 5, 7, 8, 10],
    Mode.HARMONIC_MINOR: [0, 2, 3, 5, 7, 8, 11],
    Mode.MELODIC_MINOR:  [0, 2, 3, 5, 7, 9, 11],
    Mode.DORIAN:         [0, 2, 3, 5, 7, 9, 10],
    Mode.PHRYGIAN:       [0, 1, 3, 5, 7, 8, 10],
    Mode.LYDIAN:         [0, 2, 4, 6, 7, 9, 11],
    Mode.MIXOLYDIAN:     [0, 2, 4, 5, 7, 9, 10],
    Mode.LOCRIAN:        [0, 1, 3, 5, 6, 8, 10],
}


def _scale_pitches(scale: Scale, lo: int = 0, hi: int = 127) -> list[int]:
    """All MIDI pitches belonging to scale in [lo, hi]."""
    ivs = _MODE_INTERVALS.get(scale.mode, _MODE_INTERVALS[Mode.MAJOR])
    pcs = {(scale.root + i) % 12 for i in ivs}
    return [p for p in range(lo, hi + 1) if p % 12 in pcs]


def _nearest_scale_pitch(pitch: int, scale_pitches: list[int]) -> int:
    """Snap pitch to nearest scale pitch."""
    if not scale_pitches:
        return pitch
    return min(scale_pitches, key=lambda sp: abs(sp - pitch))


def _pitch_to_degree(pitch: int, scale: Scale) -> int:
    """Return the scale degree index (0-based) of a pitch, or -1 if not in scale."""
    ivs = _MODE_INTERVALS.get(scale.mode, _MODE_INTERVALS[Mode.MAJOR])
    pc  = pitch % 12
    root_pc = scale.root % 12
    for i, interval in enumerate(ivs):
        if (root_pc + interval) % 12 == pc:
            return i
    return -1


def _degree_to_pitch(degree: int, octave: int, scale: Scale) -> int:
    """Convert (scale degree, octave) to MIDI pitch."""
    ivs = _MODE_INTERVALS.get(scale.mode, _MODE_INTERVALS[Mode.MAJOR])
    n_degrees = len(ivs)
    extra_octaves, deg_idx = divmod(degree, n_degrees)
    semitone = ivs[deg_idx]
    return (octave + extra_octaves) * 12 + scale.root + semitone


def _copy_note(n: NoteInfo, **kwargs) -> NoteInfo:
    c = copy.copy(n)
    for k, v in kwargs.items():
        object.__setattr__(c, k, v)
    return c


# ---------------------------------------------------------------------------
# Core transformations
# ---------------------------------------------------------------------------

def inversion(
    notes: list[NoteInfo],
    scale: Scale,
    pivot_pitch: int | None = None,
) -> list[NoteInfo]:
    """Diatonic inversion: mirror all intervals around a pivot pitch.

    Intervals are measured and reflected in scale-degree space, so the
    result stays within the same key.

    Parameters
    ----------
    notes : list[NoteInfo]
        Original melody.
    scale : Scale
        Diatonic context for snapping inverted pitches.
    pivot_pitch : int | None
        Pivot MIDI pitch (default: first note's pitch).
    """
    if not notes:
        return []

    sp = _scale_pitches(scale)
    pivot = pivot_pitch if pivot_pitch is not None else notes[0].pitch

    result: list[NoteInfo] = []
    for n in notes:
        interval  = n.pitch - pivot
        inv_raw   = pivot - interval
        inv_pitch = _nearest_scale_pitch(max(0, min(127, inv_raw)), sp)
        result.append(_copy_note(n, pitch=inv_pitch))
    return result


def retrograde(notes: list[NoteInfo]) -> list[NoteInfo]:
    """Reverse note order, preserving total duration and onset spacing.

    The last note in the original becomes the first in the retrograde,
    with all timings recalculated so total duration is unchanged.
    """
    if not notes:
        return []
    total_end = max(n.start + n.duration for n in notes)
    result = []
    for n in reversed(notes):
        new_start = total_end - (n.start + n.duration)
        result.append(_copy_note(n, start=new_start))
    return sorted(result, key=lambda x: x.start)


def retrograde_inversion(
    notes: list[NoteInfo],
    scale: Scale,
    pivot_pitch: int | None = None,
) -> list[NoteInfo]:
    """Retrograde then inversion (RI) — both transformations combined."""
    return inversion(retrograde(notes), scale, pivot_pitch)


def augmentation(notes: list[NoteInfo], factor: float = 2.0) -> list[NoteInfo]:
    """Multiply all note durations and onset times by factor.

    factor=2.0 doubles all durations (classical augmentation).
    """
    if factor <= 0:
        raise ValueError(f"factor must be > 0, got {factor}")
    return [_copy_note(n, start=n.start * factor, duration=n.duration * factor)
            for n in notes]


def diminution(notes: list[NoteInfo], factor: float = 2.0) -> list[NoteInfo]:
    """Divide all note durations and onset times by factor.

    factor=2.0 halves all durations (classical diminution).
    """
    return augmentation(notes, 1.0 / factor)


def transposition(notes: list[NoteInfo], semitones: int) -> list[NoteInfo]:
    """Chromatic transposition by N semitones."""
    return [_copy_note(n, pitch=max(0, min(127, n.pitch + semitones)))
            for n in notes]


def diatonic_transposition(
    notes: list[NoteInfo],
    scale: Scale,
    degrees: int,
) -> list[NoteInfo]:
    """Transpose by N diatonic scale degrees (step-wise, stays in key).

    Parameters
    ----------
    degrees : int
        Number of scale steps to shift (positive = up, negative = down).
    """
    if not notes:
        return []
    sp = _scale_pitches(scale)

    result: list[NoteInfo] = []
    for n in notes:
        # Find nearest scale pitch index
        if not sp:
            result.append(copy.copy(n))
            continue
        idx = min(range(len(sp)), key=lambda i: abs(sp[i] - n.pitch))
        new_idx = max(0, min(len(sp) - 1, idx + degrees))
        result.append(_copy_note(n, pitch=sp[new_idx]))
    return result


def sequence(
    notes: list[NoteInfo],
    scale: Scale,
    steps: int = 3,
    step_size: int = -1,
    gap_beats: float = 0.0,
) -> list[NoteInfo]:
    """Repeat melodic fragment at successive diatonic degrees.

    Parameters
    ----------
    steps : int
        How many times to repeat the fragment (including original = steps+1 total).
    step_size : int
        Scale degrees to shift each repetition (default -1 = descending by step).
    gap_beats : float
        Extra silence between repetitions.
    """
    if not notes or steps < 1:
        return list(notes)

    fragment_duration = max(n.start + n.duration for n in notes) - notes[0].start
    result: list[NoteInfo] = list(notes)
    current_offset = fragment_duration + gap_beats
    cumulative_degrees = 0

    for _ in range(steps):
        cumulative_degrees += step_size
        shifted = diatonic_transposition(notes, scale, cumulative_degrees)
        # Re-time to follow previous fragment
        time_base = shifted[0].start if shifted else 0.0
        timed = [_copy_note(n, start=n.start - time_base + current_offset)
                 for n in shifted]
        result.extend(timed)
        current_offset += fragment_duration + gap_beats

    return result
