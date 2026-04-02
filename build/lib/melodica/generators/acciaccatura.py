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
generators/acciaccatura.py — Grace note / acciaccatura generator.

Layer: Application / Domain
Style: All genres — classical, folk, jazz, world music.

Grace notes (acciaccatura / appoggiatura) are very short ornamental notes
played immediately before the main note. In MIDI, they are rendered as
a very brief note preceding the sustained main note.

Types:
    "upper"     — grace note from above (one step up)
    "lower"     — grace note from below (one step down)
    "double"    — double grace: upper + lower approaching main note
    "slide_up"  — two-note slide upward into main note
    "slide_down" — two-note slide downward into main note
    "chord"     — grace chord (multiple grace notes)
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
class AcciaccaturaGenerator(PhraseGenerator):
    """
    Grace note / acciaccatura generator.

    grace_type:
        "upper", "lower", "double", "slide_up", "slide_down", "chord"
    grace_duration:
        Duration of the grace note(s) in beats (typically very short: 0.05–0.15).
    main_duration:
        Duration of the main note in beats.
    interval:
        Semitone interval for the grace note (1 = half step, 2 = whole step).
        0 = auto from scale context.
    density:
        Probability of adding a grace note (0–1).
    note_strategy:
        "chord_tone", "scale_tone", "prev_note" — how main note is chosen.
    """

    name: str = "Acciaccatura Generator"
    grace_type: str = "lower"
    grace_duration: float = 0.08
    main_duration: float = 0.75
    interval: int = 0
    density: float = 0.7
    note_strategy: str = "chord_tone"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        grace_type: str = "lower",
        grace_duration: float = 0.08,
        main_duration: float = 0.75,
        interval: int = 0,
        density: float = 0.7,
        note_strategy: str = "chord_tone",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if grace_type not in ("upper", "lower", "double", "slide_up", "slide_down", "chord"):
            raise ValueError(f"Unknown grace_type: {grace_type!r}")
        self.grace_type = grace_type
        self.grace_duration = max(0.03, min(0.25, grace_duration))
        self.main_duration = max(0.25, min(4.0, main_duration))
        self.interval = interval
        self.density = max(0.0, min(1.0, density))
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

            main_pitch = self._pick_main(chord, prev_pitch, key, low, high)
            interval = self._resolve_interval(main_pitch, key)

            if random.random() < self.density:
                grace_notes = self._render_grace(main_pitch, interval, event.onset, low, high)
            else:
                grace_notes = []

            main_dur = min(self.main_duration, duration_beats - event.onset)
            if main_dur <= 0:
                continue

            vel = self._velocity()
            notes.extend(grace_notes)
            notes.append(
                NoteInfo(
                    pitch=main_pitch,
                    start=round(event.onset + len(grace_notes) * self.grace_duration, 6),
                    duration=main_dur - len(grace_notes) * self.grace_duration,
                    velocity=max(1, min(127, vel)),
                )
            )
            prev_pitch = main_pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_main(self, chord: ChordLabel, prev: int, key: Scale, low: int, high: int) -> int:
        if self.note_strategy == "chord_tone":
            pcs = chord.pitch_classes()
            pc = random.choice(pcs) if pcs else chord.root
        elif self.note_strategy == "scale_tone":
            degs = key.degrees()
            pc = int(random.choice(degs)) if degs else chord.root
        else:
            return prev
        return max(low, min(high, nearest_pitch(pc, prev)))

    def _resolve_interval(self, base: int, key: Scale) -> int:
        if self.interval > 0:
            return self.interval
        degs = key.degrees()
        base_pc = base % 12
        for d in degs:
            diff = (int(d) - base_pc) % 12
            if diff in (1, 2):
                return diff
        return 1

    def _render_grace(
        self, main: int, interval: int, onset: float, low: int, high: int
    ) -> list[NoteInfo]:
        g_dur = self.grace_duration
        vel = max(1, int(self._velocity() * 0.6))
        upper = max(low, min(high, main + interval))
        lower = max(low, min(high, main - interval))

        if self.grace_type == "upper":
            return [NoteInfo(pitch=upper, start=round(onset, 6), duration=g_dur, velocity=vel)]
        elif self.grace_type == "lower":
            return [NoteInfo(pitch=lower, start=round(onset, 6), duration=g_dur, velocity=vel)]
        elif self.grace_type == "double":
            return [
                NoteInfo(pitch=upper, start=round(onset, 6), duration=g_dur, velocity=vel),
                NoteInfo(pitch=lower, start=round(onset + g_dur, 6), duration=g_dur, velocity=vel),
            ]
        elif self.grace_type == "slide_up":
            return [
                NoteInfo(
                    pitch=max(low, main - 2), start=round(onset, 6), duration=g_dur, velocity=vel
                ),
                NoteInfo(
                    pitch=max(low, main - 1),
                    start=round(onset + g_dur, 6),
                    duration=g_dur,
                    velocity=vel,
                ),
            ]
        elif self.grace_type == "slide_down":
            return [
                NoteInfo(
                    pitch=min(high, main + 2), start=round(onset, 6), duration=g_dur, velocity=vel
                ),
                NoteInfo(
                    pitch=min(high, main + 1),
                    start=round(onset + g_dur, 6),
                    duration=g_dur,
                    velocity=vel,
                ),
            ]
        elif self.grace_type == "chord":
            return [
                NoteInfo(pitch=lower, start=round(onset, 6), duration=g_dur, velocity=vel),
                NoteInfo(pitch=main, start=round(onset, 6), duration=g_dur, velocity=vel),
            ]
        return []

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        dur = self.main_duration
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += dur
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 35)
