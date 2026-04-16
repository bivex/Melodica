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
generators/strings_pizzicato.py — Pizzicato string section generator.

Layer: Application / Domain
Style: Classical, film scoring, pop arrangements.

Pizzicato (plucked strings) produces short, percussive note attacks
with quick decay. Common in classical music for light, playful textures
and in film scoring for suspenseful or whimsical moods.

Patterns:
    "ostinato"  — repeating rhythmic pattern
    "random"    — random placement of plucks
    "waltz"     — pizzicato waltz pattern
    "tremolo"   — fast alternating between two notes
    "arco_mix"  — mixed arco/pizzicato (sustained + plucked)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


@dataclass
class StringsPizzicatoGenerator(PhraseGenerator):
    """
    Pizzicato string section generator.

    pattern:
        "ostinato", "random", "waltz", "tremolo", "arco_mix"
    staccato_length:
        Duration of each pizz note (typically very short: 0.1–0.3 beats).
    velocity_variation:
        Random velocity variation (0–1) for humanization.
    section_divisi:
        Number of instruments playing simultaneously (1–4).
    """

    name: str = "Strings Pizzicato Generator"
    pattern: str = "ostinato"
    staccato_length: float = 0.15
    velocity_variation: float = 0.3
    section_divisi: int = 2
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "ostinato",
        staccato_length: float = 0.15,
        velocity_variation: float = 0.3,
        section_divisi: int = 2,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.staccato_length = max(0.05, min(0.5, staccato_length))
        self.velocity_variation = max(0.0, min(1.0, velocity_variation))
        self.section_divisi = max(1, min(4, section_divisi))
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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord: ChordLabel | None = None
        prev_pitch = mid

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pcs = chord.pitch_classes()
            if not pcs:
                continue

            if self.pattern == "tremolo":
                # Rapid alternation between two chord tones
                t = event.onset
                end = event.onset + event.duration
                pc_a = pcs[0]
                pc_b = pcs[min(2, len(pcs) - 1)]
                pitch_a = nearest_pitch(int(pc_a), prev_pitch)
                pitch_a = snap_to_scale(pitch_a, key)
                pitch_b = nearest_pitch(int(pc_b), prev_pitch)
                pitch_b = snap_to_scale(pitch_b, key)
                use_a = True
                while t < end:
                    p = pitch_a if use_a else pitch_b
                    p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                    n_dur = min(0.125, end - t)
                    vel = self._velocity()
                    for d in range(self.section_divisi):
                        dp = p + d * random.choice([-3, -2, 2, 3])
                        dp = max(self.params.key_range_low, min(self.params.key_range_high, dp))
                        notes.append(
                            NoteInfo(
                                pitch=dp,
                                start=round(t, 6),
                                duration=n_dur,
                                velocity=max(1, vel - d * 3),
                            )
                        )
                    t += 0.125
                    use_a = not use_a
                prev_pitch = pitch_a
            else:
                # Single pluck event
                pc = random.choice(pcs)
                pitch = nearest_pitch(int(pc), prev_pitch)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

                vel = self._velocity()
                for d in range(self.section_divisi):
                    dp = pitch + d * random.choice([-3, -2, 2, 3])
                    dp = max(self.params.key_range_low, min(self.params.key_range_high, dp))
                    v = max(1, min(127, vel + random.randint(-5, 5)))
                    notes.append(
                        NoteInfo(
                            pitch=dp,
                            start=round(event.onset, 6),
                            duration=self.staccato_length,
                            velocity=v,
                        )
                    )
                prev_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        if self.pattern == "ostinato":
            # Eighth-note ostinato
            t, events = 0.0, []
            while t < duration_beats:
                for off in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(
                            RhythmEvent(onset=round(onset, 6), duration=self.staccato_length)
                        )
                t += 4.0
            return events

        elif self.pattern == "waltz":
            t, events = 0.0, []
            while t < duration_beats:
                for off in [0.0, 1.0, 2.0]:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(
                            RhythmEvent(onset=round(onset, 6), duration=self.staccato_length)
                        )
                t += 3.0
            return events

        elif self.pattern == "random":
            t, events = 0.0, []
            while t < duration_beats:
                num = random.randint(2, 8)
                for _ in range(num):
                    off = round(random.uniform(0, 3.9), 2)
                    onset = t + off
                    if onset < duration_beats:
                        events.append(
                            RhythmEvent(onset=round(onset, 6), duration=self.staccato_length)
                        )
                t += 4.0
            return events

        else:  # tremolo / arco_mix
            t, events = 0.0, []
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=min(4.0, duration_beats - t)))
                t += 4.0
            return events

    def _velocity(self) -> int:
        base = int(55 + self.params.density * 25)
        variation = int(base * self.velocity_variation * random.uniform(-0.5, 0.5))
        return max(1, min(127, base + variation))
