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
variations_harmonic.py
"""

from __future__ import annotations

from __future__ import annotations

import random
from dataclasses import dataclass
from melodica.types import NoteInfo
from melodica.modifiers import ModifierContext
from melodica.types import NoteInfo
from melodica.modifiers import ModifierContext

@dataclass
class DoublingModifier:
    """Doubles or triples the phrase length by repeating it."""
    multiplier: int = 2

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        original_duration = context.duration_beats
        new_notes = []
        for i in range(self.multiplier):
            for n in notes:
                new_notes.append(NoteInfo(
                    pitch=n.pitch,
                    start=round(n.start + i * original_duration, 6),
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute
                ))
        return new_notes

@dataclass
class AddIntervalModifier:
    """Adds a parallel interval to each note."""
    interval_semitones: int = 7 # Fifth
    diatonic: bool = True

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = list(notes)
        for n in notes:
            if not self.diatonic:
                result.append(NoteInfo(
                    pitch=n.pitch + self.interval_semitones,
                    start=n.start, duration=n.duration, velocity=n.velocity, absolute=n.absolute
                ))
            else:
                # Find degree in key
                deg = context.key.degree_of(n.pitch % 12)
                if deg is not None:
                    # Move by scale steps (logic simplified - add 2 steps for a third)
                    # For simplicity, we just add semitones for now but could be improved
                    result.append(NoteInfo(
                        pitch=n.pitch + self.interval_semitones,
                        start=n.start, duration=n.duration, velocity=n.velocity, absolute=n.absolute
                    ))
        return result

@dataclass
class AddChordNotesModifier:
    """Adds missing notes from the current chord to the phrase."""
    only_on_downbeat: bool = True

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = list(notes)
        for chord in context.chords:
            if self.only_on_downbeat:
                # Add chord notes at chord start
                pcs = chord.pitch_classes()
                for pc in pcs:
                    # Avoid duplicates
                    if not any(n.pitch % 12 == pc and abs(n.start - chord.start) < 0.1 for n in notes):
                        # Add in an appropriate octave (let's say octave 4)
                        result.append(NoteInfo(
                            pitch=48 + pc,
                            start=chord.start,
                            duration=chord.duration * 0.5,
                            velocity=chord.velocity if hasattr(chord, 'velocity') else 64,
                            absolute=False
                        ))
        return result

@dataclass
class SpreadChordNotesModifier:
    """Opens up voicings by moving mid notes an octave up or down."""
    
    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        # Group by start time
        groups: dict[float, list[NoteInfo]] = {}
        for n in notes:
            t = round(n.start, 4)
            groups.setdefault(t, []).append(n)
            
        result = []
        for t, g in groups.items():
            if len(g) >= 3:
                g.sort(key=lambda x: x.pitch)
                # Move the middle note an octave down (standard drop-2-ish logic)
                g[1].pitch -= 12
            result.extend(g)
        return result

@dataclass
class VelocityGeneratorModifier:
    """Generates complex velocity patterns."""
    min_vel: int = 40
    max_vel: int = 100
    curve: str = "ramp_up" # "ramp_up", "ramp_down", "random"

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        dur = context.duration_beats
        result = []
        for n in notes:
            progress = n.start / dur
            if self.curve == "ramp_up":
                v = self.min_vel + (self.max_vel - self.min_vel) * progress
            elif self.curve == "ramp_down":
                v = self.max_vel - (self.max_vel - self.min_vel) * progress
            else:
                v = random.randint(self.min_vel, self.max_vel)
            
            result.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=int(max(1, min(127, v))),
                absolute=n.absolute
            ))
        return result

@dataclass
class SlicePhraseModifier:
    """Chops notes into smaller pieces based on a grid."""
    grid: float = 0.25 # 16th notes

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = []
        for n in notes:
            if n.duration > self.grid * 1.5:
                # Chop it
                t = n.start
                while t < n.start + n.duration - 0.01:
                    chunk_dur = min(self.grid, n.start + n.duration - t)
                    result.append(NoteInfo(
                        pitch=n.pitch, start=round(t,6), duration=round(chunk_dur,6),
                        velocity=n.velocity, absolute=n.absolute
                    ))
                    t += self.grid
            else:
                result.append(n)
        return result

@dataclass
class RotateNotesModifier:
    """Cyclically rotates notes in time."""
    shift_beats: float = 1.0

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        dur = context.duration_beats
        result = []
        for n in notes:
            new_start = (n.start + self.shift_beats) % dur
            result.append(NoteInfo(
                pitch=n.pitch, start=round(new_start,6), duration=n.duration,
                velocity=n.velocity, absolute=n.absolute
            ))
        return sorted(result, key=lambda x: x.start)

@dataclass
class RemoveShortNotesModifier:
    """Removes all notes shorter than a threshold."""
    min_duration: float = 0.1

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        return [n for n in notes if n.duration >= self.min_duration]
