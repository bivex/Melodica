# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.generate.kernel — Common algorithmic kernel functions for phrase generation.

Consolidates shared logic (density thinning, pitch resolution, polyphony limiting,
LFO curves, dynamic curves, range folding) previously duplicated across generator classes.
"""

from __future__ import annotations

import math
from typing import Sequence

from melodica.generators.density import DensityStrategy
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import resolve_scale_pitch


def apply_note_density(chords: Sequence[ChordLabel], note_density: float = 1.0) -> list[ChordLabel]:
    """
    Apply musical density thinning or subdivision to a chord sequence.
    Unifies _apply_note_density across all generators.
    """
    return DensityStrategy.apply(list(chords), note_density)


def resolve_bounded_pitch(pc: int, anchor: int, key: Scale, low: int, high: int) -> int:
    """
    Resolve pitch-class `pc` to nearest octave around `anchor`, constrained to [low, high].
    Unifies _resolve_pitch across all generators.
    """
    return resolve_scale_pitch(pc, anchor, key, low, high)


def fit_to_range(pitch: int, low: int, high: int) -> int:
    """
    Fold a pitch octave by octave until it fits within [low, high].
    """
    if low >= high:
        return low
    while pitch < low:
        pitch += 12
    while pitch > high:
        pitch -= 12
    return max(low, min(high, pitch))


def generate_lfo_cc(
    duration: float,
    hz: float,
    base: int = 85,
    depth: int = 15,
    step: float = 0.05,
) -> list[tuple[float, int]]:
    """
    Generate sinusoidal LFO automation points for CC expressions (tremolo, vibrato, sweeps).
    Returns a list of (beat_offset, cc_value) tuples.
    """
    if duration <= 0 or hz <= 0:
        return []
    points: list[tuple[float, int]] = []
    t = 0.0
    two_pi_f = 2.0 * math.pi * hz
    while t < duration:
        val = int(base + depth * math.sin(t * two_pi_f))
        points.append((round(t, 4), max(0, min(127, val))))
        t += step
    return points


def limit_polyphony(notes: Sequence[NoteInfo], max_polyphony: int) -> list[NoteInfo]:
    """
    Ensure no more than `max_polyphony` notes sound simultaneously at any moment.
    When exceeding the limit, notes with lower velocities are culled.
    """
    if max_polyphony <= 0 or not notes:
        return []

    sorted_notes = sorted(notes, key=lambda n: (n.start, -n.velocity))
    active: list[NoteInfo] = []
    result: list[NoteInfo] = []

    for note in sorted_notes:
        # Remove ended notes
        active = [n for n in active if (n.start + n.duration) > note.start + 1e-5]
        if len(active) < max_polyphony:
            active.append(note)
            result.append(note)
        else:
            # Drop lowest velocity note if new note is louder, or drop new note
            active.sort(key=lambda n: n.velocity)
            if note.velocity > active[0].velocity:
                dropped = active.pop(0)
                if dropped in result:
                    result.remove(dropped)
                active.append(note)
                result.append(note)

    return sorted(result, key=lambda n: n.start)


def apply_phrase_arch(notes: Sequence[NoteInfo], arch_strength: float = 0.2) -> list[NoteInfo]:
    """
    Apply a parabolic musical dynamics arch (crescendo to phrase center, diminuendo to end)
    to a sequence of notes.
    """
    if not notes or arch_strength <= 0:
        return list(notes)

    start_time = min(n.start for n in notes)
    end_time = max(n.start + n.duration for n in notes)
    total_dur = end_time - start_time
    if total_dur <= 0:
        return list(notes)

    modified: list[NoteInfo] = []
    for n in notes:
        mid_rel = (n.start + 0.5 * n.duration - start_time) / total_dur
        # Parabola peaked at 0.5: 4 * x * (1 - x), equals 1.0 at center, 0.0 at ends
        arch_factor = 4.0 * mid_rel * (1.0 - mid_rel)
        vel_delta = int(n.velocity * arch_strength * (arch_factor - 0.5) * 2.0)
        new_vel = max(1, min(127, n.velocity + vel_delta))
        
        # Preserve all other properties
        new_note = NoteInfo(
            pitch=n.pitch,
            start=n.start,
            duration=n.duration,
            velocity=new_vel,
            absolute=n.absolute,
            articulation=n.articulation,
            expression=dict(n.expression) if n.expression else None,
        )
        modified.append(new_note)

    return modified


def apply_dynamic_curve(vel: int, progress: float, curve: str, base: int) -> int:
    """
    Calculate curved dynamic velocity progression across phrase progress [0.0, 1.0].
    """
    p = max(0.0, min(1.0, progress))
    if curve == "crescendo":
        v = int(base + p * 30)
    elif curve == "decrescendo":
        v = int(base + (1.0 - p) * 30)
    elif curve == "swell":
        v = int(base + 20 * (1.0 - abs(2.0 * p - 1.0)))
    elif curve == "diminuendo":
        v = int(base + 15 * max(0.0, 1.0 - p * 1.5))
    else:
        v = vel
    return max(1, min(127, v))
