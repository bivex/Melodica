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
generators/vocal_adlibs.py — Improvisational vocal ad-libs generator.

Layer: Application / Domain

Produces sparse vocal ad-libs and call-outs with varied duration and timing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


REGISTERS = {"low", "mid", "high"}
STYLES = {"adlib", "shout", "whisper"}

_REGISTER_OFFSETS: dict[str, int] = {"low": 0, "mid": 12, "high": 24}
_STYLE_VEL: dict[str, tuple[int, int]] = {
    "adlib": (60, 90),
    "shout": (95, 120),
    "whisper": (35, 55),
}


@dataclass
class VocalAdlibsGenerator(PhraseGenerator):
    name: str = "Vocal Ad-libs"
    density_adlib: float = 0.3
    register: str = "mid"
    style: str = "adlib"
    phrase_variety: float = 0.5
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        density_adlib: float = 0.3,
        register: str = "mid",
        style: str = "adlib",
        phrase_variety: float = 0.5,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if register not in REGISTERS:
            raise ValueError(f"register must be one of {REGISTERS}; got {register!r}")
        if style not in STYLES:
            raise ValueError(f"style must be one of {STYLES}; got {style!r}")
        self.density_adlib = max(0.0, min(1.0, density_adlib))
        self.register = register
        self.style = style
        self.phrase_variety = max(0.0, min(1.0, phrase_variety))
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
        last_chord: ChordLabel | None = None
        prev_pitch: int | None = context.prev_pitch if context else None

        for event in events:
            if random.random() > self.density_adlib:
                continue
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord
            pitch = self._choose_pitch(chord, prev_pitch)
            if pitch is None:
                continue

            dur = (
                random.uniform(0.25, 1.5)
                if random.random() < self.phrase_variety
                else event.duration
            )
            dur = min(dur, duration_beats - event.onset)
            vel_lo, vel_hi = _STYLE_VEL.get(self.style, (60, 90))
            vel = int(random.uniform(vel_lo, vel_hi) * event.velocity_factor)

            if self.style == "shout" and random.random() < 0.3:
                pitch = min(MIDI_MAX, pitch + OCTAVE)
            pitch = snap_to_scale(
                max(self.params.key_range_low, min(self.params.key_range_high, pitch)), key
            )

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=round(max(0.1, dur), 6),
                    velocity=max(0, min(MIDI_MAX, vel)),
                )
            )
            prev_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _choose_pitch(self, chord: ChordLabel, prev_pitch: int | None) -> int | None:
        pcs = chord.pitch_classes()
        if not pcs:
            return None
        offset = _REGISTER_OFFSETS.get(self.register, 12)
        base = self.params.key_range_low + offset
        pc = int(random.choice(pcs))
        anchor = prev_pitch if prev_pitch is not None else base
        pitch = nearest_pitch(pc, anchor)
        reg_lo = self.params.key_range_low + offset
        reg_hi = min(self.params.key_range_high, reg_lo + 2 * OCTAVE)
        while pitch < reg_lo:
            pitch += OCTAVE
        while pitch > reg_hi:
            pitch -= OCTAVE
        return pitch if self.params.key_range_low <= pitch <= self.params.key_range_high else None

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(random.uniform(0.3, 0.8), duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=round(dur, 6)))
            t += random.uniform(0.5, 1.5)
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 30)
