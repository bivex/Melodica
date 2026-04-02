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
generators/tango.py — Tango accompaniment pattern generator.

Layer: Application / Domain
Style: Argentine tango.

The tango accompaniment pattern ("marcato") is a distinctive rhythmic
figure: bass note on beat 1, syncopated chord on the "and" of beat 2
and beat 4, creating the characteristic habanera-derived rhythm.

Patterns:
    "marcato"   — standard tango marcato: bass(1)-chord(&2)-chord(4)
    "habanera"  — habanera rhythm: long-short-long-short
    "milonga"   — milonga rhythm (faster, more rhythmic)
    "vals"      — tango vals (3/4 time): bass(1)-chord(2)-chord(3)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Quality, Scale
from melodica.utils import nearest_pitch, chord_pitches_closed, chord_at


@dataclass
class TangoGenerator(PhraseGenerator):
    """
    Tango accompaniment pattern generator.

    pattern:
        "marcato", "habanera", "milonga", "vals"
    accent:
        Velocity accent factor for downbeat bass notes.
    staccato_chords:
        If True, chords are played staccato (short duration).
    """

    name: str = "Tango Generator"
    pattern: str = "marcato"
    accent: float = 1.15
    staccato_chords: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "marcato",
        accent: float = 1.15,
        staccato_chords: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.accent = max(0.5, min(1.5, accent))
        self.staccato_chords = staccato_chords
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
        low = max(28, self.params.key_range_low)
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        prev_bass = low + 12
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            role = self._get_role(event.onset)

            if role == "bass":
                bass = nearest_pitch(chord.root, prev_bass)
                bass = max(low, min(mid - 5, bass))
                vel = int(self._velocity() * self.accent)
                notes.append(
                    NoteInfo(
                        pitch=bass,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, vel)),
                    )
                )
                prev_bass = bass
            elif role == "chord":
                voicing = chord_pitches_closed(chord, mid)
                dur = event.duration * 0.3 if self.staccato_chords else event.duration
                vel = self._velocity()
                for p in voicing:
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(event.onset, 6),
                            duration=dur,
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

    def _get_role(self, onset: float) -> str:
        beat_in_bar = onset % 4.0
        if self.pattern == "marcato":
            if beat_in_bar < 0.5:
                return "bass"
            elif 1.5 <= beat_in_bar < 2.0:
                return "chord"
            elif 3.5 <= beat_in_bar < 4.0:
                return "chord"
            elif 1.0 <= beat_in_bar < 1.5:
                return "chord"
            elif 3.0 <= beat_in_bar < 3.5:
                return "chord"
            return "rest"
        elif self.pattern == "habanera":
            if beat_in_bar < 0.75:
                return "bass"
            elif 0.75 <= beat_in_bar < 1.0:
                return "chord"
            elif 2.0 <= beat_in_bar < 2.75:
                return "bass"
            elif 2.75 <= beat_in_bar < 3.0:
                return "chord"
            return "rest"
        elif self.pattern == "milonga":
            if int(beat_in_bar) % 2 == 0:
                return "bass"
            return "chord"
        elif self.pattern == "vals":
            beat = int(beat_in_bar) % 3
            if beat == 0:
                return "bass"
            return "chord"
        return "bass"

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.4))
            t += 0.5
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 30)
