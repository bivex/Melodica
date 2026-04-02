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
utils.py — Pure pitch-class arithmetic helpers.

Layer: Domain support
Rules:
  - All functions are pure (no side effects, no I/O).
  - No imports from engines, detectors, or infrastructure.
"""

from __future__ import annotations

from melodica.types import ChordLabel, NoteInfo, Quality, Scale


# ---------------------------------------------------------------------------
# Pitch-class arithmetic
# ---------------------------------------------------------------------------


def pitch_class(midi_pitch: int) -> int:
    """MIDI pitch → pitch class 0–11."""
    return midi_pitch % 12


def semitones_up(midi_pitch: int, semitones: int) -> int:
    """Transpose a MIDI pitch up by N semitones, clamped to 0–127."""
    return max(0, min(127, midi_pitch + semitones))


def interval_class(a: int, b: int) -> int:
    """
    Smallest interval between two pitch classes (0–6).
    Invariant: interval_class(a, b) == interval_class(b, a).
    """
    diff = abs(a - b) % 12
    return min(diff, 12 - diff)


def ascending_interval(from_pc: int, to_pc: int) -> int:
    """Semitones to go UP from from_pc to to_pc (0–11)."""
    return (to_pc - from_pc) % 12


def descending_interval(from_pc: int, to_pc: int) -> int:
    """Semitones to go DOWN from from_pc to to_pc (1–12)."""
    asc = ascending_interval(from_pc, to_pc)
    return 12 - asc if asc != 0 else 0


def nearest_pitch_above(pc: int, reference_midi: int) -> int:
    """
    Lowest MIDI pitch with pitch class `pc` that is >= reference_midi.
    Useful for voice-leading calculations.
    """
    base = (reference_midi // 12) * 12 + pc
    if base < reference_midi:
        base += 12
    return min(base, 127)


def nearest_pitch_below(pc: int, reference_midi: int) -> int:
    """
    Highest MIDI pitch with pitch class `pc` that is <= reference_midi.
    """
    base = (reference_midi // 12) * 12 + pc
    if base > reference_midi:
        base -= 12
    return max(0, base)


def nearest_pitch(pc: int, reference_midi: int) -> int:
    """
    MIDI pitch with pitch class `pc` closest to reference_midi.
    Ties broken upward.
    """
    above = nearest_pitch_above(pc, reference_midi)
    below = nearest_pitch_below(pc, reference_midi)
    if abs(above - reference_midi) <= abs(reference_midi - below):
        return above
    return below


# ---------------------------------------------------------------------------
# Chord voicing helpers
# ---------------------------------------------------------------------------


def chord_pitches_closed(
    chord: ChordLabel,
    bass_midi: int = 48,
) -> list[int]:
    """
    Build a closed-position voicing starting from bass_midi.
    Returns a list of MIDI pitches in ascending order.
    """
    pcs = chord.pitch_classes()
    # Determine bass pitch class: use inversion to find lowest note
    bass_pc = pcs[chord.inversion % len(pcs)]
    bass = nearest_pitch_above(bass_pc, bass_midi)
    voicing: list[int] = [bass]
    for pc in pcs:
        if pc == bass_pc:
            continue
        voicing.append(nearest_pitch_above(pc, bass))
    return sorted(voicing)


def chord_pitches_open(
    chord: ChordLabel,
    bass_midi: int = 36,
) -> list[int]:
    """
    Build an open-position voicing (alternate tones spread an octave apart).
    """
    closed = chord_pitches_closed(chord, bass_midi)
    if len(closed) < 3:
        return closed
    # Drop every other upper voice down an octave to open up the voicing
    result = [closed[0]]
    for i, p in enumerate(closed[1:], 1):
        result.append(p if i % 2 == 0 else p + 12)
    return sorted(result)


def chord_pitches_spread(
    chord: ChordLabel,
    bass_midi: int = 36,
    spread_semitones: int = 24,
) -> list[int]:
    """
    Build a spread voicing distributing notes across up to `spread_semitones`.
    """
    pcs = chord.pitch_classes()
    n = len(pcs)
    if n == 0:
        return []
    step = spread_semitones // max(n - 1, 1)
    result = []
    base = nearest_pitch_above(pcs[0], bass_midi)
    for i, pc in enumerate(pcs):
        result.append(nearest_pitch_above(pc, base + i * step))
    return sorted(result)


# ---------------------------------------------------------------------------
# Voice-leading distance
# ---------------------------------------------------------------------------


def voice_leading_distance(
    prev_pitches: list[int],
    next_pitches: list[int],
) -> float:
    """
    Sum of |next_pitch - nearest_prev_pitch| for every note in next_pitches.
    Modeled after inversion-minimizing note distance logic.
    """
    if not prev_pitches:
        return 0.0
    total = 0.0
    for np_ in next_pitches:
        nearest = min(prev_pitches, key=lambda pp: abs(np_ - pp))
        total += abs(np_ - nearest)
    return total


# ---------------------------------------------------------------------------
# Scale / pitch-class membership
# ---------------------------------------------------------------------------


def pitch_classes_in_window(
    notes: list[NoteInfo],
    start: float,
    end: float,
) -> set[int]:
    """Collect pitch classes of notes active (overlapping) in [start, end)."""
    return {
        pitch_class(n.pitch)
        for n in notes
        if n.start < end and (n.start + n.duration) > start
    }


def diatonic_transpose(
    note_info: NoteInfo,
    from_key: Scale,
    to_key: Scale,
) -> NoteInfo:
    """
    Transpose a relative NoteInfo from one key to another diatonically.
    Absolute notes are returned unchanged.
    """
    if note_info.absolute:
        return note_info
    # Find degree in from_key and rebuild pitch in to_key
    from_degs = from_key.degrees()
    to_degs = to_key.degrees()
    pc = pitch_class(note_info.pitch)
    octave = note_info.pitch // 12
    try:
        deg_idx = from_degs.index(pc)
        new_pc = to_degs[deg_idx % len(to_degs)]
        new_pitch = octave * 12 + new_pc
    except ValueError:
        # Chromatic note: transpose by root interval
        root_diff = (to_key.root - from_key.root) % 12
        new_pitch = semitones_up(note_info.pitch, root_diff)

    return NoteInfo(
        pitch=max(0, min(127, new_pitch)),
        start=note_info.start,
        duration=note_info.duration,
        velocity=note_info.velocity,
        absolute=note_info.absolute,
    )


def is_scale_tone(pitch: int, scale: Scale) -> bool:
    """Check if a MIDI pitch belongs to the given scale."""
    return scale.contains(pitch % 12)


# ---------------------------------------------------------------------------
# Chord lookup (shared across generators)
# ---------------------------------------------------------------------------


def chord_at(chords: list[ChordLabel], beat: float) -> ChordLabel | None:
    """Return the chord active at the given beat position, or None if empty."""
    for c in reversed(chords):
        if c.start <= beat:
            return c
    return chords[0] if chords else None


# ---------------------------------------------------------------------------
# Guitar voicing builder (shared across fingerpicking / strum)
# ---------------------------------------------------------------------------


def build_guitar_voicing(
    chord: ChordLabel,
    anchor: int = 40,
    min_voices: int = 4,
) -> list[int]:
    """
    Create a guitar-like open voicing suitable for fingerpicking / strumming.
    Walks upward from the bass pitch, matching each chord pitch class with
    minimum separation of 3 semitones between voices.
    Pads with octave doublings to reach ``min_voices``.
    """
    bass_pc = chord.bass if chord.bass is not None else chord.root
    bass_pitch = anchor
    while (bass_pitch % 12) != bass_pc:
        bass_pitch += 1
        if bass_pitch > 55:
            bass_pitch -= 12

    pcs = chord.pitch_classes()
    if bass_pc in pcs:
        pcs = [pc for pc in pcs if pc != bass_pc]

    pitches = [bass_pitch]
    cur_pitch = bass_pitch + 7

    for pc in pcs:
        while (cur_pitch % 12) != pc:
            cur_pitch += 1
        pitches.append(cur_pitch)
        cur_pitch += 3

    while len(pitches) < min_voices:
        pitches.append(pitches[-1] + 12)

    return sorted(set(pitches))


# ---------------------------------------------------------------------------
# Simplicity scoring (used by AdaptiveEngine — defined here so it's pure)
# ---------------------------------------------------------------------------

EXTENSION_PENALTIES: dict[int, float] = {
    1: 0.9,   # minor 2nd / major 7th
    2: 0.4,   # major 2nd (mild)
    6: 0.8,   # tritone
    10: 0.2,  # minor 7th (common)
    11: 0.3,  # major 7th
}


def compute_simplicity(chord: ChordLabel) -> float:
    """
    Simplicity score ∈ [0, 1].
    1.0 = pure triad, decreases with extensions.
    Pure function — no side effects.
    """
    template = [0, 4, 7]  # major triad shape as baseline
    from melodica.types import CHORD_TEMPLATES
    template = CHORD_TEMPLATES.get(chord.quality, [0, 4, 7])
    triad_size = min(3, len(template))

    score = 1.0
    extra_tones = list(template[triad_size:]) + list(chord.extensions)
    for i, ivl in enumerate(extra_tones):
        ic = ivl % 12
        penalty = EXTENSION_PENALTIES.get(ic, 0.15)
        score -= penalty
        if i > 0:
            score -= 0.1  # extra penalty per additional extension
    return max(0.0, min(1.0, score))
