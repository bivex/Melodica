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
generators/chord_gen.py — ChordGenerator.

Layer: Application / Domain

Outputs block chords (all tones simultaneous) at onsets derived from
rhythm_pattern / density, using the selected voicing strategy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import (
    chord_pitches_closed,
    chord_pitches_open,
    chord_pitches_spread,
    chord_at,
    voice_leading_distance,
    snap_to_scale,
)


VOICINGS = frozenset({"closed", "open", "spread"})

_VOICING_FN = {
    "closed": chord_pitches_closed,
    "open": chord_pitches_open,
    "spread": chord_pitches_spread,
}


@dataclass
class ChordGenerator(PhraseGenerator):
    """
    Block-chord generator.

    voicing:        "closed" | "open" | "spread"
    rhythm_pattern: explicit onset list in beats; None = auto from density
    """

    name: str = "Chord Generator"
    voicing: str = "closed"
    notes_to_use: list[int] | None = None  # chord tone indices (0=root, 1=3rd, ...)
    add_bass_note: int = 0  # 0 = off, -1/-2/-3/-4 = octave transpose
    rhythm: RhythmGenerator | None = None
    note_range_low: int | None = None
    note_range_high: int | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        voicing: str = "closed",
        notes_to_use: list[int] | None = None,
        add_bass_note: int = 0,
        rhythm: RhythmGenerator | None = None,
        note_range_low: int | None = None,
        note_range_high: int | None = None,
    ) -> None:
        super().__init__(params)
        if voicing not in VOICINGS:
            raise ValueError(f"voicing must be one of {sorted(VOICINGS)}; got {voicing!r}")
        self.voicing = voicing
        self.notes_to_use = notes_to_use
        self.add_bass_note = max(-4, min(0, add_bass_note))
        self.rhythm = rhythm
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high
        self._last_context = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        voicing_fn = _VOICING_FN[self.voicing]
        notes: list[NoteInfo] = []
        prev_pitches = context.prev_pitches if context and context.prev_pitches else []

        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )

        last_chord: ChordLabel | None = None
        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue

            last_chord = chord
            best_inv = self._best_inversion(chord, prev_pitches, self.params.key_range_low)
            voiced_chord = ChordLabel(
                root=chord.root,
                quality=chord.quality,
                extensions=list(chord.extensions),
                bass=chord.bass,
                inversion=best_inv,
                start=chord.start,
                duration=chord.duration,
                degree=chord.degree,
                function=chord.function,
            )
            pitches = voicing_fn(voiced_chord, self.params.key_range_low)

            # Filter by notes_to_use
            if self.notes_to_use is not None:
                pitches = [pitches[i] for i in self.notes_to_use if i < len(pitches)]

            pitches = [p for p in pitches if low <= p <= high]
            base_vel = self._velocity()
            vel = int(base_vel * event.velocity_factor)

            for pitch in pitches:
                notes.append(
                    NoteInfo(
                        pitch=snap_to_scale(pitch, key),
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(0, min(127, vel)),
                    )
                )

            # Add bass note
            if self.add_bass_note < 0 and pitches:
                bass_pitch = pitches[0] + self.add_bass_note * 12
                bass_pitch = max(self.params.key_range_low, bass_pitch)
                notes.append(
                    NoteInfo(
                        pitch=bass_pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(0, min(127, vel - 10)),
                    )
                )

            prev_pitches = pitches

        notes = self._apply_phrase_arch(
            notes, duration_beats, context.phrase_position if context else 0.0
        )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                last_pitches=prev_pitches,
                duration_beats=duration_beats,
                total_duration=duration_beats,
            )
        else:
            self._last_context = (context or RenderContext()).with_end_state(
                duration_beats=duration_beats,
                total_duration=duration_beats,
            )

        return notes

    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Auto: evenly spaced from density
        step = max(0.5, (1.0 - self.params.density) * 4.0)
        t, events = 0.0, []
        while t < duration_beats:
            dur = max(0.25, step - 0.02)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += step
        return events

    def _best_inversion(self, chord: ChordLabel, prev_pitches: list[int], bass_midi: int) -> int:
        """Pick inversion (0, 1, 2) that minimizes voice movement."""
        if not prev_pitches:
            return 0
        best_inv, best_dist = 0, float("inf")
        for inv in range(min(3, len(chord.pitch_classes()))):
            test_chord = ChordLabel(
                root=chord.root,
                quality=chord.quality,
                extensions=list(chord.extensions),
                bass=chord.bass,
                inversion=inv,
                start=chord.start,
                duration=chord.duration,
                degree=chord.degree,
                function=chord.function,
            )
            pitches = chord_pitches_closed(test_chord, bass_midi)
            dist = voice_leading_distance(prev_pitches, pitches)
            if dist < best_dist:
                best_dist = dist
                best_inv = inv
        return best_inv

    def _velocity(self) -> int:
        return int(60 + self.params.density * 40)

    def _apply_phrase_arch(self, notes, duration_beats, phrase_position=0.0):
        if not notes or duration_beats <= 0:
            return notes
        arch_height = 0.3 + 0.2 * phrase_position
        for note in notes:
            progress = note.start / duration_beats
            arch = 1.0 - arch_height + arch_height * math.sin(progress * math.pi * 0.7)
            note.velocity = max(1, min(127, int(note.velocity * arch)))
        return notes
