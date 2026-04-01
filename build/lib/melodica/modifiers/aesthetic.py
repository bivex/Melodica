"""
modifiers/aesthetic.py — "Sellable" / Modern Aesthetic Variations.

Layer: Application / Domain
Aimed for: Modern Pop, R&B, Lo-Fi, and "Madonna-style" polished dynamics.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from melodica.modifiers import ModifierContext, PhraseModifier
from melodica.types import NoteInfo, OCTAVE


@dataclass
class GrooveModifier(PhraseModifier):
    """
    Applies custom logic for "that modern groove" (Swing + Micro-offset).
    Modeled after 'Buy & Sell' top-tier chart dynamics.
    """
    swing: float = 0.5  # 0.5 = neutral, 0.6 = funky, 0.4 = rushed
    tightness: float = 0.95  # 1.0 = robotic, 0.0 = total chaos
    random_velocity: int = 5  # subtle velocity variation

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return notes
            
        result = []
        for n in notes:
            # 1. Swing logic on offbeats (simplified 16th swing)
            # Find position within the beat
            pos_in_beat = n.start % 1.0
            new_start = n.start
            
            if 0.2 < pos_in_beat < 0.3: # roughly 2nd 16th
                offset = (self.swing - 0.5) * 0.15
                new_start += offset
            elif 0.7 < pos_in_beat < 0.8: # roughly 4th 16th
                offset = (self.swing - 0.5) * 0.15
                new_start += offset

            # 2. Random micro-offset (Humanization)
            human_offset = (random.random() - 0.5) * (1.0 - self.tightness) * 0.2
            new_start += human_offset

            # 3. Dynamic accentuation (Pop/Madonna style: accent on 1 and 3)
            vel_accent = 0
            if n.start % 2.0 < 0.1: # beat 1
                vel_accent = 10
            elif n.start % 1.0 < 0.1: # other downbeats
                vel_accent = 5
            
            new_vel = n.velocity + vel_accent + random.randint(-self.random_velocity, self.random_velocity)
            new_vel = max(1, min(127, int(new_vel)))

            result.append(NoteInfo(
                pitch=n.pitch,
                start=new_start,
                duration=n.duration,
                velocity=new_vel,
                absolute=n.absolute
            ))
        return result


@dataclass
class PolishedOctaveModifier(PhraseModifier):
    """
    Adds a subtle octave-up 'shimmer' or octave-down 'thickness'.
    Essential for 'Premium Pop' and 'Madonna' sub-bass/lead vibes.
    """
    octave_shift: int = 1 # 1 = up, -1 = down
    probability: float = 0.3 # only double some notes to keep it airy
    velocity_scale: float = 0.6 # secondary notes are quieter

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        doubled_notes = []
        for n in notes:
            doubled_notes.append(n)
            
            # Roll for shimmer
            if random.random() < self.probability:
                shimmer_pitch = n.pitch + (self.octave_shift * OCTAVE)
                if 0 <= shimmer_pitch <= 127:
                    doubled_notes.append(NoteInfo(
                        pitch=shimmer_pitch,
                        start=n.start,
                        duration=n.duration,
                        velocity=int(n.velocity * self.velocity_scale),
                        absolute=n.absolute
                    ))
        
        return sorted(doubled_notes, key=lambda x: x.start)
