# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b-top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
composer/transformers.py — Melodic transformers for ornamentation and embellishment.

Ported from canon-generator (algorithmic composition toolkit).
Each transformer takes one or two notes and returns a list of notes
with added musical ornamentation (neighbor tones, passing tones, cambiata).

These are NOT neural network Transformers — they are rule-based musical
transformation classes that apply counterpoint ornaments algorithmically.

Transformers:
    Identity      — pass-through (no change)
    OneToThree    — neighbor tone ornamentation (1 note -> 3)
    TwoToThree    — passing tone insertion (2 notes -> 3)
    TwoToFour     — cambiata figure (2 notes -> 4)
    spiceup       — apply random transformers to a sequence with configurable depth
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass

from melodica.types import NoteInfo, Scale


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _next_scale_pitch(pitch: int, scale: Scale, direction: str) -> int:
    """Return the next pitch in the given scale direction, staying within MIDI range."""
    degs = [int(d) for d in scale.degrees()]
    pc = pitch % 12
    octave = pitch // 12

    if direction == "ascending":
        for i, d in enumerate(degs):
            if d > pc:
                candidate = octave * 12 + d
                return max(0, min(127, candidate))
        # wrap to next octave
        candidate = (octave + 1) * 12 + degs[0]
        return max(0, min(127, candidate))
    else:
        for i in range(len(degs) - 1, -1, -1):
            if degs[i] < pc:
                candidate = octave * 12 + degs[i]
                return max(0, min(127, candidate))
        candidate = (octave - 1) * 12 + degs[-1]
        return max(0, min(127, candidate))


def _scale_pitches_between(low: int, high: int, scale: Scale) -> list[int]:
    """Return all scale pitches between low and high (inclusive)."""
    degs = [int(d) for d in scale.degrees()]
    lo_oct = low // 12
    hi_oct = high // 12
    result = []
    for oct_idx in range(lo_oct - 1, hi_oct + 2):
        for d in degs:
            p = oct_idx * 12 + d
            if low <= p <= high:
                result.append(p)
    result.sort()
    return result


