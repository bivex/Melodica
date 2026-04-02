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
generators/glissando.py — Glissando / portamento generator.

Layer: Application / Domain
Style: Jazz, orchestral, pop, electronic.

A glissando slides through pitches between a start note and a target note.
In MIDI terms, this is rendered as a rapid succession of pitches.

Types:
    "up"        — ascending glissando
    "down"      — descending glissando
    "chromatic" — all semitones
    "diatonic"  — only scale tones
    "pentatonic" — pentatonic scale tones
    "arpeggio"  — chord tones only
    "random"    — random direction per event
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
class GlissandoGenerator(PhraseGenerator):
    """
    Glissando / portamento generator.

    gliss_type:
        Direction and pitch set for the glissando.
    speed:
        Duration of each note in the gliss (0.03125 = very fast).
    gliss_length:
        Total duration in beats of each glissando event.
    start_note:
        Where the gliss starts relative to target:
        "above" — start above and slide down to target
        "below" — start below and slide up to target
        "octave" — start one octave away
    """

    name: str = "Glissando Generator"
    gliss_type: str = "chromatic"
    speed: float = 0.0625
    gliss_length: float = 1.0
    start_note: str = "octave"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        gliss_type: str = "chromatic",
        speed: float = 0.0625,
        gliss_length: float = 1.0,
        start_note: str = "octave",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if gliss_type not in (
            "up",
            "down",
            "chromatic",
            "diatonic",
            "pentatonic",
            "arpeggio",
            "random",
        ):
            raise ValueError(f"Unknown gliss_type: {gliss_type!r}")
        self.gliss_type = gliss_type
        self.speed = max(0.02, min(0.25, speed))
        self.gliss_length = max(0.25, min(8.0, gliss_length))
        self.start_note = start_note
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

            target = nearest_pitch(chord.root, prev_pitch)
            target = max(low, min(high, target))

            dur = min(self.gliss_length, duration_beats - event.onset)
            if dur <= 0:
                continue

            gliss_notes = self._render_gliss(chord, key, target, event.onset, dur, low, high)
            notes.extend(gliss_notes)
            if gliss_notes:
                prev_pitch = gliss_notes[-1].pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_gliss(
        self,
        chord: ChordLabel,
        key: Scale,
        target: int,
        onset: float,
        dur: float,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        # Determine pitch set
        if self.gliss_type == "chromatic":
            all_pcs = list(range(12))
        elif self.gliss_type == "diatonic":
            all_pcs = [int(d) for d in key.degrees()]
        elif self.gliss_type == "pentatonic":
            all_pcs = [int(d) for d in key.degrees()][:5]
        elif self.gliss_type == "arpeggio":
            all_pcs = chord.pitch_classes()
        else:
            all_pcs = list(range(12))

        if not all_pcs:
            all_pcs = [target % 12]

        # Determine direction
        if self.gliss_type in ("up", "down"):
            ascending = self.gliss_type == "up"
        elif self.gliss_type == "random":
            ascending = random.choice([True, False])
        else:
            ascending = True  # default: ascending into target

        # Determine start pitch
        if self.start_note == "octave":
            start = target + (12 if ascending else -12)
        elif self.start_note == "above":
            start = target + 7
        else:
            start = target - 7
        start = max(low, min(high, start))

        # Build pitch sequence
        if ascending:
            direction = 1 if start <= target else -1
        else:
            direction = -1 if start >= target else 1

        pitches: list[int] = []
        p = start
        while True:
            if (direction > 0 and p >= target) or (direction < 0 and p <= target):
                break
            pc = p % 12
            if pc in all_pcs or self.gliss_type == "chromatic" or self.gliss_type == "random":
                pitches.append(max(low, min(high, p)))
            p += direction
            if abs(p - start) > 24:  # safety limit
                break

        # Always end on target
        if not pitches or pitches[-1] != target:
            pitches.append(target)

        # Limit to duration
        max_notes = int(dur / self.speed)
        if len(pitches) > max_notes:
            step = len(pitches) / max_notes
            pitches = [pitches[int(i * step)] for i in range(max_notes)]
            if pitches[-1] != target:
                pitches.append(target)

        # Render
        notes: list[NoteInfo] = []
        t = onset
        vel = self._velocity()
        for i, p in enumerate(pitches):
            n_dur = min(self.speed, onset + dur - t)
            if n_dur <= 0:
                break
            # Crescendo into target
            v = int(vel * (0.6 + 0.4 * (i / max(len(pitches) - 1, 1))))
            notes.append(
                NoteInfo(
                    pitch=max(low, min(high, p)),
                    start=round(t, 6),
                    duration=n_dur * 0.9,
                    velocity=max(1, min(127, v)),
                )
            )
            t += self.speed

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=self.gliss_length))
            t += self.gliss_length + 1.0
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 35)
