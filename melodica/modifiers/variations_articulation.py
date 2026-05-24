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
variations_articulation.py
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from melodica.types import NoteInfo
from melodica.modifiers import ModifierContext, PhraseModifier

@dataclass
class MirrorModifier:
    """Modeled after the phrase horizontally or vertically."""
    axis: str = "horizontal" # "horizontal" | "vertical"
    center_midi: int = 60

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes: return []
        
        if self.axis == "horizontal":
            duration = context.duration_beats
            return [NoteInfo(
                pitch=n.pitch,
                start=round(duration - (n.start + n.duration), 6),
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute
            ) for n in reversed(notes)]
        else: # vertical
            return [NoteInfo(
                pitch=round(self.center_midi - (n.pitch - self.center_midi)),
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute
            ) for n in notes]

@dataclass
class StaccatoLegatoModifier:
    """Adjusts note lengths to be short (staccato) or overlapping (legato)."""
    amount: float = 0.5 # 0.1 = staccato, 1.1 = legato

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        return [NoteInfo(
            pitch=n.pitch,
            start=n.start,
            duration=round(n.duration * self.amount, 6),
            velocity=n.velocity,
            absolute=n.absolute
        ) for n in notes]

@dataclass
class AccentModifier:
    """Accents specific beats (4ths, 8ths, 16ths)."""
    grid: float = 1.0 # 1.0 = 4ths, 0.5 = 8ths
    accent_vel: int = 20

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = []
        for n in notes:
            new_vel = n.velocity
            if n.start % self.grid < 0.05:
                new_vel += self.accent_vel
            result.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=max(1, min(127, new_vel)),
                absolute=n.absolute
            ))
        return result

@dataclass
class ReRhythmizeModifier:
    """Randomly shifts note onsets slightly while keeping pitch and order."""
    intensity: float = 0.1

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        return [NoteInfo(
            pitch=n.pitch,
            start=round(n.start + (random.random() - 0.5) * self.intensity, 6),
            duration=n.duration,
            velocity=n.velocity,
            absolute=n.absolute
        ) for n in notes]

@dataclass
class MonophonicModifier:
    """Ensures only one note plays at a time (Monophonic/Solo mode)."""
    
    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes: return []
        sorted_notes = sorted(notes, key=lambda x: x.start)
        result = []
        for i in range(len(sorted_notes)):
            n = sorted_notes[i]
            if i < len(sorted_notes) - 1:
                next_start = sorted_notes[i+1].start
                duration = min(n.duration, next_start - n.start)
            else:
                duration = n.duration
            
            # Simple heuristic: ignore notes that would have 0 duration
            if duration > 0.01:
                result.append(NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=round(duration, 6),
                    velocity=n.velocity,
                    absolute=n.absolute
                ))
        return result

@dataclass
class MIDIEchoModifier:
    """Adds rhythmic echo / delay to notes."""
    delay_beats: float = 0.5
    repetitions: int = 2
    decay: float = 0.7

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        all_notes = list(notes)
        for n in notes:
            for r in range(1, self.repetitions + 1):
                echo_start = n.start + r * self.delay_beats
                if echo_start >= context.duration_beats: break
                all_notes.append(NoteInfo(
                    pitch=n.pitch,
                    start=echo_start,
                    duration=n.duration,
                    velocity=int(n.velocity * (self.decay ** r)),
                    absolute=n.absolute
                ))
        return all_notes

@dataclass
class StrumModifier:
    """Delays notes in a chord to simulate guitar strumming / piano roll."""
    strum_offset: float = 0.05 # Beats between notes in a chord
    direction: str = "up" # "up" = low to high, "down" = high to low

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        # Group notes by start time (assuming they are in chord)
        groups: dict[float, list[NoteInfo]] = {}
        for n in notes:
            t = round(n.start, 4)
            if t not in groups: groups[t] = []
            groups[t].append(n)
            
        result = []
        for t, g in groups.items():
            # Sort by pitch
            g.sort(key=lambda x: x.pitch, reverse=(self.direction == "down"))
            for i, n in enumerate(g):
                result.append(NoteInfo(
                    pitch=n.pitch,
                    start=round(n.start + i * self.strum_offset, 6),
                    duration=max(0.01, n.duration - i * self.strum_offset),
                    velocity=n.velocity,
                    absolute=n.absolute
                ))
        return result

@dataclass
class ArpeggiateModifier:
    """Spreads chord notes over time (arpeggiation)."""
    offset: float = 0.1

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        sorted_notes = sorted(notes, key=lambda x: (x.start, x.pitch))
        for i, n in enumerate(sorted_notes):
            n.start += i * self.offset
        return sorted_notes

@dataclass
class SlideLegatoModifier:
    """
    Adds pitch bend slides between consecutive notes if they are overlapping or very close.
    Works by adding a 'pitch_bend' ramp to the NoteInfo.expression dictionary.
    Best used with Monophonic phrases.
    """

    max_gap: float = 0.05
    slide_beats: float = 0.1

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        
        sorted_notes = sorted(notes, key=lambda x: x.start)
        for i in range(len(sorted_notes) - 1):
            n1 = sorted_notes[i]
            n2 = sorted_notes[i + 1]

            gap = n2.start - (n1.start + n1.duration)
            if gap <= self.max_gap:
                # Calculate interval in semitones
                interval = n2.pitch - n1.pitch
                if interval == 0:
                    continue

                # 8192 units = 2 semitones (standard range)
                # But Melodica uses configurable pitch_bend_range (default 2)
                # We'll assume default 2 for now, or just provide semitones if we can.
                # Actually, the exporter expects raw MIDI values.
                # 8192 / range = units per semitone
                PB_RANGE = 2
                units_per_semitone = 8192 / PB_RANGE

                # Add a ramp at the end of n1
                # The ramp should start before n1 ends and reach 'interval' at n2.start
                # But n1 ends at n1.start + n1.duration. 
                # Let's start the slide 'slide_beats' before n2.start
                slide_start_rel = n2.start - n1.start - self.slide_beats
                
                # Use a small ramp of 5 steps
                pb_events = []
                for step in range(6):
                    t_rel = slide_start_rel + (step / 5.0) * self.slide_beats
                    # progress from 0 to 1
                    progress = step / 5.0
                    val = int(progress * interval * units_per_semitone)
                    pb_events.append((round(t_rel, 6), val))
                
                n1.expression["pitch_bend"] = pb_events

        return sorted_notes


@dataclass
class ArticulationByLengthModifier(PhraseModifier):
    """
    Automatically sets articulation based on note duration.
    E.g., notes shorter than 0.25 beats become 'staccato'.
    """

    short_threshold: float = 0.25
    short_articulation: str = "staccato"
    long_articulation: str = "sustain"

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = []
        for n in notes:
            art = self.short_articulation if n.duration <= self.short_threshold else self.long_articulation
            result.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute,
                articulation=art,
                expression=dict(n.expression)
            ))
        return result


@dataclass
class OverlapSafetyModifier(PhraseModifier):
    """
    Ensures a small gap between consecutive notes of the same pitch
    to prevent VST re-triggering issues.
    """

    gap_beats: float = 0.02

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []
        
        sorted_notes = sorted(notes, key=lambda x: (x.pitch, x.start))
        for i in range(len(sorted_notes) - 1):
            n1 = sorted_notes[i]
            n2 = sorted_notes[i + 1]

            if n1.pitch == n2.pitch:
                # If they overlap or are too close
                if n1.start + n1.duration > n2.start - self.gap_beats:
                    n1.duration = max(0.01, n2.start - n1.start - self.gap_beats)

        return sorted(sorted_notes, key=lambda x: x.start)
