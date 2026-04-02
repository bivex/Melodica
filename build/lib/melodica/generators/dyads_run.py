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
generators/dyads_run.py — DyadsRunGenerator.

Like PianoRunGenerator but produces two-voice parallel runs
(parallel 3rds, 6ths, or custom intervals).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


TECHNIQUES = {"up", "down", "up_down", "waterfall"}


@dataclass
class DyadsRunGenerator(PhraseGenerator):
    """
    Two-voice parallel runs (3rds, 6ths, etc).

    interval:     semitone interval between voices (3=m3, 4=M3, 7=5th, 9=M6)
    technique:    "up" | "down" | "up_down" | "waterfall"
    notes_per_run: notes in each run
    scale_steps:  True = scale tones, False = chord tones
    """

    name: str = "Dyads Run Generator"
    interval: int = 3
    technique: str = "up"
    notes_per_run: int = 8
    scale_steps: bool = False
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        interval: int = 3,
        technique: str = "up",
        notes_per_run: int = 8,
        scale_steps: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.interval = interval
        if technique not in TECHNIQUES:
            raise ValueError(f"technique must be one of {sorted(TECHNIQUES)}; got {technique!r}")
        self.technique = technique
        self.notes_per_run = max(2, notes_per_run)
        self.scale_steps = scale_steps
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

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        last_chord = chords[0]

        anchor = (self.params.key_range_low + self.params.key_range_high) // 2
        if context and context.prev_pitch is not None:
            anchor = context.prev_pitch

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Build pitch pool
            if self.scale_steps:
                pool = [
                    p
                    for p in range(self.params.key_range_low, self.params.key_range_high + 1)
                    if key.contains(p % 12)
                ]
            else:
                pcs = chord.pitch_classes()
                pool = [
                    p
                    for p in range(self.params.key_range_low, self.params.key_range_high + 1)
                    if p % 12 in pcs
                ]

            if not pool:
                continue

            pool = sorted(pool)

            # Find starting point near anchor
            start_idx = min(range(len(pool)), key=lambda i: abs(pool[i] - anchor))

            # Build run sequence
            seq = self._build_sequence(pool, start_idx)

            step_dur = event.duration / self.notes_per_run
            base_vel = int(65 + self.params.density * 30)

            for i in range(self.notes_per_run):
                top_pitch = seq[i % len(seq)]
                bot_pitch = top_pitch - self.interval

                # Clamp
                top_pitch = max(
                    self.params.key_range_low, min(self.params.key_range_high, top_pitch)
                )
                bot_pitch = max(
                    self.params.key_range_low, min(self.params.key_range_high, bot_pitch)
                )

                onset = event.onset + (i * step_dur)
                accent = 1.1 if i == 0 or i == self.notes_per_run - 1 else 0.9
                vel = max(1, min(127, int(base_vel * event.velocity_factor * accent)))

                notes.append(
                    NoteInfo(
                        pitch=top_pitch,
                        start=round(onset, 6),
                        duration=round(step_dur * 0.95, 6),
                        velocity=vel,
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=bot_pitch,
                        start=round(onset, 6),
                        duration=round(step_dur * 0.95, 6),
                        velocity=max(1, min(127, int(vel * 0.85))),
                    )
                )

            anchor = top_pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    def _build_sequence(self, pool: list[int], start_idx: int) -> list[int]:
        if self.technique == "up":
            return pool[start_idx : start_idx + self.notes_per_run]
        elif self.technique == "down":
            return list(reversed(pool[max(0, start_idx - self.notes_per_run + 1) : start_idx + 1]))
        elif self.technique == "up_down":
            half = self.notes_per_run // 2
            up = pool[start_idx : start_idx + half]
            down = list(reversed(pool[start_idx : start_idx + half]))
            return up + down
        else:  # waterfall
            return list(reversed(pool[max(0, start_idx - self.notes_per_run + 1) : start_idx + 1]))

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=3.8))
            t += 4.0
        return events

    def _velocity(self) -> int:
        return int(65 + self.params.density * 30)
