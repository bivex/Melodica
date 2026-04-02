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
generators/broken_chord.py — Extended broken chord patterns generator.

Layer: Application / Domain
Style: Classical, Romantic, Impressionist (Chopin, Debussy, Liszt).

Broken chords go far beyond Alberti bass. They can span wide ranges,
use various rhythmic subdivisions, and create flowing arpeggiated textures.

Named patterns:
    "chopin"     — Chopin-style wide broken chord (R-5-3-8-5-3)
    "debussy"    — Debussy-style flowing arpeggio (ascending cascade)
    "liszt"      — Liszt-style virtuoso sweep (full chord sweep up+down)
    "romantic"   — Romantic era broken chord (R-3-5-8-5-3)
    "rolling"    — Rolling broken chord (continuous up-down)
    "waltz_left" — Waltz left hand (bass-chord-chord)
    "cascade"    — Cascading notes across wide range
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


NAMED_PATTERNS: dict[str, list[tuple[int, int]]] = {
    # (chord_tone_position_1based, octave_offset)
    "chopin": [(1, 0), (5, 0), (3, 0), (8, 1), (5, 1), (3, 1)],
    "debussy": [(1, 0), (3, 0), (5, 0), (8, 1), (3, 1), (5, 1), (8, 2)],
    "liszt": [(1, -1), (3, 0), (5, 0), (8, 1), (5, 1), (3, 1), (1, 1)],
    "romantic": [(1, 0), (3, 0), (5, 0), (8, 1), (5, 0), (3, 0)],
    "rolling": [(1, 0), (3, 0), (5, 0), (8, 1), (8, 1), (5, 0), (3, 0), (1, 0)],
    "waltz_left": [(1, 0), (5, 0), (5, 0)],
    "cascade": [(1, 0), (5, 0), (3, 1), (1, 1), (5, 1), (3, 2)],
}


@dataclass
class BrokenChordGenerator(PhraseGenerator):
    """
    Extended broken chord pattern generator.

    pattern:
        Named pattern or "custom" with custom_positions.
    subdivision:
        Duration of each note in beats (0.25 = 16th, 0.5 = 8th).
    voice_lead:
        Smooth voice leading on chord changes.
    spread:
        How many octaves the pattern spans (1–3).
    velocity_envelope:
        "arch" — louder in the middle, softer at edges.
        "crescendo" — gradual increase.
        "flat" — uniform.
    """

    name: str = "Broken Chord Generator"
    pattern: str = "chopin"
    subdivision: float = 0.25
    voice_lead: bool = True
    spread: int = 2
    velocity_envelope: str = "arch"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "chopin",
        subdivision: float = 0.25,
        voice_lead: bool = True,
        spread: int = 2,
        velocity_envelope: str = "arch",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.subdivision = max(0.0625, min(1.0, subdivision))
        self.voice_lead = voice_lead
        self.spread = max(1, min(3, spread))
        self.velocity_envelope = velocity_envelope
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

        pattern_data = NAMED_PATTERNS.get(self.pattern, NAMED_PATTERNS["chopin"])
        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None
        prev_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Build pitch sequence from pattern
            pitch_seq = self._pattern_to_pitches(pattern_data, chord, prev_pitch, low, high)

            # Voice lead on chord change
            if self.voice_lead and prev_chord is not None and chord != prev_chord and pitch_seq:
                shift = prev_pitch - pitch_seq[0]
                pitch_seq = [max(low, min(high, p + shift)) for p in pitch_seq]

            # Render notes
            t = event.onset
            end = event.onset + event.duration
            idx = 0
            while t < end:
                pitch = pitch_seq[idx % len(pitch_seq)]
                n_dur = min(self.subdivision, end - t)
                vel = self._velocity_envelope(idx, len(pitch_seq), t, end)
                notes.append(
                    NoteInfo(
                        pitch=max(low, min(high, pitch)),
                        start=round(t, 6),
                        duration=n_dur * 0.9,
                        velocity=max(1, min(127, vel)),
                    )
                )
                t += self.subdivision
                idx += 1

            if pitch_seq:
                prev_pitch = pitch_seq[-1]
            prev_chord = chord

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pattern_to_pitches(
        self,
        pattern: list[tuple[int, int]],
        chord: ChordLabel,
        anchor: int,
        low: int,
        high: int,
    ) -> list[int]:
        pcs = chord.pitch_classes()
        if not pcs:
            return [anchor]

        pitches = []
        for pos, oct_off in pattern:
            idx = (pos - 1) % len(pcs)
            pc = pcs[idx]
            base = nearest_pitch(pc, anchor)
            pitch = base + oct_off * 12
            # Clamp to spread
            if pitch > anchor + self.spread * 12:
                pitch -= 12 * ((pitch - anchor) // 12)
            if pitch < anchor - self.spread * 12:
                pitch += 12 * ((anchor - pitch) // 12)
            pitches.append(max(low, min(high, pitch)))
        return pitches

    def _velocity_envelope(self, idx: int, total: int, onset: float, end: float) -> int:
        base = int(55 + self.params.density * 30)
        if self.velocity_envelope == "arch":
            progress = idx / max(total - 1, 1)
            factor = 0.75 + 0.25 * (1.0 - abs(2.0 * progress - 1.0))
        elif self.velocity_envelope == "crescendo":
            if end > onset:
                progress = (onset) / (end)
                factor = 0.7 + 0.3 * progress
            else:
                factor = 1.0
        else:
            factor = 1.0
        return int(base * factor)

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=min(4.0, duration_beats - t)))
            t += 4.0
        return events
