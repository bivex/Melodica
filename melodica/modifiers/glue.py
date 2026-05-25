# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
modifiers/glue.py — Micro-arrangement and Transitions.

Contains modifiers for "glueing" an arrangement together:
- DropSilenceModifier: Mutes tracks right before a drop/climax.
- DrumFillModifier: Forces a fill at the end of a section.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from melodica.types import NoteInfo
from melodica.modifiers import ModifierContext


@dataclass
class DropSilenceModifier:
    """Mutes all notes within a window before a target beat (drop silence / vacuum effect)."""
    silence_duration: float = 1.0
    apply_at_end: bool = True
    specific_beats: list[float] = field(default_factory=list)

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []

        targets = list(self.specific_beats)
        if self.apply_at_end:
            targets.append(context.duration_beats)

        result = []
        for n in notes:
            note_end = n.start + n.duration
            new_dur = n.duration

            for target_end in targets:
                sil_start = target_end - self.silence_duration
                # Note starts inside silence window — skip entirely
                if n.start >= sil_start and n.start < target_end:
                    new_dur = 0
                    break
                # Note overlaps into silence window — truncate
                if n.start < sil_start and note_end > sil_start:
                    new_dur = sil_start - n.start

            if new_dur > 0.001:
                result.append(replace(n, duration=new_dur) if new_dur != n.duration else n)

        return result


@dataclass
class DrumFillModifier:
    """Replaces a section of drum pattern with a crescendo fill (e.g. snare roll)."""
    fill_duration: float = 2.0
    fill_pitch: int = 38
    subdivision: float = 0.25
    velocity_start: int = 40
    velocity_end: int = 127
    accent_on_drop: bool = True
    accent_pitch: int = 36
    apply_at_end: bool = True
    specific_beats: list[float] = field(default_factory=list)

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []

        targets = list(self.specific_beats)
        if self.apply_at_end:
            targets.append(context.duration_beats)

        result = []
        for n in notes:
            note_end = n.start + n.duration
            new_dur = n.duration

            for target_end in targets:
                fill_start = target_end - self.fill_duration
                if n.start >= fill_start and n.start < target_end:
                    new_dur = 0
                    break
                if n.start < fill_start and note_end > fill_start:
                    new_dur = fill_start - n.start

            if new_dur > 0.001:
                result.append(replace(n, duration=new_dur) if new_dur != n.duration else n)

        # Generate fill notes with crescendo
        for target_end in targets:
            fill_start = target_end - self.fill_duration
            if fill_start < 0:
                continue

            t = fill_start
            vel_range = self.velocity_end - self.velocity_start
            while t < target_end - 0.01:
                progress = (t - fill_start) / self.fill_duration
                # Exponential curve for more dramatic build
                vel = int(self.velocity_start + vel_range * (progress ** 1.5))
                result.append(NoteInfo(
                    pitch=self.fill_pitch,
                    start=round(t, 6),
                    duration=self.subdivision * 0.85,
                    velocity=vel,
                ))
                t += self.subdivision

            # Accent hit exactly on the drop beat
            if self.accent_on_drop:
                result.append(NoteInfo(
                    pitch=self.accent_pitch,
                    start=target_end,
                    duration=0.5,
                    velocity=127,
                ))

        result.sort(key=lambda x: x.start)
        return result
