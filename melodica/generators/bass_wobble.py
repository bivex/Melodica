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
generators/bass_wobble.py — Dubstep/breakbeat wobble bass with LFO modulation.

Layer: Application / Domain
Style: Dubstep, breakbeat, grime, drum & bass, electro.

Produces rhythmically modulated basslines where velocity and duration
vary per-note to simulate LFO (Low Frequency Oscillator) modulation
of a filter or amplitude. The wobble rate determines the subdivision.

Wobble rates (beat subdivisions):
    "1/4"    = 1.0  beats
    "1/8"    = 0.5  beats
    "1/16"   = 0.25 beats
    "triplet" = 0.33 beats (approximate)

LFO shapes control the velocity curve across a wobble cycle:
    "sine"     — smooth rise and fall
    "square"   — hard on/off alternation
    "triangle" — linear ramp up and down
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


WOBBLE_RATES: dict[str, float] = {
    "1/4": 1.0,
    "1/8": 0.5,
    "1/16": 0.25,
    "triplet": 0.33,
}


@dataclass
class BassWobbleGenerator(PhraseGenerator):
    """
    Dubstep/breakbeat wobble bass with LFO modulation.

    wobble_rate:
        "1/4", "1/8", "1/16", "triplet"
    waveform:
        Oscillator waveform for the bass tone: "saw", "square", "sine".
        Affects pitch selection and harmonic density.
    lfo_shape:
        LFO modulation shape: "sine", "square", "triangle".
    pitch_slide:
        If True, add approach notes to simulate portamento/glide.
    """

    name: str = "Bass Wobble Generator"
    wobble_rate: str = "1/8"
    waveform: str = "saw"
    lfo_shape: str = "sine"
    pitch_slide: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        wobble_rate: str = "1/8",
        waveform: str = "saw",
        lfo_shape: str = "sine",
        pitch_slide: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.wobble_rate = wobble_rate
        self.waveform = waveform
        self.lfo_shape = lfo_shape
        self.pitch_slide = pitch_slide
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
        anchor = max(24, self.params.key_range_low)
        last_chord = chords[-1]
        step = WOBBLE_RATES.get(self.wobble_rate, 0.5)
        wobble_idx = 0
        prev_pitch: int | None = None

        t = 0.0
        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is None:
                t += step
                wobble_idx += 1
                continue

            root_pc = chord.bass if chord.bass is not None else chord.root
            pitch = nearest_pitch(int(root_pc), anchor)

            # Waveform octave doubling
            if self.waveform == "saw":
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            elif self.waveform == "square":
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            else:  # sine — pure tone, stay low
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
                pitch = min(pitch, anchor + 12)

            # Pitch slide: approach from semitone below
            if self.pitch_slide and prev_pitch is not None and prev_pitch != pitch:
                slide_pc = (int(root_pc) - 1) % 12
                slide_pitch = snap_to_scale(nearest_pitch(slide_pc, prev_pitch), key)
                slide_pitch = max(
                    self.params.key_range_low, min(self.params.key_range_high, slide_pitch)
                )
                notes.append(
                    NoteInfo(
                        pitch=slide_pitch,
                        start=round(t - step * 0.3, 6),
                        duration=step * 0.3,
                        velocity=max(1, int(self._velocity() * 0.6)),
                    )
                )

            vel = self._lfo_velocity(wobble_idx)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=step * 0.9,
                    velocity=max(1, min(127, vel)),
                )
            )

            prev_pitch = pitch
            anchor = pitch
            t += step
            wobble_idx += 1

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _lfo_velocity(self, step_idx: int) -> int:
        """Compute velocity using LFO shape at the given step index."""
        base = int(60 + self.params.density * 35)
        cycle_len = 8  # steps per LFO cycle
        phase = (step_idx % cycle_len) / cycle_len

        if self.lfo_shape == "sine":
            mod = math.sin(phase * 2 * math.pi)
        elif self.lfo_shape == "square":
            mod = 1.0 if phase < 0.5 else -1.0
        elif self.lfo_shape == "triangle":
            mod = 4.0 * abs(phase - 0.5) - 1.0 if phase != 0.5 else 1.0
        else:
            mod = 0.0

        # Map [-1, 1] to [0.4, 1.0] velocity multiplier
        factor = 0.7 + 0.3 * (mod + 1.0) / 2.0
        return int(base * factor)

    def _velocity(self) -> int:
        return int(70 + self.params.density * 30)
