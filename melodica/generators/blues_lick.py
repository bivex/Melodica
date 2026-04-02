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
generators/blues_lick.py — Blues lick / phrase generator.

Layer: Application / Domain
Style: Blues, rock, jazz-fusion, gospel.

Generates blues-based phrases using the blues scale (minor pentatonic + b5)
with characteristic phrasing: bends, blue notes (b3, b5, b7),
call-and-response micro-phrases, and chromatic enclosures.

Lick patterns:
    "standard"   — classic blues turnaround licks
    "bending"    — emphasizes b3→3 and b7→1 bends
    "minor_pent" — pure minor pentatonic runs
    "mixolydian" — dominant 7th arpeggios with blues notes
    "chromatic"  — heavy chromatic enclosures
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# Blues scale: 1, b3, 4, b5, 5, b7
BLUES_SCALE_DEGREES = [0, 3, 5, 6, 7, 10]
# Extended: add major 3rd (for blues bend), major 6th, natural 7
EXTENDED_BLUES = [0, 3, 4, 5, 6, 7, 9, 10, 11]


@dataclass
class BluesLickGenerator(PhraseGenerator):
    """
    Blues lick generator with authentic phrasing.

    lick_style:
        "standard", "bending", "minor_pent", "mixolydian", "chromatic"
    phrase_length:
        Notes per micro-phrase (3–8).
    rest_probability:
        Chance of a rest between phrases (0–1).
    enclosure_probability:
        Chance of chromatic enclosure around target note.
    bend_probability:
        Chance of simulating a bend (two-note slur b→nat).
    """

    name: str = "Blues Lick Generator"
    lick_style: str = "standard"
    phrase_length: int = 4
    rest_probability: float = 0.3
    enclosure_probability: float = 0.2
    bend_probability: float = 0.15
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        lick_style: str = "standard",
        phrase_length: int = 4,
        rest_probability: float = 0.3,
        enclosure_probability: float = 0.2,
        bend_probability: float = 0.15,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if lick_style not in ("standard", "bending", "minor_pent", "mixolydian", "chromatic"):
            raise ValueError(
                f"lick_style must be one of 'standard', 'bending', 'minor_pent', "
                f"'mixolydian', 'chromatic'; got {lick_style!r}"
            )
        self.lick_style = lick_style
        self.phrase_length = max(3, min(8, phrase_length))
        self.rest_probability = max(0.0, min(1.0, rest_probability))
        self.enclosure_probability = max(0.0, min(1.0, enclosure_probability))
        self.bend_probability = max(0.0, min(1.0, bend_probability))
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
        phrase_note_count = 0

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Rest between phrases
            if phrase_note_count >= self.phrase_length:
                if random.random() < self.rest_probability:
                    phrase_note_count = 0
                    continue
                phrase_note_count = 0

            pitch = self._pick_pitch(chord, prev_pitch, key, low, high)
            pitch = max(low, min(high, pitch))

            # Simulate bend: add a short grace note a half/whole step below
            if (
                self.lick_style == "bending"
                and random.random() < self.bend_probability
                and phrase_note_count > 0
            ):
                bend_from = pitch - random.choice([1, 2])
                bend_from = max(low, bend_from)
                notes.append(
                    NoteInfo(
                        pitch=bend_from,
                        start=round(event.onset, 6),
                        duration=event.duration * 0.3,
                        velocity=max(1, min(127, int(self._velocity() * 0.7))),
                        articulation="grace",
                    )
                )

            vel = self._velocity_with_expression(event.onset, duration_beats)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, int(vel * event.velocity_factor))),
                )
            )

            # Chromatic enclosure: add an upper neighbor note before next note
            if random.random() < self.enclosure_probability and self.lick_style in (
                "chromatic",
                "standard",
            ):
                enc_pitch = pitch + 1
                if enc_pitch <= high:
                    enc_start = event.onset + event.duration * 0.7
                    enc_dur = event.duration * 0.25
                    if enc_start + enc_dur < duration_beats:
                        notes.append(
                            NoteInfo(
                                pitch=enc_pitch,
                                start=round(enc_start, 6),
                                duration=enc_dur,
                                velocity=max(1, min(127, int(vel * 0.6))),
                                articulation="grace",
                            )
                        )

            prev_pitch = pitch
            phrase_note_count += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------
    # Pitch selection
    # ------------------------------------------------------------------

    def _pick_pitch(
        self, chord: ChordLabel, prev_pitch: int, key: Scale, low: int, high: int
    ) -> int:
        root_pc = chord.root

        if self.lick_style == "minor_pent":
            pool = [(root_pc + ivl) % 12 for ivl in BLUES_SCALE_DEGREES]
        elif self.lick_style == "mixolydian":
            # Mixolydian: 1, 2, 3, 4, 5, 6, b7
            pool = [(root_pc + ivl) % 12 for ivl in [0, 2, 4, 5, 7, 9, 10]]
            # Add blues notes
            pool.extend([(root_pc + ivl) % 12 for ivl in [3, 6]])
        elif self.lick_style == "chromatic":
            # All 12 pitch classes available
            pool = list(range(12))
        else:
            # Standard blues: extended blues scale
            pool = [(root_pc + ivl) % 12 for ivl in EXTENDED_BLUES]

        pool = sorted(set(pool))

        # Prefer stepwise motion
        if random.random() < 0.6:
            # Find closest scale tone
            candidates = [nearest_pitch(pc, prev_pitch) for pc in pool]
            candidates = [p for p in candidates if 1 <= abs(p - prev_pitch) <= 2]
            if candidates:
                return random.choice(candidates)

        # Leap to a chord tone or blues note
        pc = random.choice(pool)
        pitch = nearest_pitch(pc, prev_pitch)

        # Clamp
        while pitch < low:
            pitch += 12
        while pitch > high:
            pitch -= 12

        return pitch

    # ------------------------------------------------------------------
    # Rhythm & velocity
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Swing eighth notes
        t, events = 0.0, []
        while t < duration_beats:
            # Long eighth (swing)
            events.append(RhythmEvent(onset=round(t, 6), duration=0.30))
            t += 0.33
            if t >= duration_beats:
                break
            # Short eighth
            events.append(RhythmEvent(onset=round(t, 6), duration=0.15))
            t += 0.17
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 35)

    def _velocity_with_expression(self, onset: float, total: float) -> int:
        """Phrase arch: louder in middle, softer at edges."""
        base = self._velocity()
        if total <= 0:
            return base
        progress = onset / total
        arch = 0.85 + 0.15 * (1.0 - abs(2.0 * progress - 1.0))
        return int(base * arch)
