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
generators/bend.py — Pitch bend / slide generator.

Layer: Application / Domain
Style: Blues, rock, guitar music, synth lead.

Simulates pitch bends in MIDI by creating a rapid succession of notes
that slide from a start pitch to a target pitch.

Types:
    "bend_up"      — bend from below to target
    "bend_down"    — bend from above to target
    "pre_bend"     — start at target, release down then bend back
    "reverse_bend" — start at target, bend away
    "slide_up"     — slide through multiple notes upward
    "slide_down"   — slide through multiple notes downward
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
class BendGenerator(PhraseGenerator):
    """
    Pitch bend / slide generator.

    bend_type:
        Type of bend (see above).
    bend_range:
        Semitone range of the bend (1–4).
    bend_speed:
        Duration of each step in the bend (0.03–0.15 beats).
    sustain_after:
        Duration to hold the target pitch after the bend.
    note_strategy:
        "chord_tone", "scale_tone", "blues" — base note selection.
    """

    name: str = "Bend Generator"
    bend_type: str = "bend_up"
    bend_range: int = 2
    bend_speed: float = 0.06
    sustain_after: float = 1.0
    note_strategy: str = "chord_tone"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        bend_type: str = "bend_up",
        bend_range: int = 2,
        bend_speed: float = 0.06,
        sustain_after: float = 1.0,
        note_strategy: str = "chord_tone",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.bend_type = bend_type
        self.bend_range = max(1, min(4, bend_range))
        self.bend_speed = max(0.02, min(0.2, bend_speed))
        self.sustain_after = max(0.0, min(4.0, sustain_after))
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

            target = self._pick_target(chord, key, prev_pitch, low, high)
            bend_notes = self._render_bend(target, event.onset, event.duration, low, high)
            notes.extend(bend_notes)
            if bend_notes:
                prev_pitch = bend_notes[-1].pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_target(self, chord: ChordLabel, key: Scale, prev: int, low: int, high: int) -> int:
        if self.note_strategy == "chord_tone":
            pcs = chord.pitch_classes()
            pc = random.choice(pcs) if pcs else chord.root
        elif self.note_strategy == "blues":
            blues = [(chord.root + ivl) % 12 for ivl in [0, 3, 5, 6, 7, 10]]
            pc = random.choice(blues)
        else:
            degs = key.degrees()
            pc = int(random.choice(degs)) if degs else chord.root
        return max(low, min(high, nearest_pitch(pc, prev)))

    def _render_bend(
        self, target: int, onset: float, dur: float, low: int, high: int
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        vel = self._velocity()
        spd = self.bend_speed
        rng = self.bend_range

        if self.bend_type == "bend_up":
            # Start below, bend up to target
            start = max(low, target - rng)
            t = onset
            p = start
            while p < target and t < onset + dur:
                n_dur = min(spd, onset + dur - t)
                notes.append(
                    NoteInfo(pitch=p, start=round(t, 6), duration=n_dur * 0.9, velocity=vel)
                )
                t += spd
                p += 1
            # Sustain target
            if t < onset + dur:
                notes.append(
                    NoteInfo(
                        pitch=target, start=round(t, 6), duration=onset + dur - t, velocity=vel
                    )
                )

        elif self.bend_type == "bend_down":
            start = min(high, target + rng)
            t = onset
            p = start
            while p > target and t < onset + dur:
                n_dur = min(spd, onset + dur - t)
                notes.append(
                    NoteInfo(pitch=p, start=round(t, 6), duration=n_dur * 0.9, velocity=vel)
                )
                t += spd
                p -= 1
            if t < onset + dur:
                notes.append(
                    NoteInfo(
                        pitch=target, start=round(t, 6), duration=onset + dur - t, velocity=vel
                    )
                )

        elif self.bend_type == "pre_bend":
            # Start at target, release down, bend back up
            t = onset
            notes.append(NoteInfo(pitch=target, start=round(t, 6), duration=spd, velocity=vel))
            t += spd
            p = target
            while p > target - rng and t < onset + dur:
                n_dur = min(spd, onset + dur - t)
                p -= 1
                notes.append(
                    NoteInfo(
                        pitch=max(low, p), start=round(t, 6), duration=n_dur * 0.9, velocity=vel
                    )
                )
                t += spd
            while p < target and t < onset + dur:
                n_dur = min(spd, onset + dur - t)
                p += 1
                notes.append(
                    NoteInfo(
                        pitch=min(high, p), start=round(t, 6), duration=n_dur * 0.9, velocity=vel
                    )
                )
                t += spd
            if t < onset + dur:
                notes.append(
                    NoteInfo(
                        pitch=target, start=round(t, 6), duration=onset + dur - t, velocity=vel
                    )
                )

        elif self.bend_type == "slide_up":
            start = max(low, target - rng)
            t = onset
            for p in range(start, target + 1):
                if t >= onset + dur:
                    break
                n_dur = min(spd, onset + dur - t)
                notes.append(
                    NoteInfo(pitch=p, start=round(t, 6), duration=n_dur * 0.9, velocity=vel)
                )
                t += spd
            if t < onset + dur:
                notes.append(
                    NoteInfo(
                        pitch=target, start=round(t, 6), duration=onset + dur - t, velocity=vel
                    )
                )

        elif self.bend_type == "slide_down":
            start = min(high, target + rng)
            t = onset
            for p in range(start, target - 1, -1):
                if t >= onset + dur:
                    break
                n_dur = min(spd, onset + dur - t)
                notes.append(
                    NoteInfo(pitch=p, start=round(t, 6), duration=n_dur * 0.9, velocity=vel)
                )
                t += spd
            if t < onset + dur:
                notes.append(
                    NoteInfo(
                        pitch=target, start=round(t, 6), duration=onset + dur - t, velocity=vel
                    )
                )

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = self.sustain_after + self.bend_range * self.bend_speed
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += dur + random.uniform(0.5, 2.0)
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 35)
