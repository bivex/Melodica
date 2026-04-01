"""
generators/ambient.py — Ambience / Background Music Generator.

Layer: Application / Domain
Features: Long, evolving notes, soft velocities, and wide spread voicings for textures.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica import types
from melodica.utils import chord_pitches_spread, chord_pitches_open, chord_at


@dataclass
class AmbientPadGenerator(PhraseGenerator):
    """
    Generates long, ethereal chord pads for background music / Lo-Fi ambient.
    Uses spread voicings and soft velocity curves.
    """

    name: str = "Ambient Pad Generator"
    voicing: str = "spread"  # "open", "spread"
    overlap: float = 0.1  # overlap in beats between chords for smoothness
    rhythm: RhythmGenerator | None = None
    note_range_low: int | None = None
    note_range_high: int | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        voicing: str = "spread",
        overlap: float = 0.1,
        rhythm: RhythmGenerator | None = None,
        note_range_low: int | None = None,
        note_range_high: int | None = None,
    ) -> None:
        super().__init__(params)
        self.voicing = voicing
        self.overlap = overlap
        self.rhythm = rhythm
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high
        self._last_context: RenderContext | None = None

    def render(
        self,
        chords: list[types.ChordLabel],
        key: types.Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[types.NoteInfo]:
        if not chords:
            return []

        notes: list[types.NoteInfo] = []
        voicing_fn = chord_pitches_spread if self.voicing == "spread" else chord_pitches_open

        # Base velocity for ambient (soft)
        base_vel = int(40 + self.params.density * 20)

        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )

        last_chord = chords[-1]
        last_voicing_pitches: list[int] = []
        prev_pitches: list[int] = (
            list(context.prev_pitches) if context and context.prev_pitches else []
        )

        if self.rhythm is not None:
            events = self._build_events(duration_beats)
            for event in events:
                chord = chord_at(chords, event.onset)
                if chord is None:
                    continue
                last_chord = chord
                pitches = voicing_fn(chord, self.params.key_range_low)
                pitches = [p for p in pitches if low <= p <= high]

                # Voice lead: shift pitches to minimize movement from previous
                if prev_pitches:
                    pitches = self._voice_lead(pitches, prev_pitches)
                prev_pitches = pitches
                last_voicing_pitches = pitches
                duration = event.duration

                for p in pitches:
                    note_vel = base_vel + random.randint(-5, 5)
                    notes.append(
                        types.NoteInfo(
                            pitch=p,
                            start=round(event.onset, 6),
                            duration=duration,
                            velocity=max(1, min(127, note_vel)),
                        )
                    )
        else:
            for chord in chords:
                pitches = voicing_fn(chord, self.params.key_range_low)
                pitches = [p for p in pitches if low <= p <= high]

                # Voice lead
                if prev_pitches:
                    pitches = self._voice_lead(pitches, prev_pitches)
                prev_pitches = pitches
                last_chord = chord
                last_voicing_pitches = pitches

                duration = chord.duration + self.overlap

                for p in pitches:
                    note_vel = base_vel + random.randint(-5, 5)
                    notes.append(
                        types.NoteInfo(
                            pitch=p,
                            start=chord.start,
                            duration=duration,
                            velocity=max(1, min(127, note_vel)),
                        )
                    )

        notes = self._apply_phrase_arch(
            notes, duration_beats, context.phrase_position if context else 0.0
        )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                last_pitches=last_voicing_pitches,
            )

        return notes

    def _voice_lead(self, new_pitches: list[int], prev_pitches: list[int]) -> list[int]:
        """Shift new pitches by octaves to minimize movement from previous chord."""
        if not prev_pitches or not new_pitches:
            return new_pitches
        # Find median of each set
        prev_median = sorted(prev_pitches)[len(prev_pitches) // 2]
        new_median = sorted(new_pitches)[len(new_pitches) // 2]
        diff = prev_median - new_median
        octave_shift = round(diff / 12) * 12
        shifted = [p + octave_shift for p in new_pitches]
        # Clamp to range
        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )
        return [max(low, min(high, p)) for p in shifted]

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Shouldn't be called in no-rhythm path, but provide fallback
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=1.9))
            t += 2.0
        return events

    def _apply_phrase_arch(self, notes, duration_beats, phrase_position=0.0):
        if not notes or duration_beats <= 0:
            return notes
        arch_height = 0.3 + 0.2 * phrase_position
        for note in notes:
            progress = note.start / duration_beats
            arch = 1.0 - arch_height + arch_height * math.sin(progress * math.pi * 0.7)
            note.velocity = max(1, min(127, int(note.velocity * arch)))
        return notes
