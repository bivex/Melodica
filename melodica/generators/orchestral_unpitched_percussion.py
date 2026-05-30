# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/orchestral_unpitched_percussion.py -- Orchestral unpitched percussion.

Layer: Application / Domain
Style: Classical, cinematic, orchestral percussion.

Six generators for standard orchestral unpitched percussion:
BassDrum, TamTam, Gong, Triangle, Castanets, Whip/Slapstick.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale

# GM Percussion Map (Channel 10)
BASS_DRUM_GRAN_CASSA = 36
BASS_DRUM_ACOUSTIC = 35
TAM_TAM = 55
GONG = 55
TRIANGLE = 80
CASTANETS = 85
SLAPSTICK = 91


class BassDrumGenerator(PhraseGenerator):
    """Concert bass drum / gran cassa.

    pattern_type:
        "single" -- isolated hits at section boundaries.
        "roll"   -- crescendo roll with increasing velocity.
        "march"  -- steady quarter-note pulse.
    """

    name: str = "Bass Drum Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern_type: str = "single",
    ) -> None:
        super().__init__(params)
        self.pattern_type = pattern_type
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

        notes: list[NoteInfo] = []
        for i, chord in enumerate(chords):
            is_first = (i == 0)
            if self.pattern_type == "single":
                notes.extend(self._render_single(chord.start, chord.duration, is_first))
            elif self.pattern_type == "roll":
                notes.extend(self._render_roll(chord.start, chord.duration))
            else:
                notes.extend(self._render_march(chord.start, chord.duration))

        if notes:
            notes.sort(key=lambda n: n.start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )
        return notes

    def _render_single(self, start: float, duration: float, is_first: bool) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        prob = 1.0 if is_first else self.params.density * 0.3
        if random.random() < prob:
            vel = int(90 + random.randint(0, 25))
            notes.append(NoteInfo(
                pitch=BASS_DRUM_GRAN_CASSA,
                start=round(start, 6),
                duration=max(2.0, duration * 0.8),
                velocity=max(1, min(127, vel)),
            ))
        return notes

    def _render_roll(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        step = 0.5
        steps = max(4, int(duration / step))
        for s in range(steps):
            t = start + s * step
            if t >= start + duration:
                break
            progress = s / steps
            vel = int(30 + 70 * progress ** 1.5)
            notes.append(NoteInfo(
                pitch=BASS_DRUM_ACOUSTIC,
                start=round(t, 6),
                duration=step * 0.8,
                velocity=max(1, min(127, vel + random.randint(-4, 4))),
            ))
        return notes

    def _render_march(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        t = start
        while t < start + duration:
            beat = t - start
            is_strong = (int(beat) % 2 == 0)
            vel = int((80 if is_strong else 60) + random.randint(-5, 5))
            notes.append(NoteInfo(
                pitch=BASS_DRUM_GRAN_CASSA,
                start=round(t, 6),
                duration=1.5,
                velocity=max(1, min(127, vel)),
            ))
            t += 1.0
        return notes


class TamTamGenerator(PhraseGenerator):
    """Tam-tam (large gong) -- deep, resonant, long decay.

    pattern_type:
        "strike"           -- single deep hit with long ring.
        "crescendo_strike" -- soft roll building to a loud hit.
        "tremolo"          -- rapid soft strokes for sustained shimmer.
    """

    name: str = "Tam-Tam Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern_type: str = "strike",
    ) -> None:
        super().__init__(params)
        self.pattern_type = pattern_type
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

        notes: list[NoteInfo] = []
        for i, chord in enumerate(chords):
            is_first = (i == 0)
            if self.pattern_type == "strike":
                notes.extend(self._render_strike(chord.start, chord.duration, is_first))
            elif self.pattern_type == "crescendo_strike":
                notes.extend(self._render_crescendo(chord.start, chord.duration))
            else:
                notes.extend(self._render_tremolo(chord.start, chord.duration))

        if notes:
            notes.sort(key=lambda n: n.start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )
        return notes

    def _render_strike(self, start: float, duration: float, is_first: bool) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        prob = 1.0 if is_first else self.params.density * 0.2
        if random.random() < prob:
            vel = int(80 + random.randint(0, 30))
            ring = max(4.0, duration * 1.2)
            notes.append(NoteInfo(
                pitch=TAM_TAM,
                start=round(start, 6),
                duration=ring,
                velocity=max(1, min(127, vel)),
            ))
        return notes

    def _render_crescendo(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        step = 0.5
        steps = max(4, int(duration * 0.7 / step))
        for s in range(steps):
            t = start + s * step
            progress = s / steps
            vel = int(25 + 60 * progress ** 2)
            notes.append(NoteInfo(
                pitch=TAM_TAM,
                start=round(t, 6),
                duration=step * 1.5,
                velocity=max(1, min(127, vel + random.randint(-3, 3))),
            ))
        # Final strike
        peak_t = start + steps * step
        notes.append(NoteInfo(
            pitch=TAM_TAM,
            start=round(peak_t, 6),
            duration=max(6.0, duration * 0.4),
            velocity=120,
        ))
        return notes

    def _render_tremolo(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        step = 0.25
        t = start
        while t < start + duration:
            vel = int(40 + random.randint(-5, 10))
            notes.append(NoteInfo(
                pitch=TAM_TAM,
                start=round(t, 6),
                duration=step * 1.2,
                velocity=max(1, min(127, vel)),
            ))
            t += step
        return notes


class GongGenerator(PhraseGenerator):
    """Gong -- pitched bronze gong with rich harmonics.

    pattern_type:
        "strike"    -- single deep hit.
        "roll"      -- crescendo roll leading to a strike.
        "crescendo" -- gradually increasing intensity hits.
    """

    name: str = "Gong Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern_type: str = "strike",
    ) -> None:
        super().__init__(params)
        self.pattern_type = pattern_type
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

        notes: list[NoteInfo] = []
        for i, chord in enumerate(chords):
            is_first = (i == 0)
            if self.pattern_type == "strike":
                notes.extend(self._render_strike(chord.start, chord.duration, is_first))
            elif self.pattern_type == "roll":
                notes.extend(self._render_roll(chord.start, chord.duration))
            else:
                notes.extend(self._render_crescendo(chord.start, chord.duration))

        if notes:
            notes.sort(key=lambda n: n.start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )
        return notes

    def _render_strike(self, start: float, duration: float, is_first: bool) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        prob = 1.0 if is_first else self.params.density * 0.25
        if random.random() < prob:
            vel = int(85 + random.randint(0, 25))
            notes.append(NoteInfo(
                pitch=GONG,
                start=round(start, 6),
                duration=max(6.0, duration),
                velocity=max(1, min(127, vel)),
            ))
        return notes

    def _render_roll(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        step = 0.375
        steps = max(4, int(duration * 0.6 / step))
        for s in range(steps):
            t = start + s * step
            progress = s / steps
            vel = int(20 + 80 * progress ** 1.6)
            notes.append(NoteInfo(
                pitch=GONG,
                start=round(t, 6),
                duration=step * 1.5,
                velocity=max(1, min(127, vel + random.randint(-3, 3))),
            ))
        notes.append(NoteInfo(
            pitch=GONG,
            start=round(start + steps * step, 6),
            duration=max(5.0, duration * 0.5),
            velocity=115,
        ))
        return notes

    def _render_crescendo(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        hits = max(2, int(self.params.density * 6))
        spacing = duration / hits
        for h in range(hits):
            t = start + h * spacing
            progress = h / max(1, hits - 1)
            vel = int(40 + 70 * progress)
            notes.append(NoteInfo(
                pitch=GONG,
                start=round(t, 6),
                duration=max(3.0, spacing * 2),
                velocity=max(1, min(127, vel)),
            ))
        return notes


class TriangleGenerator(PhraseGenerator):
    """Triangle -- bright, high metallic ping.

    pattern_type:
        "single" -- isolated hits.
        "roll"   -- sustained trill/roll.
        "trill"  -- rapid alternating strokes.
    """

    name: str = "Triangle Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern_type: str = "single",
    ) -> None:
        super().__init__(params)
        self.pattern_type = pattern_type
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

        notes: list[NoteInfo] = []
        for chord in chords:
            if self.pattern_type == "single":
                notes.extend(self._render_single(chord.start, chord.duration))
            elif self.pattern_type == "roll":
                notes.extend(self._render_roll(chord.start, chord.duration))
            else:
                notes.extend(self._render_trill(chord.start, chord.duration))

        if notes:
            notes.sort(key=lambda n: n.start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )
        return notes

    def _render_single(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        if random.random() < self.params.density * 0.6:
            vel = int(50 + random.randint(0, 20))
            notes.append(NoteInfo(
                pitch=TRIANGLE,
                start=round(start, 6),
                duration=max(1.0, duration * 0.5),
                velocity=max(1, min(127, vel)),
            ))
        return notes

    def _render_roll(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        step = 0.25
        steps = max(4, int(duration / step))
        for s in range(steps):
            t = start + s * step
            if t >= start + duration:
                break
            progress = s / steps
            vel = int(30 + 30 * progress)
            notes.append(NoteInfo(
                pitch=TRIANGLE,
                start=round(t, 6),
                duration=step * 0.9,
                velocity=max(1, min(127, vel + random.randint(-3, 3))),
            ))
        return notes

    def _render_trill(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        step = 0.125
        t = start
        while t < start + duration:
            vel = int(45 + random.randint(-5, 10))
            notes.append(NoteInfo(
                pitch=TRIANGLE,
                start=round(t, 6),
                duration=step * 1.1,
                velocity=max(1, min(127, vel)),
            ))
            t += step
        return notes


class CastanetsGenerator(PhraseGenerator):
    """Castanets -- Spanish/Flamenco percussive clicks.

    pattern_type:
        "single" -- isolated click.
        "roll"   -- rapid continuous roll.
        "rhythm" -- characteristic dotted rhythm pattern.
    """

    name: str = "Castanets Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern_type: str = "single",
    ) -> None:
        super().__init__(params)
        self.pattern_type = pattern_type
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

        notes: list[NoteInfo] = []
        for chord in chords:
            if self.pattern_type == "single":
                notes.extend(self._render_single(chord.start, chord.duration))
            elif self.pattern_type == "roll":
                notes.extend(self._render_roll(chord.start, chord.duration))
            else:
                notes.extend(self._render_rhythm(chord.start, chord.duration))

        if notes:
            notes.sort(key=lambda n: n.start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )
        return notes

    def _render_single(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        if random.random() < self.params.density * 0.7:
            vel = int(60 + random.randint(0, 20))
            notes.append(NoteInfo(
                pitch=CASTANETS,
                start=round(start, 6),
                duration=0.25,
                velocity=max(1, min(127, vel)),
            ))
        return notes

    def _render_roll(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        step = 0.125
        t = start
        while t < start + duration:
            vel = int(55 + random.randint(-8, 12))
            notes.append(NoteInfo(
                pitch=CASTANETS,
                start=round(t, 6),
                duration=0.1,
                velocity=max(1, min(127, vel)),
            ))
            t += step
        return notes

    def _render_rhythm(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        # Dotted rhythm: long-short pattern per beat
        t = start
        while t < start + duration:
            # Long (dotted 8th)
            vel = int(70 + random.randint(-5, 10))
            notes.append(NoteInfo(
                pitch=CASTANETS,
                start=round(t, 6),
                duration=0.25,
                velocity=max(1, min(127, vel)),
            ))
            # Short (16th)
            notes.append(NoteInfo(
                pitch=CASTANETS,
                start=round(t + 0.75, 6),
                duration=0.15,
                velocity=max(1, min(127, vel - 10)),
            ))
            t += 1.0
        return notes


class WhipSlapstickGenerator(PhraseGenerator):
    """Whip / Slapstick -- sharp crack sound effect.

    pattern_type:
        "single" -- isolated whip crack.
        "rapid"  -- two or three quick successive cracks.
    """

    name: str = "Whip/Slapstick Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern_type: str = "single",
    ) -> None:
        super().__init__(params)
        self.pattern_type = pattern_type
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

        notes: list[NoteInfo] = []
        for i, chord in enumerate(chords):
            is_first = (i == 0)
            if self.pattern_type == "single":
                notes.extend(self._render_single(chord.start, chord.duration, is_first))
            else:
                notes.extend(self._render_rapid(chord.start, chord.duration))

        if notes:
            notes.sort(key=lambda n: n.start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )
        return notes

    def _render_single(self, start: float, duration: float, is_first: bool) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        prob = 1.0 if is_first else self.params.density * 0.3
        if random.random() < prob:
            vel = int(100 + random.randint(0, 27))
            notes.append(NoteInfo(
                pitch=SLAPSTICK,
                start=round(start, 6),
                duration=0.3,
                velocity=max(1, min(127, vel)),
            ))
        return notes

    def _render_rapid(self, start: float, duration: float) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        count = random.choice([2, 3])
        spacing = 0.15
        for c in range(count):
            vel = int(95 + random.randint(0, 25))
            notes.append(NoteInfo(
                pitch=SLAPSTICK,
                start=round(start + c * spacing, 6),
                duration=0.2,
                velocity=max(1, min(127, vel - c * 8)),
            ))
        return notes
