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
modifiers/harmonic.py — Harmonic Variations.

Layer: Application / Domain
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.modifiers import ModifierContext, PhraseModifier
from melodica.types import NoteInfo
from melodica.utils import semitones_up


@dataclass
class NoteDoublerModifier(PhraseModifier):
    """
    Duplicates notes up or down by octaves.
    octaves: list of octave shifts to apply (e.g. [-1, 1] means sub-octave and up-octave).
    """
    octaves: list[int] = field(default_factory=lambda: [-1])

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not self.octaves:
            return notes
            
        result = list(notes)
        for n in notes:
            for oct_shift in self.octaves:
                new_pitch = n.pitch + (oct_shift * 12)
                if 0 <= new_pitch <= 127:
                    # Reduce velocity for doublings
                    new_vel = int(n.velocity * 0.8)
                    result.append(NoteInfo(
                        pitch=new_pitch,
                        start=n.start,
                        duration=n.duration,
                        velocity=new_vel,
                        absolute=n.absolute
                    ))
                    
        return sorted(result, key=lambda x: (x.start, x.pitch))


@dataclass
class TransposeModifier(PhraseModifier):
    """Transposes all notes chromatically."""
    semitones: int = 0

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if self.semitones == 0:
            return notes
            
        result = []
        for n in notes:
            new_pitch = semitones_up(n.pitch, self.semitones)
            result.append(NoteInfo(
                pitch=new_pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute
            ))
        return result


@dataclass
class LimitNoteRangeModifier(PhraseModifier):
    """
    Ensures all notes fall within a specified MIDI range.
    Notes outside the range are transposed by octaves until they fit.
    """
    low: int = 48
    high: int = 84

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if self.low >= self.high:
            return notes
            
        result = []
        for n in notes:
            new_pitch = n.pitch
            while new_pitch < self.low:
                new_pitch += 12
            while new_pitch > self.high:
                new_pitch -= 12
                
            # Fallback if range is smaller than an octave (should not happen usually)
            if new_pitch < self.low:
                new_pitch = self.low
                
            result.append(NoteInfo(
                pitch=new_pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute
            ))
        return result
