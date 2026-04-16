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
generators/organ_drawbars.py — Hammond organ style generator.

Layer: Application / Domain

Produces sustained chords with Hammond-style drawbar voicings and Leslie articulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


REGISTRATIONS = {"jazz", "gospel", "rock", "ballad"}
LESLIE_SPEEDS = {"slow", "fast"}

_DRAWBARS: dict[str, list[int]] = {
    "jazz": [0, 7, 12, 19, 24],
    "gospel": [0, 4, 7, 12, 16, 19, 24],
    "rock": [0, 7, 12, 15, 24],
    "ballad": [0, 4, 7, 12, 19],
}


@dataclass
class OrganDrawbarsGenerator(PhraseGenerator):
    name: str = "Organ Drawbars"
    registration: str = "jazz"
    leslie_speed: str = "slow"
    percussion: bool = True
    vibrato: bool = False
    sustain_bars: float = 1.0
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        registration: str = "jazz",
        leslie_speed: str = "slow",
        percussion: bool = True,
        vibrato: bool = False,
        sustain_bars: float = 1.0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if registration not in REGISTRATIONS:
            raise ValueError(f"registration must be one of {REGISTRATIONS}; got {registration!r}")
        if leslie_speed not in LESLIE_SPEEDS:
            raise ValueError(f"leslie_speed must be one of {LESLIE_SPEEDS}; got {leslie_speed!r}")
        self.registration = registration
        self.leslie_speed = leslie_speed
        self.percussion = percussion
        self.vibrato = vibrato
        self.sustain_bars = max(0.25, sustain_bars)
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

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord
            drawbar_pitches = self._get_drawbar_pitches(chord)
            if not drawbar_pitches:
                continue

            base_vel = int(self._velocity() * event.velocity_factor)
            leslie_dur = event.duration * (0.95 if self.leslie_speed == "fast" else 0.98)

            for i, pitch in enumerate(drawbar_pitches):
                pitch = snap_to_scale(max(self.params.key_range_low, min(self.params.key_range_high, pitch)), key)
                drawbar_factor = 0.6 + 0.4 * math.sin(
                    math.pi * (i + 1) / (len(drawbar_pitches) + 1)
                )
                vel = int(base_vel * drawbar_factor)

                if self.percussion and i == 0:
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(event.onset, 6),
                            duration=round(min(0.08, event.duration * 0.1), 6),
                            velocity=max(1, min(MIDI_MAX, int(vel * 0.4))),
                            articulation="staccato",
                        )
                    )

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(event.onset, 6),
                        duration=round(leslie_dur, 6),
                        velocity=max(0, min(MIDI_MAX, vel)),
                        articulation="sustain",
                    )
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _get_drawbar_pitches(self, chord: ChordLabel) -> list[int]:
        root_pc = chord.bass if chord.bass is not None else chord.root
        intervals = _DRAWBARS.get(self.registration, _DRAWBARS["jazz"])
        pcs = chord.pitch_classes()
        anchor = (self.params.key_range_low + self.params.key_range_high) // 2
        pitches = []
        for ivl in intervals:
            pc = (int(root_pc) + ivl) % OCTAVE
            best_pc = min(pcs, key=lambda c: min((int(c) - pc) % 12, (pc - int(c)) % 12))
            dist = min((int(best_pc) - pc) % 12, (pc - int(best_pc)) % 12)
            use_pc = int(best_pc) if dist <= 1 else pc
            p = nearest_pitch(use_pc, anchor)
            if self.params.key_range_low <= p <= self.params.key_range_high:
                pitches.append(p)
        return sorted(set(pitches))

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        bar_dur = self.sustain_bars * 4.0
        t, events = 0.0, []
        while t < duration_beats:
            events.append(
                RhythmEvent(onset=round(t, 6), duration=round(min(bar_dur, duration_beats - t), 6))
            )
            t += bar_dur
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 40)
