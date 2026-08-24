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
generators/_postprocess.py — Shared post-processing for generator classes.

Contains apply_phrase_arch, extracted from PianoRunGenerator, MelodyGenerator,
and other generators to reduce duplication (Multifaceted Abstraction smell).
"""

from __future__ import annotations

import math


def apply_phrase_arch(
    notes: list,
    duration_beats: float,
    phrase_position: float = 0.0,
    section_type=None,
) -> list:
    """Apply a sinusoidal velocity arch over the phrase duration.

    arch_height grows with phrase_position (0.0→1.0), producing a
    crescendo-shaped velocity contour peaking mid-phrase.
    When section_type is provided, uses section energy for arch height.
    """
    if not notes or duration_beats <= 0:
        return notes
    if section_type is not None:
        from melodica.types import SECTION_ROLE_ENERGY
        arch_height = SECTION_ROLE_ENERGY.get(section_type, 0.5) * 0.5
    else:
        arch_height = 0.3 + 0.2 * phrase_position
    for note in notes:
        progress = note.start / duration_beats
        arch = 1.0 - arch_height + arch_height * math.sin(progress * math.pi * 0.7)
        note.velocity = max(1, min(127, int(note.velocity * arch)))
    return notes


def _compute_slide_curve_value(interp: float, slide_curve: str, p1: int, p2: int) -> float:
    """Compute interpolated pitch curve progress between two pitches."""
    if slide_curve == "linear":
        return interp
    if slide_curve == "exponential":
        return interp ** 2.5
    if slide_curve == "logarithmic":
        return 1.0 - (1.0 - interp) ** 2.5
    if slide_curve == "octave_whip":
        diff = max(1, p2 - p1)
        whip_target = p2 + (12 if p2 >= p1 else -12)
        if interp < 0.3:
            t = interp / 0.3
            return (whip_target - p1) / diff * t
        t = (interp - 0.3) / 0.7
        current_pitch = whip_target + (p2 - whip_target) * (t ** 2.5)
        return (current_pitch - p1) / diff
    return interp


def _generate_808_pitch_slides(
    notes: list,
    duration_beats: float,
    slide_curve: str,
    low_pitch_bound: int,
) -> list:
    """Generate intermediate micro-pitch slide steps between consecutive 808 notes."""
    from melodica.types import NoteInfo

    notes.sort(key=lambda x: x.start)
    sub_notes = [n for n in notes if getattr(n, "articulation", None) == "808"]
    if len(sub_notes) <= 1:
        return []

    new_slides: list[NoteInfo] = []
    for idx in range(len(sub_notes) - 1):
        n1 = sub_notes[idx]
        n2 = sub_notes[idx + 1]

        if n2.start > n1.start and n2.start <= n1.start + n1.duration + 0.25 and n1.pitch != n2.pitch:
            slide_dur = 0.25
            slide_start = max(n1.start + 0.1, n2.start - slide_dur)
            slide_end = n2.start

            if slide_end > slide_start:
                n1.duration = round(slide_start - n1.start, 6)
                num_steps = 4
                step_dur = (slide_end - slide_start) / num_steps
                for k in range(num_steps):
                    step_onset = slide_start + k * step_dur
                    interp = (k + 1) / num_steps
                    curve_val = _compute_slide_curve_value(interp, slide_curve, n1.pitch, n2.pitch)
                    step_pitch = int(round(n1.pitch + (n2.pitch - n1.pitch) * curve_val))
                    step_pitch = max(0, min(127, step_pitch))

                    if 0 <= step_onset < duration_beats:
                        new_slides.append(
                            NoteInfo(
                                pitch=max(low_pitch_bound, step_pitch),
                                start=round(step_onset, 6),
                                duration=round(step_dur * 1.25, 6),
                                velocity=max(1, min(127, int(n1.velocity * 0.95))),
                                articulation="808",
                            )
                        )
    return new_slides


def _apply_transient_ducking(notes: list, ducking_duration: float) -> None:
    """Offset 808 attacks slightly when concurrent with kick drum to let transient pop."""
    kick_starts = {n.start for n in notes if n.pitch == 36 and getattr(n, "articulation", None) != "808"}
    for n in notes:
        if getattr(n, "articulation", None) == "808":
            if any(abs(n.start - k_start) < 0.01 for k_start in kick_starts):
                n.start = round(n.start + ducking_duration, 6)
                n.duration = round(max(0.05, n.duration - ducking_duration), 6)


def _apply_envelope_gating(notes: list, chords: list) -> None:
    """Choke 808 notes at chord boundaries or when next 808 hits to eliminate bass mud."""
    notes.sort(key=lambda x: x.start)
    chord_boundaries = [c.start for c in chords]
    for i, n in enumerate(notes):
        if getattr(n, "articulation", None) != "808":
            continue
        for cb in chord_boundaries:
            if cb > n.start and cb < n.start + n.duration:
                n.duration = round(cb - n.start - 0.01, 6)
                break
        for j in range(i + 1, len(notes)):
            next_n = notes[j]
            if getattr(next_n, "articulation", None) == "808" and next_n.start > n.start:
                if next_n.start < n.start + n.duration:
                    n.duration = round(next_n.start - n.start - 0.01, 6)
                break


def post_process_808(
    notes: list,
    chords: list,
    duration_beats: float,
    slide_curve: str = "exponential",
    transient_ducking: bool = True,
    ducking_duration: float = 0.02,
    envelope_gating: bool = True,
    low_pitch_bound: int = 24,
) -> list:
    """Supercharges 808 sub-bass with pitch slides, transient ducking, and envelope gating."""
    if not notes:
        return notes

    slides = _generate_808_pitch_slides(notes, duration_beats, slide_curve, low_pitch_bound)
    notes.extend(slides)

    if transient_ducking:
        _apply_transient_ducking(notes, ducking_duration)

    if envelope_gating:
        _apply_envelope_gating(notes, chords)

    return notes