def _median_pitch(pitches: list[int], prefer_upper: bool = False) -> int:
    """Return the median pitch from a sorted list."""
    n = len(pitches)
    if n == 0:
        return 60
    if n == 1:
        return pitches[0]
    if n % 2 == 1:
        return pitches[n // 2]
    return pitches[n // 2] if prefer_upper else pitches[(n - 1) // 2]


# ---------------------------------------------------------------------------
# Transformer base
# ---------------------------------------------------------------------------

class NoteTransformer:
    """Base class for melodic transformers."""

    def transform(self, scale: Scale, note: NoteInfo, next_note: NoteInfo | None = None) -> list[NoteInfo]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Transformers
# ---------------------------------------------------------------------------

class Identity(NoteTransformer):
    """Pass-through: returns the note unchanged."""

    def transform(self, scale: Scale, note: NoteInfo, next_note: NoteInfo | None = None) -> list[NoteInfo]:
        return [NoteInfo(
            pitch=note.pitch,
            start=note.start,
            duration=note.duration,
            velocity=note.velocity,
        )]


class OneToThree(NoteTransformer):
    """
    Neighbor tone ornamentation: 1 note -> 3 notes.
    Keeps total duration. First and last = original pitch.
    Middle note is a scale neighbor above or below.
    """

    def transform(self, scale: Scale, note: NoteInfo, next_note: NoteInfo | None = None) -> list[NoteInfo]:
        duration_splits = [
            [0.5, 0.25, 0.25],
            [0.25, 0.5, 0.25],
            [0.25, 0.25, 0.5],
        ]
        chosen = random.choice(duration_splits)
        direction = random.choice(["ascending", "descending"])
        total_dur = note.duration

        n1 = NoteInfo(
            pitch=note.pitch,
            start=note.start,
            duration=round(chosen[0] * total_dur, 6),
            velocity=note.velocity,
        )
        neighbor_pitch = _next_scale_pitch(note.pitch, scale, direction)
        n2 = NoteInfo(
            pitch=neighbor_pitch,
            start=round(note.start + n1.duration, 6),
            duration=round(chosen[1] * total_dur, 6),
            velocity=max(1, min(127, note.velocity - 5)),
        )
        n3 = NoteInfo(
            pitch=note.pitch,
            start=round(n2.start + n2.duration, 6),
            duration=round(chosen[2] * total_dur, 6),
            velocity=note.velocity,
        )
        return [n1, n2, n3]


class TwoToThree(NoteTransformer):
    """
    Passing tone insertion: interpolates a scale pitch between two notes.
    Total duration of note1 is split between the original and the passing tone.
    """

    def transform(self, scale: Scale, note1: NoteInfo, next_note: NoteInfo | None = None) -> list[NoteInfo]:
        if next_note is None:
            return [NoteInfo(
                pitch=note1.pitch, start=note1.start,
                duration=note1.duration, velocity=note1.velocity,
            )]

        duration_splits = [
            [0.5, 0.5],
            [0.75, 0.25],
        ]
        chosen = random.choice(duration_splits)
        prefer_upper = random.choice([True, False])
        total_dur = note1.duration

        pitches_between = _scale_pitches_between(
            min(note1.pitch, next_note.pitch),
            max(note1.pitch, next_note.pitch),
            scale,
        )
        if len(pitches_between) >= 2:
            # exclude the endpoints
            inner = pitches_between[1:-1]
            interp = _median_pitch(inner, prefer_upper) if inner else note1.pitch
        else:
            interp = _next_scale_pitch(note1.pitch, scale, "ascending")

        n1 = NoteInfo(
            pitch=note1.pitch,
            start=note1.start,
            duration=round(chosen[0] * total_dur, 6),
            velocity=note1.velocity,
        )
        n2 = NoteInfo(
            pitch=interp,
            start=round(note1.start + n1.duration, 6),
            duration=round(chosen[1] * total_dur, 6),
            velocity=max(1, min(127, note1.velocity - 3)),
        )
        return [n1, n2]


class TwoToFour(NoteTransformer):
    """
    Cambiata figure: 2 notes -> 4 notes.
    Takes note1's duration and splits it into 3 segments that oscillate
    around the next note's pitch (upper neighbor, lower neighbor).
    """

    def transform(self, scale: Scale, note1: NoteInfo, next_note: NoteInfo | None = None) -> list[NoteInfo]:
        if next_note is None:
            return [NoteInfo(
                pitch=note1.pitch, start=note1.start,
                duration=note1.duration, velocity=note1.velocity,
            )]

        duration_splits = [
            [0.5, 0.25, 0.25],
            [0.25, 0.5, 0.25],
        ]
        chosen = random.choice(duration_splits)
        direction = random.choice(["ascending", "descending"])
        other_dir = "descending" if direction == "ascending" else "ascending"
        total_dur = note1.duration

        n1 = NoteInfo(
            pitch=note1.pitch,
            start=note1.start,
            duration=round(chosen[0] * total_dur, 6),
            velocity=note1.velocity,
        )
        upper = _next_scale_pitch(next_note.pitch, scale, direction)
        n2 = NoteInfo(
            pitch=upper,
            start=round(note1.start + n1.duration, 6),
            duration=round(chosen[1] * total_dur, 6),
            velocity=max(1, min(127, note1.velocity - 5)),
        )
        lower = _next_scale_pitch(next_note.pitch, scale, other_dir)
        n3 = NoteInfo(
            pitch=lower,
            start=round(n2.start + n2.duration, 6),
            duration=round(chosen[2] * total_dur, 6),
            velocity=max(1, min(127, note1.velocity - 3)),
        )
        return [n1, n2, n3]


# ---------------------------------------------------------------------------
# Transformer pools (Identity weighted higher to avoid over-ornamentation)
# ---------------------------------------------------------------------------

SINGLE_NOTE_TRANSFORMERS: list[type[NoteTransformer]] = [
    Identity, Identity,
    OneToThree,
]

DOUBLE_NOTE_TRANSFORMERS: list[type[NoteTransformer]] = [
    Identity, Identity,
    TwoToThree,
    TwoToFour,
]


# ---------------------------------------------------------------------------
# Spice-up pipeline
# ---------------------------------------------------------------------------

def spiceup(
    notes: list[NoteInfo],
    scale: Scale,
    depth: int = 1,
    single_pool: list[type[NoteTransformer]] | None = None,
    double_pool: list[type[NoteTransformer]] | None = None,
) -> list[NoteInfo]:
    """
    Apply random melodic transformers to a sequence of notes.

    depth: number of iterative passes (each pass makes the melody more ornate).
    single_pool: transformers that look at one note only.
    double_pool: transformers that look at current + next note.
    """
    if not notes:
        return []

    singles = single_pool or SINGLE_NOTE_TRANSFORMERS
    doubles = double_pool or DOUBLE_NOTE_TRANSFORMERS

    current = list(notes)

    for _ in range(depth):
        result: list[NoteInfo] = []
        # Build pairs: (note, next_note_or_None)
        for i, note in enumerate(current):
            next_note = current[i + 1] if i + 1 < len(current) else None

            # 50/50: single-note vs double-note transformer
            if random.random() < 0.5:
                trafo = random.choice(singles)()
                transformed = trafo.transform(scale, note)
            else:
                trafo = random.choice(doubles)()
                transformed = trafo.transform(scale, note, next_note)

            result.extend(transformed)
        current = result

    return current


def serialize_canon(
    voices: list[list[NoteInfo]],
    delay_beats: float,
    transpositions: list[int] | None = None,
    duration_beats: float | None = None,
) -> list[NoteInfo]:
    """
    Create a canon from multiple voices by offsetting each voice in time.

    voices: list of voice note sequences (voice[0] = lead)
    delay_beats: time offset between each successive voice
    transpositions: semitone offset per voice (default: all 0)
    duration_beats: total duration cap (default: auto from voices)
    """
    if not voices:
        return []

    transpositions = transpositions or [0] * len(voices)
    all_notes: list[NoteInfo] = []

    for v_idx, voice in enumerate(voices):
        offset = v_idx * delay_beats
        shift = transpositions[v_idx] if v_idx < len(transpositions) else 0

        for note in voice:
            new_start = note.start + offset
            if duration_beats is not None and new_start >= duration_beats:
                break
            pitch = max(0, min(127, note.pitch + shift))
            dur = note.duration
            if duration_beats is not None and new_start + dur > duration_beats:
                dur = duration_beats - new_start
            if dur <= 0:
                continue
            all_notes.append(NoteInfo(
                pitch=pitch,
                start=round(new_start, 6),
                duration=round(dur, 6),
                velocity=note.velocity,
            ))

    all_notes.sort(key=lambda n: (n.start, n.pitch))
    return all_notes
