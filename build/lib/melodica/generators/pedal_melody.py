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
generators/pedal_melody.py — Pedal bass + melody fusion generator.

Layer: Application / Domain
Style: Cinematic, progressive rock, classical, ambient.

Combines a sustained pedal bass (drone) with a melodic voice on top.
This is a fundamental texture in:
  - Film scoring (pedal + evolving melody)
  - Prog rock (sustained bass note + guitar solo)
  - Classical organ (pedal point + manual melody)
  - Ambient music (drone + melodic fragments)

The two voices are generated simultaneously by this single generator.
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
class PedalMelodyGenerator(PhraseGenerator):
    """
    Pedal bass + melody fusion generator.

    Produces two simultaneous voices:
      1. A sustained pedal note (or octave) in the bass
      2. A melody above it

    pedal_pc:
        Pitch class for the pedal. None = use key's tonic.
    pedal_octaves:
        Number of octaves for the pedal (1 or 2).
    melody_style:
        "stepwise" — mostly stepwise motion
        "arpeggio" — chord-tone arpeggios
        "mixed" — combination
    melody_rhythm:
        Subdivision for the melody voice in beats.
    pedal_retrigger:
        Retrigger pedal on chord changes.
    """

    name: str = "Pedal Melody Generator"
    pedal_pc: int | None = None
    pedal_octaves: int = 1
    melody_style: str = "stepwise"
    melody_rhythm: float = 0.5
    pedal_retrigger: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pedal_pc: int | None = None,
        pedal_octaves: int = 1,
        melody_style: str = "stepwise",
        melody_rhythm: float = 0.5,
        pedal_retrigger: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pedal_pc = pedal_pc
        self.pedal_octaves = max(1, min(2, pedal_octaves))
        self.melody_style = melody_style
        self.melody_rhythm = max(0.125, min(2.0, melody_rhythm))
        self.pedal_retrigger = pedal_retrigger
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

        low = self.params.key_range_low
        high = self.params.key_range_high
        mid = (low + high) // 2
        pedal_anchor = low + 12
        melody_anchor = mid + 5

        pedal_pc = self.pedal_pc if self.pedal_pc is not None else key.root
        pedal_pitch = nearest_pitch(pedal_pc, pedal_anchor)
        pedal_pitch = max(low, min(mid - 5, pedal_pitch))

        notes: list[NoteInfo] = []
        last_chord = chords[-1]
        prev_melody = melody_anchor

        # Pedal voice
        if self.pedal_retrigger:
            for chord in chords:
                p = nearest_pitch(chord.root, pedal_pitch)
                p = max(low, min(mid - 5, p))
                vel = int(40 + self.params.density * 15)
                notes.append(
                    NoteInfo(pitch=p, start=chord.start, duration=chord.duration, velocity=vel)
                )
                if self.pedal_octaves > 1:
                    notes.append(
                        NoteInfo(
                            pitch=max(low, p - 12),
                            start=chord.start,
                            duration=chord.duration,
                            velocity=int(vel * 0.7),
                        )
                    )
        else:
            vel = int(40 + self.params.density * 15)
            notes.append(
                NoteInfo(pitch=pedal_pitch, start=0.0, duration=duration_beats, velocity=vel)
            )
            if self.pedal_octaves > 1:
                notes.append(
                    NoteInfo(
                        pitch=max(low, pedal_pitch - 12),
                        start=0.0,
                        duration=duration_beats,
                        velocity=int(vel * 0.7),
                    )
                )

        # Melody voice
        melody_events = self._build_melody_events(duration_beats)
        for event in melody_events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue

            if self.melody_style == "stepwise":
                step = random.choice([-2, -1, -1, 1, 1, 2])
                pitch = prev_melody + step
                if not key.contains(pitch % 12):
                    pitch = nearest_pitch(chord.root, pitch)
            elif self.melody_style == "arpeggio":
                pcs = chord.pitch_classes()
                pc = random.choice(pcs) if pcs else chord.root
                pitch = nearest_pitch(int(pc), prev_melody)
            else:
                if random.random() < 0.6:
                    step = random.choice([-2, -1, 1, 2])
                    pitch = prev_melody + step
                    if not key.contains(pitch % 12):
                        pitch = nearest_pitch(chord.root, pitch)
                else:
                    pcs = chord.pitch_classes()
                    pc = random.choice(pcs) if pcs else chord.root
                    pitch = nearest_pitch(int(pc), prev_melody)

            pitch = max(mid, min(high, pitch))
            vel = int(60 + self.params.density * 30)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, vel)),
                )
            )
            prev_melody = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_melody_events(self, duration_beats: float) -> list[RhythmEvent]:
        t, events = 0.0, []
        dur = self.melody_rhythm
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=dur * 0.9))
            t += dur
        return events
