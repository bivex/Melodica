"""
generators/guitar_legato.py — Guitar legato technique generator.

Layer: Application / Domain
Style: Shred, prog rock, metal, fusion.

Legato guitar playing uses hammer-ons and pull-offs for smooth,
connected notes without re-picking. Creates fast scalar runs
with a fluid, singing quality.

Patterns:
    "ascending"   — ascending scale legato
    "descending"  — descending scale legato
    "zigzag"      — ascending then descending
    "string_skip" — skip strings for wider intervals
    "tapping"     — two-hand tapping pattern
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class GuitarLegatoGenerator(PhraseGenerator):
    """
    Guitar legato (hammer-on/pull-off) generator.

    direction:
        "ascending", "descending", "zigzag", "string_skip", "tapping"
    notes_per_string:
        Notes played on each string before shifting (3–6).
    speed:
        Duration of each note in beats.
    use_scale:
        If True, follow the key scale. If False, use chromatic.
    palm_mute_start:
        Start each phrase with a palm-muted note.
    """

    name: str = "Guitar Legato Generator"
    direction: str = "ascending"
    notes_per_string: int = 4
    speed: float = 0.125
    use_scale: bool = True
    palm_mute_start: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        direction: str = "ascending",
        notes_per_string: int = 4,
        speed: float = 0.125,
        use_scale: bool = True,
        palm_mute_start: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.direction = direction
        self.notes_per_string = max(3, min(6, notes_per_string))
        self.speed = max(0.03125, min(0.5, speed))
        self.use_scale = use_scale
        self.palm_mute_start = palm_mute_start
        self.rhythm = rhythm

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
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        mid = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else mid
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pitch_seq = self._build_run(chord, key, prev_pitch, low, high)
            t = event.onset
            end = event.onset + event.duration
            vel = self._velocity()
            idx = 0

            for pitch in pitch_seq:
                if t >= end:
                    break
                n_dur = min(self.speed, end - t)

                # First note: palm mute
                v = int(vel * 0.6) if (idx == 0 and self.palm_mute_start) else vel

                notes.append(
                    NoteInfo(
                        pitch=max(low, min(high, pitch)),
                        start=round(t, 6),
                        duration=n_dur * 0.9,
                        velocity=max(1, min(127, v)),
                    )
                )
                t += self.speed
                idx += 1

            if pitch_seq:
                prev_pitch = pitch_seq[-1]

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_run(
        self, chord: ChordLabel, key: Scale, prev: int, low: int, high: int
    ) -> list[int]:
        degs = key.degrees()
        if not degs:
            return [prev]

        nps = self.notes_per_string
        total_notes = nps * 4  # 4 "strings"

        if self.direction == "ascending":
            pitches = [prev + i for i in range(total_notes)]
            if self.use_scale:
                pitches = [
                    nearest_pitch(int(degs[i % len(degs)]), prev + i * 2)
                    for i in range(total_notes)
                ]
            return pitches

        elif self.direction == "descending":
            pitches = [prev - i for i in range(total_notes)]
            if self.use_scale:
                pitches = [
                    nearest_pitch(int(degs[i % len(degs)]), prev - i * 2)
                    for i in range(total_notes)
                ]
            return pitches

        elif self.direction == "zigzag":
            up = [prev + i for i in range(total_notes // 2)]
            down = [up[-1] - i for i in range(total_notes // 2)]
            if self.use_scale:
                up = [
                    nearest_pitch(int(degs[i % len(degs)]), prev + i)
                    for i in range(total_notes // 2)
                ]
                down = [
                    nearest_pitch(int(degs[i % len(degs)]), up[-1] - i)
                    for i in range(total_notes // 2)
                ]
            return up + down

        elif self.direction == "string_skip":
            # Wider intervals
            return [prev + (i * 5 if i % 2 == 0 else i * 2) for i in range(total_notes)]

        else:  # tapping
            # Alternating between two wide positions
            pos_a = prev
            pos_b = prev + 12
            return [
                pos_a + (i % nps) if i < total_notes // 2 else pos_b - (i % nps)
                for i in range(total_notes)
            ]

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(2.0, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += dur + random.uniform(0.5, 1.5)
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 30)
