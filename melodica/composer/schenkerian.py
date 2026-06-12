"""composer/schenkerian.py — Schenkerian-style melodic elaboration.

Adds passing tones and neighbour tones to an existing melody, mimicking
the Schenkerian foreground elaboration of a structural (middleground) line.

Three operations:
  passing_tones  — fill stepwise gaps between consecutive notes
  neighbour_tones — add upper/lower neighbours to sustained notes
  elaborate       — both, controlled by density

All functions return NEW note lists; originals are never mutated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import Scale


def _snap_to_scale(pitch: int, scale: Scale) -> int:
    """Snap a chromatic pitch to the nearest scale degree."""
    degs = scale.degrees()
    if not degs:
        return pitch
    pc = pitch % 12
    oct_ = pitch // 12
    best_pc = min(degs, key=lambda d: min(abs(int(round(d)) - pc), 12 - abs(int(round(d)) - pc)))
    return max(0, min(127, oct_ * 12 + int(round(best_pc))))


def _copy(n: NoteInfo, **kw) -> NoteInfo:
    return NoteInfo(
        pitch=kw.get("pitch", n.pitch),
        start=kw.get("start", n.start),
        duration=kw.get("duration", n.duration),
        velocity=kw.get("velocity", n.velocity),
        absolute=n.absolute,
        articulation=n.articulation,
        expression=dict(n.expression),
    )


def passing_tones(
    notes: list[NoteInfo],
    scale: Scale,
    *,
    min_gap_semitones: int = 3,
    passing_velocity_scale: float = 0.75,
    max_per_gap: int = 2,
) -> list[NoteInfo]:
    """Insert passing tones between notes separated by >= min_gap_semitones.

    For each pair of consecutive notes with a pitch gap, inserts 1–2 diatonic
    passing tones that fill the interval stepwise.  The passing notes are
    shorter than the structural notes and quieter.

    Parameters
    ----------
    notes : list[NoteInfo]
        Structural melody (sorted by start time).
    scale : Scale
        Scale for diatonic snapping.
    min_gap_semitones : int
        Minimum pitch gap to fill (default 3 = minor third).
    passing_velocity_scale : float
        Velocity multiplier for passing tones (default 0.75).
    max_per_gap : int
        Maximum passing tones per gap (default 2).

    Returns
    -------
    list[NoteInfo]
        Original notes interleaved with passing tones, sorted by start.
    """
    if len(notes) < 2:
        return list(notes)

    sorted_notes = sorted(notes, key=lambda n: n.start)
    result: list[NoteInfo] = []

    for i, n in enumerate(sorted_notes):
        result.append(n)
        if i + 1 >= len(sorted_notes):
            continue

        nxt = sorted_notes[i + 1]
        gap = nxt.pitch - n.pitch
        if abs(gap) < min_gap_semitones:
            continue

        # Time available for passing tones
        # Use the gap between end of current note and start of next,
        # OR borrow from the tail of the current note if notes are adjacent.
        note_end = n.start + n.duration
        time_gap = nxt.start - note_end
        borrowed = False
        if time_gap < 0.05:
            # Notes are adjacent — borrow last fraction of current note
            borrow = min(n.duration * 0.4, 0.8)
            time_gap = borrow
            borrowed = True

        # Number of passing tones: 1 for 3rd, 2 for larger
        n_pass = min(max_per_gap, abs(gap) // 2)
        if n_pass == 0:
            continue

        step = gap / (n_pass + 1)
        t_step = time_gap / (n_pass + 1)
        pass_dur = min(t_step * 0.85, n.duration * 0.5)
        vel = max(1, int(n.velocity * passing_velocity_scale))

        pass_start = (note_end - time_gap) if borrowed else note_end

        for j in range(1, n_pass + 1):
            raw_pitch = int(round(n.pitch + step * j))
            p = _snap_to_scale(raw_pitch, scale)
            t = pass_start + (j - 1) * t_step
            result.append(NoteInfo(
                pitch=p,
                start=round(t, 6),
                duration=round(pass_dur, 6),
                velocity=vel,
            ))

    result.sort(key=lambda n: n.start)
    return result


def neighbour_tones(
    notes: list[NoteInfo],
    scale: Scale,
    *,
    min_duration: float = 1.5,
    upper: bool = True,
    lower: bool = False,
    neighbour_velocity_scale: float = 0.70,
    neighbour_dur_fraction: float = 0.30,
) -> list[NoteInfo]:
    """Add upper/lower neighbour tones to sustained structural notes.

    A neighbour tone is a brief ornamental note one scale step above or below
    a structural note, inserted at the midpoint of long notes.

    Parameters
    ----------
    notes : list[NoteInfo]
        Structural melody.
    scale : Scale
        Scale for diatonic step calculation.
    min_duration : float
        Minimum note duration to ornament (default 1.5 beats).
    upper : bool
        Add upper neighbours (default True).
    lower : bool
        Add lower neighbours (default False).
    neighbour_velocity_scale : float
        Velocity of neighbour tone relative to structural note.
    neighbour_dur_fraction : float
        Fraction of structural note duration used for the neighbour tone.

    Returns
    -------
    list[NoteInfo]
        Original notes with neighbour tones inserted, sorted by start.
    """
    degs = scale.degrees()
    if not degs:
        return list(notes)

    def _step_above(pitch: int) -> int:
        pc = pitch % 12
        oct_ = pitch // 12
        above = [int(round(d)) for d in degs if int(round(d)) > pc]
        if above:
            return oct_ * 12 + above[0]
        return (oct_ + 1) * 12 + int(round(degs[0]))

    def _step_below(pitch: int) -> int:
        pc = pitch % 12
        oct_ = pitch // 12
        below = [int(round(d)) for d in reversed(degs) if int(round(d)) < pc]
        if below:
            return oct_ * 12 + below[0]
        return (oct_ - 1) * 12 + int(round(degs[-1]))

    result: list[NoteInfo] = []
    for n in notes:
        if n.duration < min_duration:
            result.append(n)
            continue

        nb_dur = round(n.duration * neighbour_dur_fraction, 6)
        nb_vel = max(1, int(n.velocity * neighbour_velocity_scale))
        # Structural note shortened to make room
        struct_dur = round(n.duration - nb_dur, 6)
        result.append(_copy(n, duration=struct_dur))

        nb_start = round(n.start + struct_dur, 6)
        if upper:
            up = min(127, _step_above(n.pitch))
            result.append(NoteInfo(pitch=up, start=nb_start, duration=nb_dur, velocity=nb_vel))
        if lower:
            lo = max(0, _step_below(n.pitch))
            result.append(NoteInfo(pitch=lo, start=nb_start, duration=nb_dur, velocity=nb_vel))

    result.sort(key=lambda n: n.start)
    return result


def elaborate(
    notes: list[NoteInfo],
    scale: Scale,
    *,
    density: float = 0.5,
    passing: bool = True,
    neighbours: bool = True,
) -> list[NoteInfo]:
    """Full Schenkerian foreground elaboration.

    Applies passing tones and/or neighbour tones controlled by *density*.

    Parameters
    ----------
    notes : list[NoteInfo]
        Structural melody.
    scale : Scale
        Target scale.
    density : float
        0.0 = no elaboration, 1.0 = maximum elaboration.
        Controls min_gap_semitones (lower = more passing tones) and
        min_duration (lower = more neighbour tones).
    passing : bool
        Apply passing tone elaboration (default True).
    neighbours : bool
        Apply neighbour tone elaboration (default True).

    Returns
    -------
    list[NoteInfo]
        Elaborated melody.
    """
    density = max(0.0, min(1.0, density))
    result = list(notes)

    if passing:
        # density 0=fills every 2nd, 1=only fills 5ths+
        min_gap = max(2, int(2 + (1 - density) * 4))
        result = passing_tones(result, scale, min_gap_semitones=min_gap)

    if neighbours:
        # density 0=ornaments quarter notes+, 1=only whole notes+
        min_dur = max(0.5, 0.5 + (1.0 - density) * 2.5)
        result = neighbour_tones(result, scale, min_duration=min_dur)

    return result
