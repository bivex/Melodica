# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-08-24
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
modifiers/melody_processors.py — PhraseModifier adapters for melody processing.

Layer: Application / Modifier

Provides standardized PhraseModifier implementations for ornamental grace notes,
passing-tone smoothing (leap fills), and phrase velocity contouring.
These can be inserted into any ModifierPipeline or applied to any PhraseGenerator.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from melodica.modifiers import ModifierContext, PhraseModifier
from melodica.types import NoteInfo, Scale
from melodica.utils import snap_to_scale

if TYPE_CHECKING:
    from melodica.generators._melody_drama import DramaticArc


class OrnamentModifier(PhraseModifier):
    """
    Adds ornamental grace notes before strong beats and harmonic points.
    Implements the standard PhraseModifier strategy protocol.
    """

    def __init__(
        self,
        ornament_probability: float = 0.2,
        low_pitch: int = 48,
        high_pitch: int = 84,
        drama: "DramaticArc | None" = None,
    ) -> None:
        super().__init__()
        self.ornament_probability = max(0.0, min(1.0, ornament_probability))
        self.low_pitch = low_pitch
        self.high_pitch = high_pitch
        self.drama = drama

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes or self.ornament_probability <= 0:
            return notes

        active_key = context.scale
        scale_pcs = set(active_key.degrees())
        result: list[NoteInfo] = []

        for note in notes:
            is_strong = note.start % 1.0 < 0.15

            eff_prob = self.ornament_probability
            if self.drama:
                eff_prob = min(0.8, eff_prob + self.drama.tension(note.start) * 0.3)

            if is_strong and random.random() < eff_prob:
                approach_above = random.random() < 0.5
                for offset in [2, 1, 3]:  # try m2, M2, m3
                    sign = 1 if approach_above else -1
                    grace_pc = (note.pitch + offset * sign) % 12
                    if grace_pc in scale_pcs:
                        grace_pitch = note.pitch + offset * sign
                        if self.low_pitch <= grace_pitch <= self.high_pitch:
                            grace_dur = 0.0625
                            grace_start = max(0.0, note.start - grace_dur)
                            result.append(
                                NoteInfo(
                                    pitch=grace_pitch,
                                    start=round(grace_start, 6),
                                    duration=grace_dur,
                                    velocity=max(1, int(note.velocity * 0.6)),
                                )
                            )
                            break
            result.append(note)

        result.sort(key=lambda n: (n.start, n.pitch))
        return result


class FillLeapsModifier(PhraseModifier):
    """
    Inserts passing tones between notes with large intervallic leaps (> 4 semitones).
    Implements the standard PhraseModifier strategy protocol.
    """

    def __init__(
        self,
        min_leap_semitones: int = 4,
        max_fills_factor: float = 0.5,
        note_range_low: int = 48,
        note_range_high: int = 84,
    ) -> None:
        super().__init__()
        self.min_leap_semitones = min_leap_semitones
        self.max_fills_factor = max_fills_factor
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if len(notes) < 2:
            return notes

        sorted_notes = sorted(notes, key=lambda n: n.start)
        result = [sorted_notes[0]]
        fills_added = 0
        max_fills = max(4, int(len(sorted_notes) * self.max_fills_factor))
        key = context.scale

        for i in range(1, len(sorted_notes)):
            gap = sorted_notes[i].pitch - sorted_notes[i - 1].pitch
            abs_gap = abs(gap)

            if abs_gap > self.min_leap_semitones and fills_added < max_fills:
                direction = 1 if gap > 0 else -1
                num_fills = min(abs_gap // 3, 4) if abs_gap > 7 else 1
                span = sorted_notes[i].start - sorted_notes[i - 1].start

                for fill_idx in range(num_fills):
                    if num_fills == 1:
                        frac = 0.5
                        step = min(abs_gap // 2, 4)
                    else:
                        frac = (fill_idx + 1) / (num_fills + 1)
                        step = round(abs_gap * frac)

                    pass_pitch = sorted_notes[i - 1].pitch + direction * max(1, step)
                    pass_start = sorted_notes[i - 1].start + span * frac

                    active_key = key.get_key_at(pass_start) if hasattr(key, "get_key_at") else key
                    pass_pitch = snap_to_scale(
                        max(self.note_range_low, min(self.note_range_high, pass_pitch)), active_key
                    )

                    pass_dur = min(sorted_notes[i - 1].duration, 0.25)

                    result.append(
                        NoteInfo(
                            pitch=pass_pitch,
                            start=round(pass_start, 6),
                            duration=round(pass_dur, 6),
                            velocity=max(1, int(sorted_notes[i - 1].velocity * 0.75)),
                        )
                    )
                    fills_added += 1

            result.append(sorted_notes[i])

        result.sort(key=lambda n: (n.start, n.pitch))
        return result


class VelocityContourModifier(PhraseModifier):
    """
    Applies musical phrase contour, metric accents, and dynamics curve to note velocities.
    Implements the standard PhraseModifier strategy protocol.
    """

    def __init__(
        self,
        contour: str = "arch",
        accent_strength: float = 1.2,
        phrase_length: float | None = None,
    ) -> None:
        super().__init__()
        self.contour = contour
        self.accent_strength = accent_strength
        self.phrase_length = phrase_length

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return notes

        total_length = self.phrase_length or context.duration_beats or max(n.start + n.duration for n in notes)
        if total_length <= 0:
            total_length = 4.0

        modified: list[NoteInfo] = []
        for n in notes:
            progress = min(1.0, max(0.0, n.start / total_length))

            # Shape factor
            if self.contour == "arch":
                # Peak around midpoint
                shape = 1.0 - 4.0 * (progress - 0.5) ** 2  # 0 at edges, 1 at center
                vel_mult = 0.85 + 0.3 * shape
            elif self.contour == "crescendo":
                vel_mult = 0.7 + 0.5 * progress
            elif self.contour == "decrescendo":
                vel_mult = 1.2 - 0.4 * progress
            else:
                vel_mult = 1.0

            # Downbeat metric accent
            is_downbeat = n.start % 1.0 < 0.1
            if is_downbeat:
                vel_mult *= self.accent_strength

            new_vel = max(1, min(127, int(n.velocity * vel_mult)))
            modified.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=new_vel,
                    articulation=n.articulation,
                    expression=dict(n.expression),
                )
            )

        return modified
