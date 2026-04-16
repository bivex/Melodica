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
generators/synth_bass.py — Electronic synth bass pattern generator.

Layer: Application / Domain
Style: Acid house, techno, EDM, dubstep, drum & bass.

Synth bass differs from acoustic bass in its use of slides (portamento),
filter sweeps, and characteristic electronic timbres. This generator
creates rhythmic patterns with pitch slides and articulation variations.

Waveforms:
    "saw"    — sawtooth (aggressive, rich harmonics)
    "square" — square wave (hollow, classic acid)
    "sine"   — sine wave (clean sub-bass)
    "acid"   — TB-303 style with slides and accents

Patterns:
    "acid_line"  — classic acid pattern (eighth notes with slides)
    "reese"      — deep reese bass (long notes, detuned)
    "sub_kick"   — sub-bass hits synchronized with kick
    "wobble"     — dubstep wobble rhythm
    "plucked"    — short plucked bass
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


ACID_PATTERN = [0.0, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 2.75, 3.0, 3.5]
WOBBLE_PATTERN = [0.0, 0.67, 1.33, 2.0, 2.67, 3.33]


@dataclass
class SynthBassGenerator(PhraseGenerator):
    """
    Electronic synth bass pattern generator.

    waveform:
        "saw", "square", "sine", "acid"
    pattern:
        "acid_line", "reese", "sub_kick", "wobble", "plucked"
    slide_probability:
        Probability of portamento between notes (acid character).
    octave_variation:
        Probability of jumping octave on accent notes.
    filter_accent:
        Velocity boost for accented notes (simulates filter opening).
    """

    name: str = "Synth Bass Generator"
    waveform: str = "acid"
    pattern: str = "acid_line"
    slide_probability: float = 0.3
    octave_variation: float = 0.15
    filter_accent: float = 1.2
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        waveform: str = "acid",
        pattern: str = "acid_line",
        slide_probability: float = 0.3,
        octave_variation: float = 0.15,
        filter_accent: float = 1.2,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.waveform = waveform
        self.pattern = pattern
        self.slide_probability = max(0.0, min(1.0, slide_probability))
        self.octave_variation = max(0.0, min(1.0, octave_variation))
        self.filter_accent = max(1.0, min(1.5, filter_accent))
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
        low = max(24, self.params.key_range_low)
        mid = low + 24

        prev_pitch = low + 12
        last_chord: ChordLabel | None = None
        prev_slide = False

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pitch = self._pick_pitch(chord, prev_pitch, low, mid, key)
            is_slide = random.random() < self.slide_probability and prev_slide is False
            is_accent = random.random() < 0.3

            vel = self._velocity(is_accent)

            if is_slide and prev_pitch != pitch:
                # Slide note: short grace note before target
                slide_from = prev_pitch
                notes.append(
                    NoteInfo(
                        pitch=slide_from,
                        start=round(event.onset, 6),
                        duration=event.duration * 0.3,
                        velocity=int(vel * 0.7),
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(event.onset + event.duration * 0.25, 6),
                        duration=event.duration * 0.7,
                        velocity=vel,
                    )
                )
            else:
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=vel,
                    )
                )

            prev_pitch = pitch
            prev_slide = is_slide

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_pitch(self, chord: ChordLabel, prev: int, low: int, mid: int, key: Scale | None = None) -> int:
        root_pc = chord.root

        if self.pattern == "reese":
            # Reese: root + slight detune (one note per bar)
            return max(low, min(mid, nearest_pitch(root_pc, prev)))

        elif self.pattern == "sub_kick":
            # Sub: root, very low
            return max(low, min(low + 12, nearest_pitch(root_pc, low + 6)))

        elif self.pattern == "wobble":
            # Wobble: root and fifth
            if random.random() < 0.4:
                fifth_pc = (root_pc + 7) % 12
                return max(low, min(mid, nearest_pitch(fifth_pc, prev)))
            return max(low, min(mid, nearest_pitch(root_pc, prev)))

        else:
            # Acid / plucked: root with occasional octave jump
            pitch = nearest_pitch(root_pc, prev)
            if random.random() < self.octave_variation:
                pitch += random.choice([-12, 12])
            if key is not None:
                pitch = snap_to_scale(pitch, key)
            return max(low, min(mid, pitch))

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        if self.pattern == "reese":
            t, events = 0.0, []
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=3.8))
                t += 4.0
            return events

        elif self.pattern == "sub_kick":
            t, events = 0.0, []
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=0.9))
                t += 1.0
            return events

        elif self.pattern == "wobble":
            t, events = 0.0, []
            while t < duration_beats:
                for off in WOBBLE_PATTERN:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.6))
                t += 4.0
            return events

        else:  # acid_line / plucked
            t, events = 0.0, []
            while t < duration_beats:
                for off in ACID_PATTERN:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.4))
                t += 4.0
            return events

    def _velocity(self, accent: bool) -> int:
        base = int(65 + self.params.density * 30)
        if accent:
            return min(127, int(base * self.filter_accent))
        return base
