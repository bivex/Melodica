# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
modifiers/glue.py — Micro-arrangement and Transitions.

Contains modifiers for "glueing" an arrangement together:
- DropSilenceModifier: Mutes tracks right before a drop/climax.
- DrumFillModifier: Forces a fill at the end of a section.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from melodica.types import NoteInfo
from melodica.modifiers import ModifierContext


@dataclass
class DropSilenceModifier:
    """
    Creates a 'Drop Silence' effect (muting all notes) right before a climax.
    Can trigger at specific beats or automatically at the end of the phrase.
    """
    silence_duration: float = 1.0  # How many beats to silence
    apply_at_end: bool = True      # Automatically silence the end of the full duration
    specific_beats: list[float] = field(default_factory=list) # Exact beats to end the silence at

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []

        targets = list(self.specific_beats)
        if self.apply_at_end:
            targets.append(context.duration_beats)

        result = []
        for n in notes:
            muted = False
            for target_end in targets:
                target_start = target_end - self.silence_duration
                # If note falls within the silence window
                if target_start <= n.start < target_end:
                    muted = True
                    break
                # If note overlaps into the silence window, truncate it
                elif n.start < target_start and n.start + n.duration > target_start:
                    n.duration = target_start - n.start
                    
            if not muted and n.duration > 0.001:
                result.append(n)
                
        return result


@dataclass
class DrumFillModifier:
    """
    Overrides the end of a drum pattern with a fast fill (e.g. 16ths/32nds snare roll).
    """
    fill_duration: float = 1.0   # Length of the fill in beats (e.g. 1 beat = 1/4 note)
    fill_pitch: int = 38         # Snare drum pitch by default
    subdivision: float = 0.25    # 16th notes
    apply_at_end: bool = True
    specific_beats: list[float] = field(default_factory=list)

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []

        targets = list(self.specific_beats)
        if self.apply_at_end:
            targets.append(context.duration_beats)

        result = []
        # First, remove original notes in the fill windows
        for n in notes:
            in_fill_window = False
            for target_end in targets:
                target_start = target_end - self.fill_duration
                if target_start <= n.start < target_end:
                    in_fill_window = True
                    break
                elif n.start < target_start and n.start + n.duration > target_start:
                    n.duration = target_start - n.start
            
            if not in_fill_window and n.duration > 0.001:
                result.append(n)

        # Second, generate the fills
        for target_end in targets:
            target_start = target_end - self.fill_duration
            if target_start < 0:
                continue
                
            current_time = target_start
            velocity_start = 50
            velocity_end = 110
            
            while current_time < target_end - 0.01:
                # Calculate crescendo velocity
                progress = (current_time - target_start) / self.fill_duration
                vel = int(velocity_start + (velocity_end - velocity_start) * progress)
                
                result.append(
                    NoteInfo(
                        pitch=self.fill_pitch,
                        start=round(current_time, 6),
                        duration=self.subdivision * 0.9, # Slight staccato
                        velocity=vel
                    )
                )
                current_time += self.subdivision

        return sorted(result, key=lambda x: x.start)
