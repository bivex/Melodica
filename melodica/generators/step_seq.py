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
generators/step_seq.py — StepSequencer.

16-step grid sequencer for EDM/synth patterns.
Each step has: gate (on/off), velocity, tie (extend to next step).
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
class StepSequencer(PhraseGenerator):
    """
    16-step grid sequencer.

    steps:       number of steps per pattern (default 16)
    gate_prob:   probability each step is ON (0.0-1.0)
    velocity_map: per-step velocity (0-127), None = auto
    ties:        list of step indices that TIE to next step
    root_note:   if True, always play chord root
    """

    name: str = "Step Sequencer"
    steps: int = 16
    gate_prob: float = 0.75
    velocity_map: list[int] | None = None
    ties: list[int] = field(default_factory=list)
    root_note: bool = True
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        steps: int = 16,
        gate_prob: float = 0.75,
        velocity_map: list[int] | None = None,
        ties: list[int] | None = None,
        root_note: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.steps = max(1, min(64, steps))
        self.gate_prob = max(0.0, min(1.0, gate_prob))
        self.velocity_map = velocity_map
        self.ties = ties if ties is not None else []
        self.root_note = root_note
        self.rhythm = rhythm
        self._last_context: RenderContext | None = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        # Step duration: spread pattern across 4 beats (1 measure), then repeat
        step_dur = 4.0 / self.steps

        events = self._build_events(duration_beats, step_dur)
        notes: list[NoteInfo] = []
        last_chord = chords[0]

        anchor = (self.params.key_range_low + self.params.key_range_high) // 2

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Gate on/off
            step_idx = int((event.onset * self.steps / 4.0)) % self.steps
            if random.random() > self.gate_prob:
                continue  # rest

            # Pitch: root or scale tone
            if self.root_note:
                pitch = nearest_pitch(chord.root, anchor)
            else:
                pcs = chord.pitch_classes()
                pitch = nearest_pitch(random.choice(pcs), anchor) if pcs else anchor

            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            # Velocity from map or auto
            if self.velocity_map and step_idx < len(self.velocity_map):
                vel = self.velocity_map[step_idx]
            else:
                is_downbeat = step_idx % (self.steps // 4) == 0
                vel = int(90 if is_downbeat else 65 + self.params.density * 20)
            vel = int(vel * event.velocity_factor)

            # Tie: extend duration
            if step_idx in self.ties:
                dur = step_dur * 2
            else:
                dur = step_dur * 0.8

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=round(dur, 6),
                    velocity=max(1, min(127, vel)),
                )
            )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    def _build_events(self, duration_beats: float, step_dur: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=round(step_dur * 0.9, 6)))
            t += step_dur
        return events

    def _velocity(self) -> int:
        return int(70 + self.params.density * 30)
