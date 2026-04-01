"""
modifiers/rhythmic.py — Rhythmic Variations.

Layer: Application / Domain
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.modifiers import ModifierContext, PhraseModifier
from melodica.types import NoteInfo


@dataclass
class QuantizeModifier(PhraseModifier):
    """Snaps note onsets and optionally durations to a grid."""
    grid_resolution: float = 0.25
    quantize_durations: bool = False

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if self.grid_resolution <= 0:
            return notes
            
        result = []
        for n in notes:
            new_start = round(n.start / self.grid_resolution) * self.grid_resolution
            new_dur = n.duration
            if self.quantize_durations:
                new_dur = round(n.duration / self.grid_resolution) * self.grid_resolution
                new_dur = max(self.grid_resolution, new_dur)
                
            result.append(NoteInfo(
                pitch=n.pitch,
                start=new_start,
                duration=new_dur,
                velocity=n.velocity,
                absolute=n.absolute
            ))
        return result


@dataclass
class FollowRhythmModifier(PhraseModifier):
    """
    Takes the onsets and durations from a source track and applies them 
    to the pitch choices of the current phrase.
    """
    source_track: str = "Melody"

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        source_notes = context.tracks.get(self.source_track)
        if not source_notes or not notes:
            return notes
            
        # Get unique rhythm events from source (grouped by onset)
        onsets = {} # onset -> max duration
        for sn in source_notes:
            t = round(sn.start, 6)
            onsets[t] = max(onsets.get(t, 0), sn.duration)
            
        # For each onset in source, we want to play what 'notes' was playing at that time
        result = []
        for onset, dur in sorted(onsets.items()):
            # Find which notes in the current phrase are 'active' at this onset
            # If none, find the notes that WERE playing at the original phrase's closest point
            active_notes = [n for n in notes if n.start <= onset < n.start + n.duration]
            
            if not active_notes:
                # Fallback: pick the closest notes in time
                closest_start = min(notes, key=lambda n: abs(n.start - onset)).start
                active_notes = [n for n in notes if n.start == closest_start]
                
            for n in active_notes:
                result.append(NoteInfo(
                    pitch=n.pitch,
                    start=onset,
                    duration=dur,
                    velocity=n.velocity,
                    absolute=n.absolute
                ))
        return result


@dataclass
class HumanizeModifier(PhraseModifier):
    """Applies slight gaussian noise to timing and dynamics."""
    timing_std: float = 0.015   # Standard deviation for onset/duration in beats
    velocity_std: float = 5.0   # Standard deviation for MIDI velocity

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = []
        for n in notes:
            start_noise = random.gauss(0, self.timing_std)
            dur_noise = random.gauss(0, self.timing_std)
            vel_noise = random.gauss(0, self.velocity_std)
            
            new_start = max(0.0, n.start + start_noise)
            new_dur = max(0.05, n.duration + dur_noise)
            new_vel = int(n.velocity + vel_noise)
            new_vel = max(1, min(127, new_vel))
            
            result.append(NoteInfo(
                pitch=n.pitch,
                start=round(new_start, 6),
                duration=round(new_dur, 6),
                velocity=new_vel,
                absolute=n.absolute,
                articulation=n.articulation,
                expression=dict(n.expression),
            ))
        return result


@dataclass
class SwingController(PhraseModifier):
    """
    Applies swing feel. Delays the offbeat notes.
    swing_ratio: 0.5 = straight, 0.66 = hard triplet swing.
    grid: The beat division (usually 0.5 for 8th note swing, or 0.25 for 16th note swing).
    """
    swing_ratio: float = 0.6
    grid: float = 0.5

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if self.swing_ratio <= 0.5 or self.grid <= 0:
            return notes
            
        # Amount to shift the offbeat (as a fraction of grid)
        # Ratio 0.5 -> delay 0
        # Ratio 0.66 -> delay is grid/3
        delay = (self.swing_ratio - 0.5) * 2.0 * (self.grid / 2.0)
        
        result = []
        for n in notes:
            # Check if this note falls closely on the offbeat
            grid_pos = (n.start % self.grid)
            is_offbeat = abs(grid_pos - (self.grid / 2.0)) < 0.05
            
            new_start = n.start + delay if is_offbeat else n.start
            
            result.append(NoteInfo(
                pitch=n.pitch,
                start=round(new_start, 6),
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute
            ))
        return result


@dataclass
class AdjustNoteLengthsModifier(PhraseModifier):
    """Gates or scales note durations."""
    gate_factor: float = 1.0  # e.g. 0.5 for staccato
    set_fixed: float | None = None # Force all notes to this duration

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = []
        for n in notes:
            if self.set_fixed is not None:
                new_dur = self.set_fixed
            else:
                new_dur = max(0.01, n.duration * self.gate_factor)
                
            result.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=round(new_dur, 6),
                velocity=n.velocity,
                absolute=n.absolute
            ))
        return result
