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


@dataclass
class ChordToneSnapModifier(PhraseModifier):
    """
    Snaps notes to the nearest chord tone of the active chord.
    If multiple chord tones are equally near, it picks the one in the direction
    of the original note (or downwards by default).
    """

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not context.timeline:
            return notes

        result = []
        for n in notes:
            chord = context.timeline.get_chord_at(n.start)
            if not chord:
                result.append(n)
                continue

            chord_tones = chord.pitch_classes()
            if not chord_tones:
                result.append(n)
                continue

            pc = n.pitch % 12
            if pc in chord_tones:
                result.append(n)
                continue

            # Find nearest chord tone in pitch space
            best_shift = 0
            min_dist = 13
            for cpc in chord_tones:
                for shift in [-12, 0, 12]:
                    diff = (cpc + shift) - pc
                    if abs(diff) < min_dist:
                        min_dist = abs(diff)
                        best_shift = diff
                    elif abs(diff) == min_dist:
                        # Tie-break: prefer the shift that was already chosen or smaller absolute
                        if abs(diff) < abs(best_shift):
                            best_shift = diff

            new_pitch = max(0, min(127, n.pitch + best_shift))
            result.append(NoteInfo(
                pitch=new_pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute
            ))
        return result
