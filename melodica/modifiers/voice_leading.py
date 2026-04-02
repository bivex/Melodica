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
modifiers/voice_leading.py — VoiceLeadingModifier.

Layer: Application / Modifier
"""

from __future__ import annotations

from melodica import types
from melodica.modifiers import ModifierContext, PhraseModifier
from melodica.types import NoteInfo
from melodica.utils import pitch_class, nearest_pitch


class VoiceLeadingModifier(PhraseModifier):
    """
    Minimizes jumps between notes by shifting entire phrase octaves
    based on the 'center of mass' of previous melodic content.

    This is a stateful-ish modifier that looks at the transition
    between segments to ensure smooth horizontal flow.
    """

    def __init__(self, target_octave: int | None = None) -> None:
        """
        target_octave: If set, tries to anchor the first note near this octave.
                       Otherwise uses the first note as is.
        """
        super().__init__()
        self.target_octave = target_octave

    def modify(self, notes: list[types.NoteInfo], context: ModifierContext) -> list[types.NoteInfo]:
        if not notes:
            return []

        # 1. Sort notes by onset
        sorted_notes = sorted(notes, key=lambda n: n.start)

        # 2. Group notes by chord segments
        # (Assuming notes within a chord segment are already voiced okay,
        # we want to fix the LEAPS between segments).

        chords = context.chords
        if not chords:
            return notes

        modified_notes: list[NoteInfo] = []

        # Track the "ideal" pitch center to follow
        # Start with the first note's pitch or the target
        if self.target_octave is not None:
            first_pc = pitch_class(sorted_notes[0].pitch)
            ideal_center = self.target_octave * types.OCTAVE + first_pc
        else:
            ideal_center = sorted_notes[0].pitch

        # Track actual pitch range to prevent drift
        running_min = ideal_center
        running_max = ideal_center

        # Iterate through notes and nudge them toward the ideal_center
        # when a new chord segment starts.

        current_chord_idx = -1
        octave_shift = 0

        for n in sorted_notes:
            # Find which chord this note belongs to
            chord_idx = self._find_chord_idx(n.start, chords)

            if chord_idx != current_chord_idx:
                # NEW CHORD SEGMENT: Calculate new octave shift
                # We want to find the shift that brings this note (and its chord-mates)
                # closest to the last 'ideal_center'

                original_pitch = n.pitch
                best_pitch = nearest_pitch(pitch_class(original_pitch), ideal_center)
                octave_shift = (best_pitch - original_pitch) // 12

                # Clamp octave shift to ±2 octaves to prevent wild jumps
                octave_shift = max(-2, min(2, octave_shift))

                current_chord_idx = chord_idx

            # Apply the shift
            new_pitch = n.pitch + (octave_shift * types.OCTAVE)

            # Prevent voice crossing: keep pitch within the running range ±1 octave
            pitch_floor = running_min - types.OCTAVE
            pitch_ceil = running_max + types.OCTAVE
            while new_pitch < pitch_floor:
                new_pitch += types.OCTAVE
            while new_pitch > pitch_ceil:
                new_pitch -= types.OCTAVE

            # Constrain to MIDI range
            low_bound = types.OCTAVE  # C1
            high_bound = types.MIDI_MAX - types.OCTAVE  # C9 (approx)

            while new_pitch < low_bound:
                new_pitch += types.OCTAVE
            while new_pitch > high_bound:
                new_pitch -= types.OCTAVE

            modified_notes.append(
                types.NoteInfo(
                    pitch=new_pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute,
                )
            )

            # Update running range (prevents drift)
            running_min = min(running_min, new_pitch)
            running_max = max(running_max, new_pitch)

            # Move the ideal center towards the newly placed note (smoothing)
            # Use a bounded EMA that can't drift beyond the running range
            ideal_center = (ideal_center * 0.7) + (new_pitch * 0.3)
            ideal_center = max(running_min, min(running_max, ideal_center))

        return sorted(modified_notes, key=lambda n: n.start)

    def _find_chord_idx(self, start: float, chords: list) -> int:
        for i, c in enumerate(reversed(chords)):
            if c.start <= start:
                return len(chords) - 1 - i
        return 0
