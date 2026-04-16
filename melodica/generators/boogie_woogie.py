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
generators/boogie_woogie.py — Boogie-woogie piano left-hand generator.

Layer: Application / Domain
Style: Boogie-woogie, blues piano.

The boogie-woogie bass pattern is an 8-note (or 6-note) ostinato per bar
derived from the blues scale. It alternates between bass notes and
chord-tone patterns in a driving, rhythmic left-hand pattern.

Named patterns:
    "standard"   — classic boogie: root-root-5-6-b7-6-5-3
    "walking"    — walking boogie with passing tones
    "shuffle"    — triplet shuffle boogie
    "driving"    — power boogie with octave doubling
    "rocks"      — "Boogie Rocks" pattern (root-3-4-b5-5-3)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Quality, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


NAMED_PATTERNS: dict[str, list[int]] = {
    "standard": [1, 1, 5, 6, 7, 6, 5, 3],
    "walking": [1, 2, 3, 4, 5, 4, 3, 2],
    "shuffle": [1, 5, 1, 6, 1, 5, 3, 5],
    "driving": [1, 8, 5, 8, 6, 8, 5, 8],
    "rocks": [1, 3, 4, 5, 5, 3],
}


@dataclass
class BoogieWoogieGenerator(PhraseGenerator):
    """
    Boogie-woogie piano bass generator.

    pattern:
        Named pattern or custom degree list.
    octave_bass:
        If True, double the bass notes at the octave.
    swing:
        Swing factor (0.0 = straight, 1.0 = full triplet swing).
    accent_on_one:
        Accent the first note of each bar.
    """

    name: str = "Boogie-Woogie Generator"
    pattern: str = "standard"
    octave_bass: bool = True
    swing: float = 0.67
    accent_on_one: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "standard",
        octave_bass: bool = True,
        swing: float = 0.67,
        accent_on_one: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.octave_bass = octave_bass
        self.swing = max(0.0, min(1.0, swing))
        self.accent_on_one = accent_on_one
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

        degrees = self._resolve_pattern()
        if not degrees:
            return []

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        low = max(28, self.params.key_range_low)
        high = self.params.key_range_high

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else low + 12
        last_chord: ChordLabel | None = None
        pat_idx = 0
        prev_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Reset pattern on chord change
            if chord != prev_chord:
                pat_idx = 0

            deg = degrees[pat_idx % len(degrees)]
            pitch = self._degree_to_pitch(deg, chord, prev_pitch, low, high, key)

            # Octave double on bass notes (degree 1)
            vel = self._velocity(event, pat_idx, len(degrees))
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, vel)),
                )
            )
            if self.octave_bass and deg == 1:
                notes.append(
                    NoteInfo(
                        pitch=max(low, pitch - 12),
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, int(vel * 0.8))),
                    )
                )

            prev_pitch = pitch
            prev_chord = chord
            pat_idx += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _resolve_pattern(self) -> list[int]:
        if self.pattern in NAMED_PATTERNS:
            return list(NAMED_PATTERNS[self.pattern])
        try:
            return [int(x) for x in self.pattern.split("-")]
        except ValueError:
            return [1, 1, 5, 6, 7, 6, 5, 3]

    def _degree_to_pitch(
        self, degree: int, chord: ChordLabel, prev: int, low: int, high: int, key: Scale | None = None
    ) -> int:
        root = chord.root
        # Blues scale degrees: 1=0, 2=3, 3=5, 4=6, 5=7, 6=10
        blues_map = {1: 0, 2: 3, 3: 5, 4: 6, 5: 7, 6: 10, 7: 10, 8: 12}
        offset = blues_map.get(degree, (degree - 1) * 2)
        pc = (root + offset) % 12
        pitch = nearest_pitch(pc, prev)
        if key is not None:
            pitch = snap_to_scale(pitch, key)
        return max(low, min(high, pitch))

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Swung eighth notes
        t, events = 0.0, []
        while t < duration_beats:
            long_dur = 0.33 * (1.0 + self.swing * 0.5)
            short_dur = 0.33 * (1.0 - self.swing * 0.3)
            events.append(RhythmEvent(onset=round(t, 6), duration=long_dur))
            t += 0.33
            if t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=short_dur))
                t += 0.17
        return events

    def _velocity(self, event: RhythmEvent, pat_idx: int, pat_len: int) -> int:
        base = int(65 + self.params.density * 30)
        if self.accent_on_one and pat_idx % pat_len == 0:
            base = min(127, int(base * 1.15))
        return int(base * event.velocity_factor)
