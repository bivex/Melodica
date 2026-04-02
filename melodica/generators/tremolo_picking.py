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
generators/tremolo_picking.py — Tremolo picking generator.

Layer: Application / Domain
Style: Guitar metal/punk, violin tremolo, mandolin.

Rapid repetition of a single pitch. Unlike trill (which alternates between
two notes), tremolo picking repeats the same note as fast as possible.

Variants:
    "single"   — tremolo on one pitch
    "dyad"     — tremolo on a power chord (root + fifth)
    "octave"   — tremolo on root + octave
    "melodic"  — tremolo on successive chord tones (changes pitch per bar)
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
class TremoloPickingGenerator(PhraseGenerator):
    """
    Tremolo picking: rapid repetition of the same pitch(es).

    variant:
        "single", "dyad", "octave", "melodic"
    speed:
        Subdivision in beats (0.0625 = very fast, 0.125 = fast, 0.25 = moderate).
    palm_mute_probability:
        Probability of palm-muted (lower velocity, shorter) notes.
    note_strategy:
        How to pick the base note: "chord_root", "chord_tone", "fifth".
    """

    name: str = "Tremolo Picking Generator"
    variant: str = "single"
    speed: float = 0.125
    palm_mute_probability: float = 0.0
    note_strategy: str = "chord_root"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "single",
        speed: float = 0.125,
        palm_mute_probability: float = 0.0,
        note_strategy: str = "chord_root",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.speed = max(0.03125, min(0.5, speed))
        self.palm_mute_probability = max(0.0, min(1.0, palm_mute_probability))
        self.note_strategy = note_strategy
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
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pitches = self._pick_pitches(chord, prev_pitch, low, high)
            end = min(event.onset + event.duration, duration_beats)
            t = event.onset
            vel = self._velocity()
            is_muted = random.random() < self.palm_mute_probability

            if is_muted:
                vel = int(vel * 0.65)

            while t < end:
                for p in pitches:
                    if t >= end:
                        break
                    n_dur = min(self.speed, end - t)
                    if is_muted:
                        n_dur *= 0.5
                    notes.append(
                        NoteInfo(
                            pitch=max(low, min(high, p)),
                            start=round(t, 6),
                            duration=n_dur * 0.85,
                            velocity=max(1, min(127, vel + random.randint(-3, 3))),
                        )
                    )
                    t += self.speed

            if pitches:
                prev_pitch = pitches[0]

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_pitches(self, chord: ChordLabel, prev: int, low: int, high: int) -> list[int]:
        if self.note_strategy == "chord_root":
            base = nearest_pitch(chord.root, prev)
        elif self.note_strategy == "fifth":
            fifth_pc = (chord.root + 7) % 12
            base = nearest_pitch(fifth_pc, prev)
        else:
            pcs = chord.pitch_classes()
            pc = random.choice(pcs) if pcs else chord.root
            base = nearest_pitch(pc, prev)

        base = max(low, min(high, base))

        if self.variant == "single":
            return [base]
        elif self.variant == "dyad":
            fifth = nearest_pitch((chord.root + 7) % 12, base + 5)
            return [base, max(low, min(high, fifth))]
        elif self.variant == "octave":
            return [base, min(127, base + 12)]
        elif self.variant == "melodic":
            pcs = chord.pitch_classes()
            if len(pcs) > 1:
                return [max(low, min(high, nearest_pitch(int(pc), base))) for pc in pcs[:2]]
            return [base]
        return [base]

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(4.0, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += 4.0
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 35)
