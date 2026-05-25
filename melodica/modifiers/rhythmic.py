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
    Re-rhythmize notes by adopting onsets and inter-onset durations from a source track.

    For each unique onset in the source, the closest pitch from the follower notes
    is placed at that onset. Duration = gap to the next source onset (or remaining
    time for the last onset). Polyphonic source onsets produce a single rhythm event.
    """
    source_track: str = "Melody"

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        source_notes = context.tracks.get(self.source_track)
        if not source_notes or not notes:
            return notes

        # Unique onset times from source (sorted)
        onset_times = sorted(set(round(sn.start, 4) for sn in source_notes))
        if not onset_times:
            return notes

        # Duration = gap to next onset; last onset extends to cover remaining time
        max_end = max(n.start + n.duration for n in notes)
        src_end = max(sn.start + sn.duration for sn in source_notes)
        timeline_end = max(max_end, src_end)
        onset_durs = []
        for i, t in enumerate(onset_times):
            if i + 1 < len(onset_times):
                onset_durs.append((t, round(onset_times[i + 1] - t, 6)))
            else:
                onset_durs.append((t, round(timeline_end - t, 6)))

        # Sort follower notes by start time for efficient lookup
        sorted_notes = sorted(notes, key=lambda n: n.start)

        result = []
        for onset, dur in onset_durs:
            # Find the follower note whose start is closest to this onset
            best = min(sorted_notes, key=lambda n: abs(n.start - onset))
            # Pick one note per onset — no duplicates from polyphony
            result.append(NoteInfo(
                pitch=best.pitch,
                start=onset,
                duration=max(0.05, dur),
                velocity=best.velocity,
                absolute=best.absolute,
                articulation=best.articulation,
                expression=dict(best.expression) if best.expression else {},
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


@dataclass
class RhythmicDensityModifier(PhraseModifier):
    """
    Adjusts the density of the phrase by randomly removing notes.
    density: 0.0 to 1.0. If < 1.0, notes are randomly dropped.
    """

    density: float = 1.0

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if self.density >= 1.0:
            return notes
        if self.density <= 0.0:
            return []

        import random

        result = [n for n in notes if random.random() < self.density]
        return result


@dataclass
class PolyrhythmLayerModifier:
    """
    Overlays a second rhythmic layer over existing notes to create a polyrhythm.
    E.g. 3 over 4.
    Original notes are kept, but new notes are added on a different grid.
    """

    tuple_count: int = 3  # e.g. 3 in 3:4
    base_count: int = 4  # e.g. 4 in 3:4
    velocity_scale: float = 0.7

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []

        # Find the range of current notes
        start = min(n.start for n in notes)
        end = max(n.start + n.duration for n in notes)
        total_beats = end - start

        # New grid step
        # For 3 over 4, if total duration is 4 beats, we want 3 notes.
        # step = 4 / 3
        step = (self.base_count / self.tuple_count)
        
        result = list(notes)
        t = start
        while t < end:
            # Pick a pitch from existing notes at this time (or nearest)
            closest_n = min(notes, key=lambda n: abs(n.start - t))
            
            result.append(
                NoteInfo(
                    pitch=closest_n.pitch,
                    start=round(t, 6),
                    duration=round(step * 0.8, 6),
                    velocity=int(closest_n.velocity * self.velocity_scale),
                    absolute=closest_n.absolute,
                )
            )
            t += step
            
        return sorted(result, key=lambda x: x.start)


@dataclass
class AdaptiveSwingModifier:
    """
    Applies swing that changes dynamically across the phrase.
    'start_swing' to 'end_swing' ramp.
    """

    start_swing: float = 0.5
    end_swing: float = 0.7
    grid: float = 0.5

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []

        total_len = context.duration_beats
        result = []
        for n in notes:
            progress = n.start / total_len
            current_swing = self.start_swing + (self.end_swing - self.start_swing) * progress
            
            if current_swing <= 0.5 or self.grid <= 0:
                result.append(n)
                continue

            delay = (current_swing - 0.5) * 2.0 * (self.grid / 2.0)
            grid_pos = (n.start % self.grid)
            is_offbeat = abs(grid_pos - (self.grid / 2.0)) < 0.05
            
            new_start = n.start + delay if is_offbeat else n.start
            result.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=round(new_start, 6),
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute,
                )
            )
        return result


@dataclass
class MetricAccentModifier(PhraseModifier):
    """
    Applies velocity accents based on metric weight (strong vs weak beats).
    E.g., in 4/4: Beat 1 is strongest, Beat 3 is strong, 2 and 4 are weak, offbeats are weakest.
    """

    strength: float = 0.2  # 0.0 to 1.0 intensity of the effect
    time_sig: tuple[int, int] = (4, 4)

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        num, den = self.time_sig
        
        result = []
        for n in notes:
            # Position within the measure (0.0 to num)
            pos = n.start % num
            
            # Metric weight logic (0.0 to 1.0)
            weight = 0.5  # base
            
            if pos < 0.05: # Downbeat (1)
                weight = 1.0
            elif abs(pos - num / 2.0) < 0.05: # Mid-point (3 in 4/4)
                weight = 0.85
            elif abs(pos % 1.0) < 0.05: # Other quarter beats (2, 4)
                weight = 0.7
            elif abs(pos % 0.5) < 0.05: # 8th notes
                weight = 0.5
            else: # 16th or deeper
                weight = 0.3
                
            # Scale velocity based on weight and strength
            factor = 1.0 + (weight - 0.7) * self.strength
            new_vel = int(n.velocity * factor)
            new_vel = max(1, min(127, new_vel))
            
            result.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=new_vel,
                absolute=n.absolute,
                articulation=n.articulation,
                expression=dict(n.expression)
            ))
        return result
