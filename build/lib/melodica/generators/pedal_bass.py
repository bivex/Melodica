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
generators/pedal_bass.py — PedalBassGenerator.

Organ pedal point / sustained bass note under chord changes.
Foundation for any harmony — classical, ambient, EDM bass drop.
"""

from __future__ import annotations

from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE
from melodica.utils import nearest_pitch, nearest_pitch_above, chord_at


@dataclass
class PedalBassGenerator(PhraseGenerator):
    """
    Sustained bass note (pedal point) under changing chords.

    pedal_note:    "root" | "fifth" | "both"
    sustain:       sustain duration in beats (0 = chord duration)
    velocity_level: 0.0-1.0, how loud the pedal is relative to full velocity
    """

    name: str = "Pedal Bass Generator"
    pedal_note: str = "root"
    sustain: float = 0.0
    velocity_level: float = 0.8
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pedal_note: str = "root",
        sustain: float = 0.0,
        velocity_level: float = 0.8,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pedal_note = pedal_note
        self.sustain = max(0.0, sustain)
        self.velocity_level = max(0.0, min(1.0, velocity_level))
        self.rhythm = rhythm
        self._last_context: RenderContext | None = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        notes: list[NoteInfo] = []
        low = max(36, self.params.key_range_low)  # Bass register
        last_chord = chords[0]

        # Use first chord's root as the pedal (or all chord roots)
        for chord in chords:
            last_chord = chord
            root_pc = chord.bass if chord.bass is not None else chord.root
            pitch = nearest_pitch_above(root_pc, self.params.key_range_low)

            # Clamp to range
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            dur = self.sustain if self.sustain > 0 else chord.duration
            vel = int(self._velocity() * self.velocity_level)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=max(1, min(127, vel)),
                )
            )

            # Add fifth if pedal_note == "both"
            if self.pedal_note == "both":
                fifth_pc = (root_pc + 7) % 12
                fifth_pitch = nearest_pitch_above(fifth_pc, self.params.key_range_low)
                fifth_pitch = max(
                    self.params.key_range_low, min(self.params.key_range_high, fifth_pitch)
                )
                notes.append(
                    NoteInfo(
                        pitch=fifth_pitch,
                        start=round(chord.start, 6),
                        duration=round(dur, 6),
                        velocity=max(1, min(127, vel - 10)),
                    )
                )
            elif self.pedal_note == "fifth":
                fifth_pc = (root_pc + 7) % 12
                fifth_pitch = nearest_pitch_above(fifth_pc, self.params.key_range_low)
                fifth_pitch = max(
                    self.params.key_range_low, min(self.params.key_range_high, fifth_pitch)
                )
                # Replace root with fifth
                notes[-1] = NoteInfo(
                    pitch=fifth_pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=max(1, min(127, vel)),
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        return []

    def _velocity(self) -> int:
        return int(60 + self.params.density * 40)
