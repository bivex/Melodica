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
rc_variations_chord.py
"""

from __future__ import annotations

from __future__ import annotations
import random
from dataclasses import dataclass, field
from melodica.types import NoteInfo
from melodica.modifiers import ModifierContext

@dataclass
class AddChordNotesModifier:
    """Add chord tones to each existing note (unison doubling with chord notes)."""

    count: int = 1  # how many extra notes per original

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        result = list(notes)
        for n in notes:
            chord = None
            for c in context.chords:
                if c.start <= n.start < c.end:
                    chord = c
                    break
            if chord is None:
                continue
            pcs = chord.pitch_classes()
            for i in range(self.count):
                pc = pcs[(i + 1) % len(pcs)] if pcs else n.pitch % 12
                new_pitch = n.pitch - (n.pitch % 12) + pc
                if new_pitch != n.pitch:
                    result.append(
                        NoteInfo(
                            pitch=new_pitch,
                            start=n.start,
                            duration=n.duration,
                            velocity=max(1, n.velocity - 10),
                            absolute=n.absolute,
                        )
                    )
        return result

@dataclass
class SpreadOutChordNotesModifier:
    """Spread chord notes vertically (add octave offsets)."""

    spread_semitones: int = 12  # octave spread

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = []
        for i, n in enumerate(notes):
            result.append(n)
            if i % 2 == 1:
                result.append(
                    NoteInfo(
                        pitch=n.pitch + self.spread_semitones,
                        start=n.start,
                        duration=n.duration,
                        velocity=max(1, n.velocity - 15),
                        absolute=n.absolute,
                    )
                )
        return result

@dataclass
class SwapChordNotesModifier:
    """Swap adjacent chord notes (transpose one up, one down)."""

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = list(notes)
        for i in range(0, len(result) - 1, 2):
            result[i], result[i + 1] = result[i + 1], result[i]
        return result

@dataclass
class PermuteChordNotesModifier:
    """Randomly permute the order of chord notes within each beat."""

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        # Group notes by beat
        from collections import defaultdict

        groups: dict[float, list[NoteInfo]] = defaultdict(list)
        for n in notes:
            beat = round(n.start)
            groups[beat].append(n)
        result = []
        for beat in sorted(groups.keys()):
            group = groups[beat]
            random.shuffle(group)
            for n in group:
                result.append(n)
        return result

@dataclass
class FillGapsModifier:
    """Fill gaps between notes with passing tones."""

    max_gap: float = 1.0  # beats

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if len(notes) < 2:
            return notes
        sorted_notes = sorted(notes, key=lambda n: n.start)
        result = [sorted_notes[0]]
        for i in range(1, len(sorted_notes)):
            prev = sorted_notes[i - 1]
            curr = sorted_notes[i]
            gap = curr.start - (prev.start + prev.duration)
            if 0 < gap <= self.max_gap:
                mid_pitch = (prev.pitch + curr.pitch) // 2
                mid_start = prev.start + prev.duration
                result.append(
                    NoteInfo(
                        pitch=mid_pitch,
                        start=round(mid_start, 6),
                        duration=round(gap * 0.8, 6),
                        velocity=max(1, int(curr.velocity * 0.6)),
                        absolute=prev.absolute,
                    )
                )
            result.append(curr)
        return result

@dataclass
class RemoveDuplicatesModifier:
    """Remove consecutive duplicate pitches."""

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        result = [notes[0]]
        for n in notes[1:]:
            if n.pitch != result[-1].pitch:
                result.append(n)
        return result

@dataclass
class AudioGainModifier:
    """Scale all velocities by a gain factor."""

    gain: float = 1.0  # 0.0-2.0

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        return [
            NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=max(1, min(127, int(n.velocity * self.gain))),
                absolute=n.absolute,
            )
            for n in notes
        ]

@dataclass
class VelocityGeneratorModifier:
    """Generate a velocity curve across the phrase."""

    pattern: str = "crescendo"  # "crescendo", "decrescendo", "accent_beats", "random"

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        result = []
        for i, n in enumerate(notes):
            if self.pattern == "crescendo":
                vel = int(40 + (i / max(1, len(notes) - 1)) * 80)
            elif self.pattern == "decrescendo":
                vel = int(120 - (i / max(1, len(notes) - 1)) * 80)
            elif self.pattern == "accent_beats":
                vel = 100 if n.start % 1.0 < 0.1 else 60
            else:
                vel = random.randint(40, 100)
            result.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=min(127, max(1, vel)),
                    absolute=n.absolute,
                )
            )
        return result

@dataclass
class SimplifyPhraseModifier:
    """Keep only every Nth note (simplify the phrase)."""

    keep_every: int = 2  # keep every 2nd note

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        return [n for i, n in enumerate(notes) if i % self.keep_every == 0]
