"""
generators/staccato.py — Strings Staccato Generator.

Layer: Application / Domain
High-density, short duration notes designed for orchestral staccato ostinatos.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica import types
from melodica.utils import nearest_pitch_above, pitch_class, chord_at


@dataclass
class StringsStaccatoGenerator(PhraseGenerator):
    """
    Generates rhythmic strings staccato patterns.
    High energy, often doubling roots or playing tight chord voicings.
    """

    name: str = "Strings Staccato Generator"
    rhythm: RhythmGenerator | None = None
    style: str = "octaves"  # "roots", "octaves", "triad", "shell"
    note_range_low: int | None = None
    note_range_high: int | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        rhythm: RhythmGenerator | None = None,
        style: str = "octaves",
        note_range_low: int | None = None,
        note_range_high: int | None = None,
    ) -> None:
        super().__init__(params)
        self.rhythm = rhythm
        self.style = style
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

        events = self._build_events(duration_beats)
        notes: list[types.NoteInfo] = []
        last_chord = chords[0]
        last_pitches: list[int] = []

        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord
            pitches = self._get_pitches(chord, key)
            pitches = [p for p in pitches if low <= p <= high]
            last_pitches = pitches

            # Staccato is always short
            staccato_dur = min(event.duration, 0.2)

            base_vel = int(70 + self.params.density * 40)
            vel = int(base_vel * event.velocity_factor)

            for p in pitches:
                note_vel = max(1, min(127, vel + random.randint(-8, 8)))
                notes.append(
                    types.NoteInfo(
                        pitch=p,
                        start=round(event.onset, 6),
                        duration=staccato_dur,
                        velocity=note_vel,
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
                last_pitches=last_pitches,
            )

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        # Default: 8th or 16th notes based on density
        step = 0.5 if self.params.density < 0.7 else 0.25
        t, events = 0.0, []
        while t < duration_beats:
            events.append(
                RhythmEvent(onset=t, duration=step, velocity_factor=1.0 if t % 1.0 < 0.1 else 0.8)
            )
            t += step
        return events

    def _get_pitches(self, chord: types.ChordLabel, key: types.Scale) -> list[int]:
        root = chord.root
        low = self.params.key_range_low

        if self.style == "roots":
            return [nearest_pitch_above(root, low)]
        elif self.style == "octaves":
            p1 = nearest_pitch_above(root, low)
            p2 = p1 + types.OCTAVE
            return [p1, p2] if p2 <= self.params.key_range_high else [p1]
        elif self.style == "shell":
            # Shell voicing: root + 3rd + 7th (or 5th if no 7th)
            pcs = chord.pitch_classes()
            shell_pcs = [pcs[0]]  # root
            if len(pcs) >= 3:
                shell_pcs.append(pcs[2])  # 5th
            if len(pcs) >= 4:
                shell_pcs.append(pcs[3])  # 7th
            elif len(pcs) >= 2:
                shell_pcs.append(pcs[1])  # 3rd
            return [nearest_pitch_above(pc, low) for pc in shell_pcs]
        else:  # triad
            pcs = chord.pitch_classes()[:3]
            # Filter by key — only include scale tones
            return [nearest_pitch_above(pc, low) for pc in pcs if key.contains(pc)]

    def _apply_phrase_arch(self, notes, duration_beats, phrase_position=0.0):
        if not notes or duration_beats <= 0:
            return notes
        arch_height = 0.3 + 0.2 * phrase_position
        for note in notes:
            progress = note.start / duration_beats
            arch = 1.0 - arch_height + arch_height * math.sin(progress * math.pi * 0.7)
            note.velocity = max(1, min(127, int(note.velocity * arch)))
        return notes
