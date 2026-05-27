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
    """
    Supercharges 808 sub-bass with:
      - Non-linear pitch slide curves (linear, exponential, logarithmic, octave_whip).
      - Transient Ducking Gate (chokes/shifts attack by ~20ms when concurrent with kick to let transient pop).
      - Envelope Gating (chokes 808 when next chord begins or next 808 hits to eliminate mud).
    """
    if not notes:
        return notes

    # 1. 808 Slide Processor
    notes.sort(key=lambda x: x.start)
    sub_notes = [n for n in notes if getattr(n, "articulation", None) == "808"]
    if len(sub_notes) > 1:
        new_slides = []
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
                        
                        if slide_curve == "linear":
                            curve_val = interp
                        elif slide_curve == "exponential":
                            curve_val = interp ** 2.5
                        elif slide_curve == "logarithmic":
                            curve_val = 1.0 - (1.0 - interp) ** 2.5
                        elif slide_curve == "octave_whip":
                            if interp < 0.3:
                                whip_target = n2.pitch + (12 if n2.pitch >= n1.pitch else -12)
                                t = interp / 0.3
                                curve_val = (whip_target - n1.pitch) / max(1, n2.pitch - n1.pitch) * t
                            else:
                                whip_target = n2.pitch + (12 if n2.pitch >= n1.pitch else -12)
                                t = (interp - 0.3) / 0.7
                                current_pitch = whip_target + (n2.pitch - whip_target) * (t ** 2.5)
                                curve_val = (current_pitch - n1.pitch) / max(1, n2.pitch - n1.pitch)
                        else:
                            curve_val = interp
                            
                        step_pitch = int(round(n1.pitch + (n2.pitch - n1.pitch) * curve_val))
                        step_pitch = max(0, min(127, step_pitch))
                        
                        step_dur_legato = step_dur * 1.25
                        
                        if 0 <= step_onset < duration_beats:
                            from melodica.types import NoteInfo
                            new_slides.append(
                                NoteInfo(
                                    pitch=max(low_pitch_bound, step_pitch),
                                    start=round(step_onset, 6),
                                    duration=round(step_dur_legato, 6),
                                    velocity=max(1, min(127, int(n1.velocity * 0.95))),
                                    articulation="808",
                                )
                            )
        notes.extend(new_slides)

    # 2. Transient Ducking Gate (Kick-Lock)
    if transient_ducking:
        kick_starts = {n.start for n in notes if n.pitch == 36 and getattr(n, "articulation", None) != "808"}
        for n in notes:
            if getattr(n, "articulation", None) == "808":
                if any(abs(n.start - k_start) < 0.01 for k_start in kick_starts):
                    n.start = round(n.start + ducking_duration, 6)
                    n.duration = round(max(0.05, n.duration - ducking_duration), 6)

    # 3. Envelope Gating
    if envelope_gating:
        notes.sort(key=lambda x: x.start)
        chord_boundaries = [c.start for c in chords]
        for i, n in enumerate(notes):
            if getattr(n, "articulation", None) == "808":
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

    return notes
