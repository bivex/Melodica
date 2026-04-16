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
generators/supersaw_pad.py — Supersaw / trance pad generator.

Layer: Application / Domain
Style: Trance, progressive, ambient, EDM.

Supersaw pads use multiple detuned sawtooth oscillators to create
a thick, wide stereo texture. This generator produces sustained
chord voicings with slow attack/release characteristics.

Variants:
    "trance"    — trance supersaw (7 detuned voices, sidechain feel)
    "ambient"   — slow ambient pad (long notes, gentle motion)
    "stabs"     — rhythmic supersaw stabs
    "plucks"    — short supersaw plucks
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, chord_pitches_closed, snap_to_scale


@dataclass
class SupersawPadGenerator(PhraseGenerator):
    """
    Supersaw / trance pad generator.

    variant:
        "trance", "ambient", "stabs", "plucks"
    voice_count:
        Number of detuned voices (3–7). More = thicker.
    detune_amount:
        How much pitch variation between voices (0.0–0.3 semitones).
        Simulated by slight velocity variation + chord spread.
    release_time:
        How long notes ring after their duration (in beats).
    sidechain_feel:
        If True, create a pumping rhythm (velocity duck on beats).
    """

    name: str = "Supersaw Pad Generator"
    variant: str = "trance"
    voice_count: int = 5
    detune_amount: float = 0.15
    release_time: float = 1.0
    sidechain_feel: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "trance",
        voice_count: int = 5,
        detune_amount: float = 0.15,
        release_time: float = 1.0,
        sidechain_feel: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.voice_count = max(3, min(7, voice_count))
        self.detune_amount = max(0.0, min(0.3, detune_amount))
        self.release_time = max(0.0, min(4.0, release_time))
        self.sidechain_feel = sidechain_feel
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

        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord: ChordLabel | None = None

        if self.variant == "trance":
            notes = self._trance(chords, duration_beats, mid, key)
        elif self.variant == "ambient":
            notes = self._ambient(chords, duration_beats, mid, key)
        elif self.variant == "stabs":
            notes = self._stabs(chords, duration_beats, mid, key)
        elif self.variant == "plucks":
            notes = self._plucks(chords, duration_beats, mid, key)

        if chords:
            last_chord = chords[-1]

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _trance(self, chords: list[ChordLabel], dur: float, anchor: int, key: Scale) -> list[NoteInfo]:
        notes = []
        vel = int(55 + self.params.density * 25)

        for chord in chords:
            voicing = chord_pitches_closed(chord, anchor)
            voicing = voicing[: self.voice_count]

            for i, p in enumerate(voicing):
                p = snap_to_scale(max(self.params.key_range_low, min(self.params.key_range_high, p)), key)
                # Velocity variation simulates detune
                v = vel + random.randint(-5, 5)

                if self.sidechain_feel:
                    # Pumping: accent on beat, duck on & of beat
                    for beat in range(int(chord.duration)):
                        onset = chord.start + beat
                        if onset >= dur:
                            break
                        notes.append(
                            NoteInfo(
                                pitch=p,
                                start=round(onset, 6),
                                duration=0.9,
                                velocity=min(127, v + 5),
                            )
                        )
                else:
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=chord.start,
                            duration=chord.duration + self.release_time,
                            velocity=max(1, min(127, v)),
                        )
                    )

        return notes

    def _ambient(self, chords: list[ChordLabel], dur: float, anchor: int, key: Scale) -> list[NoteInfo]:
        notes = []
        vel = int(40 + self.params.density * 20)

        for chord in chords:
            voicing = chord_pitches_closed(chord, anchor)
            # Spread voicing wider
            spread = []
            for i, p in enumerate(voicing):
                if i % 2 == 1:
                    p += 12
                spread.append(p)
            spread = spread[: self.voice_count]

            for p in spread:
                p = snap_to_scale(max(self.params.key_range_low, min(self.params.key_range_high, p)), key)
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=chord.start,
                        duration=chord.duration + self.release_time * 2,
                        velocity=max(1, min(127, vel + random.randint(-3, 3))),
                    )
                )

        return notes

    def _stabs(self, chords: list[ChordLabel], dur: float, anchor: int, key: Scale) -> list[NoteInfo]:
        notes = []
        vel = int(65 + self.params.density * 30)

        t = 0.0
        while t < dur:
            chord = chord_at(chords, t)
            if chord is None:
                t += 1.0
                continue
            voicing = chord_pitches_closed(chord, anchor)
            voicing = voicing[: self.voice_count]

            for p in voicing:
                p = snap_to_scale(max(self.params.key_range_low, min(self.params.key_range_high, p)), key)
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(t, 6),
                        duration=0.3,
                        velocity=vel,
                    )
                )
            t += 1.0

        return notes

    def _plucks(self, chords: list[ChordLabel], dur: float, anchor: int, key: Scale) -> list[NoteInfo]:
        notes = []
        vel = int(55 + self.params.density * 30)

        t = 0.0
        while t < dur:
            chord = chord_at(chords, t)
            if chord is None:
                t += 0.5
                continue
            voicing = chord_pitches_closed(chord, anchor)
            # Single pluck from voicing
            p = random.choice(voicing) if voicing else anchor
            p = snap_to_scale(max(self.params.key_range_low, min(self.params.key_range_high, p)), key)
            notes.append(
                NoteInfo(
                    pitch=p,
                    start=round(t, 6),
                    duration=0.2,
                    velocity=vel,
                )
            )
            t += 0.5

        return notes
