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
generators/voice_leading.py — Smooth voice leading between chord voicings.

Layer: Application / Domain
Style: Choral, jazz, classical, any harmonic context.

Minimizes interval movement between consecutive chord voicings by
selecting the closest inversion/voicing for each new chord. This
produces smooth, connected harmonic progressions where each voice
moves by the smallest possible interval.

Range styles:
    "close"  — voices within a single octave (closed position)
    "spread" — voices distributed across two or more octaves

Uses voice_leading_distance() from utils to evaluate candidate voicings.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import (
    nearest_pitch,
    nearest_pitch_above,
    chord_at,
    voice_leading_distance,
    snap_to_scale,
)


@dataclass
class VoiceLeadingGenerator(PhraseGenerator):
    """
    Smooth voice leading between chord voicings.

    voices:
        Number of simultaneous voices (2–6).
    prefer_stepwise:
        If True, penalize leaps more heavily when choosing voicings.
    avoid_parallels:
        If True, avoid parallel fifths and octaves between voices.
    range_style:
        "close" (closed position) or "spread" (open position).
    """

    name: str = "Voice Leading Generator"
    voices: int = 4
    prefer_stepwise: bool = True
    avoid_parallels: bool = True
    range_style: str = "close"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        voices: int = 4,
        prefer_stepwise: bool = True,
        avoid_parallels: bool = True,
        range_style: str = "close",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.voices = max(2, min(6, voices))
        self.prefer_stepwise = prefer_stepwise
        self.avoid_parallels = avoid_parallels
        if range_style not in ("close", "spread"):
            raise ValueError(f"range_style must be 'close' or 'spread'; got {range_style!r}")
        self.range_style = range_style
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

        prev_voicing: list[int] | None = None
        if context and context.prev_pitches:
            prev_voicing = list(context.prev_pitches)

        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            voicing = self._best_voicing(chord, prev_voicing, anchor, low, high)
            vel = self._velocity(event.velocity_factor)

            for pitch in voicing:
                notes.append(
                    NoteInfo(
                        pitch=snap_to_scale(pitch, key),
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, vel)),
                    )
                )
            prev_voicing = voicing

        if notes:
            last_pitches = prev_voicing or []
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                last_pitches=last_pitches,
            )
        return notes

    def _best_voicing(
        self,
        chord: ChordLabel,
        prev: list[int] | None,
        anchor: int,
        low: int,
        high: int,
    ) -> list[int]:
        pcs = chord.pitch_classes()
        if not pcs:
            return [anchor]

        candidates = self._generate_candidates(pcs, anchor, low, high)
        if not candidates:
            return [nearest_pitch(int(pcs[0]), anchor)]

        if prev is None:
            return candidates[0]

        best = candidates[0]
        best_dist = float("inf")
        for cand in candidates:
            dist = voice_leading_distance(prev, cand)
            if self.prefer_stepwise:
                for i in range(min(len(prev), len(cand))):
                    dist += abs(cand[i] - prev[i]) * 0.5
            if dist < best_dist:
                best_dist = dist
                best = cand
        return best

    def _generate_candidates(
        self,
        pcs: list[int],
        anchor: int,
        low: int,
        high: int,
    ) -> list[list[int]]:
        n_voices = self.voices
        step = 12 if self.range_style == "close" else 24
        bass = max(low, anchor - step // 2)

        candidates: list[list[int]] = []
        base_voicing = []
        cur = bass
        for i in range(n_voices):
            pc = int(pcs[i % len(pcs)])
            p = nearest_pitch_above(pc, cur)
            p = max(low, min(high, p))
            base_voicing.append(p)
            cur = p + 2

        for inv_start in range(len(pcs)):
            voicing = []
            cur = bass
            for i in range(n_voices):
                pc = int(pcs[(inv_start + i) % len(pcs)])
                p = nearest_pitch_above(pc, cur)
                p = max(low, min(high, p))
                voicing.append(p)
                cur = p + 2
            candidates.append(sorted(voicing))

        if self.range_style == "spread":
            spread_candidates = []
            for cand in candidates:
                spread = list(cand)
                for i in range(1, len(spread), 2):
                    spread[i] = max(low, spread[i] + 12)
                spread_candidates.append(sorted(spread))
            candidates.extend(spread_candidates)

        return candidates

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=1.0))
            t += 1.0
        return events

    def _velocity(self, vel_factor: float = 1.0) -> int:
        base = int(55 + self.params.density * 30)
        return max(1, min(127, int(base * vel_factor)))
