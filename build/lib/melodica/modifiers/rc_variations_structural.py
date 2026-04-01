"""
rc_variations_structural.py
"""

from __future__ import annotations

from __future__ import annotations
import random
from dataclasses import dataclass, field
from melodica.types import NoteInfo
from melodica.modifiers import ModifierContext

@dataclass
class AddIntervalModifier:
    """Add interval above or below each note."""

    semitones: int = 7  # +5 = 4th, +7 = 5th, +12 = octave
    direction: str = "above"  # "above" | "below"

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = list(notes)
        for n in notes:
            offset = self.semitones if self.direction == "above" else -self.semitones
            new_pitch = max(0, min(127, n.pitch + offset))
            result.append(
                NoteInfo(
                    pitch=new_pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=max(1, n.velocity - 15),
                    absolute=n.absolute,
                )
            )
        return result

@dataclass
class DelayNotesModifier:
    """Delay all notes by a number of beats."""

    delay_beats: float = 0.5

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        return [
            NoteInfo(
                pitch=n.pitch,
                start=round(n.start + self.delay_beats, 6),
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute,
            )
            for n in notes
        ]

@dataclass
class DoublePhraseModifier:
    """Repeat the phrase (double it in time)."""

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        shift = context.duration_beats
        result = list(notes)
        for n in notes:
            result.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=round(n.start + shift, 6),
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute,
                )
            )
        return result

@dataclass
class TriplePhraseModifier:
    """Triple the phrase (repeat it twice)."""

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        shift = context.duration_beats
        result = list(notes)
        for repeat in [1, 2]:
            for n in notes:
                result.append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=round(n.start + shift * repeat, 6),
                        duration=n.duration,
                        velocity=n.velocity,
                        absolute=n.absolute,
                    )
                )
        return result

@dataclass
class ExtractRhythmModifier:
    """Extract rhythm from notes — set all pitches to a single pitch."""

    target_pitch: int = 60

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        return [
            NoteInfo(
                pitch=self.target_pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute,
            )
            for n in notes
        ]

@dataclass
class JoinNotesModifier:
    """Join consecutive notes on the same pitch into one sustained note."""

    max_gap: float = 0.1  # max gap in beats to consider joining

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        sorted_notes = sorted(notes, key=lambda n: n.start)
        result = [sorted_notes[0]]
        for n in sorted_notes[1:]:
            prev = result[-1]
            if n.pitch == prev.pitch and n.start - (prev.start + prev.duration) <= self.max_gap:
                # Join
                result[-1] = NoteInfo(
                    pitch=prev.pitch,
                    start=prev.start,
                    duration=round(n.start + n.duration - prev.start, 6),
                    velocity=max(prev.velocity, n.velocity),
                    absolute=prev.absolute,
                )
            else:
                result.append(n)
        return result

@dataclass
class RemoveShortNotesModifier:
    """Remove notes shorter than a threshold."""

    min_duration: float = 0.1  # beats

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        return [n for n in notes if n.duration >= self.min_duration]

@dataclass
class RotateNotesModifier:
    """Rotate note positions by a number of beats."""

    beats: float = 0.5

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        rotated = []
        for n in notes:
            new_start = (n.start + self.beats) % context.duration_beats
            rotated.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=round(new_start, 6),
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute,
                )
            )
        return sorted(rotated, key=lambda n: n.start)
