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
generators/soukous_guitar.py — Soukous / Rumba Guitar pattern generator.

Layer: Application / Domain
Style: Soukous, Rumba, Congolese, Sebene, Ndombolo.

Generates Congolese guitar patterns:
  - Sebene (cascading arpeggio runs)
  - Rumba guitar comping
  - Interlocking guitar parts
  - Pentatonic melodies

Variants:
    "soukous"    — fast soukous/sebene runs
    "rumba"      — Congolese rumba (slower, melodic)
    "ndombolo"   — Ndombolo (dance-oriented)
    "cavacha"    — Cavacha rhythm guitar
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


@dataclass
class SoukousGuitarGenerator(PhraseGenerator):
    """Soukous / Rumba Guitar generator. variant: soukous, rumba, ndombolo, cavacha."""

    name: str = "Soukous Guitar Generator"
    variant: str = "soukous"
    run_speed: str = "sixteenth"
    note_density: float = 0.8
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "soukous",
        run_speed: str = "sixteenth",
        note_density: float = 0.8,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.run_speed = run_speed
        self.note_density = max(0.0, min(1.0, note_density))

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
        last_chord = chords[-1]
        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue
            self._render_pattern(notes, bar_start, duration_beats, chord, key)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_pattern(self, notes, bar_start, total, chord, key):
        mid = 66
        root = chord.root
        pentatonic = [root, (root + 3) % 12, (root + 5) % 12, (root + 7) % 12, (root + 10) % 12]

        if self.variant == "soukous":
            # Sebene: fast cascading runs
            sub = {"sixteenth": 0.25, "triplet": 1 / 3, "eighth": 0.5}.get(self.run_speed, 0.25)
            t = bar_start
            prev = nearest_pitch(root, mid)
            direction = 1
            while t < min(bar_start + 4.0, total):
                if random.random() < self.note_density:
                    idx = (
                        pentatonic.index(
                            min(pentatonic, key=lambda pc: abs(nearest_pitch(pc, prev) - prev))
                        )
                        if pentatonic
                        else 0
                    )
                    next_idx = (idx + direction) % len(pentatonic)
                    pitch = nearest_pitch(pentatonic[next_idx], prev)
                    if pitch > 84:
                        direction = -1
                    elif pitch < 48:
                        direction = 1
                    notes.append(
                        NoteInfo(
                            pitch=max(48, min(84, pitch)),
                            start=round(t, 6),
                            duration=sub * 0.7,
                            velocity=75,
                        )
                    )
                    prev = pitch
                t += sub

        elif self.variant == "rumba":
            # Rumba: melodic, arpeggiated
            offsets = [0.0, 0.75, 1.0, 1.75, 2.0, 2.75, 3.0, 3.75]
            prev = nearest_pitch(root, mid)
            for off in offsets:
                if random.random() > self.note_density:
                    continue
                onset = bar_start + off
                if onset >= total:
                    break
                pc = random.choice(pentatonic)
                pitch = nearest_pitch(pc, prev)
                notes.append(
                    NoteInfo(
                        pitch=max(48, min(84, pitch)),
                        start=round(onset, 6),
                        duration=0.5,
                        velocity=65,
                    )
                )
                prev = pitch

        elif self.variant == "cavacha":
            # Cavacha: driving rhythm pattern
            for i in range(8):
                onset = bar_start + i * 0.5
                if onset >= total:
                    break
                pc = pentatonic[i % len(pentatonic)]
                pitch = nearest_pitch(pc, mid)
                vel = 80 if i % 2 == 0 else 60
                notes.append(
                    NoteInfo(
                        pitch=max(48, min(84, pitch)),
                        start=round(onset, 6),
                        duration=0.3,
                        velocity=vel,
                    )
                )

        else:  # ndombolo
            sub = 0.25
            t = bar_start
            prev = nearest_pitch(root, mid)
            while t < min(bar_start + 4.0, total):
                if random.random() < self.note_density * 0.8:
                    pc = random.choice(pentatonic)
                    pitch = nearest_pitch(pc, prev)
                    notes.append(
                        NoteInfo(
                            pitch=max(48, min(84, pitch)),
                            start=round(t, 6),
                            duration=sub * 0.8,
                            velocity=70,
                        )
                    )
                    prev = pitch
                t += sub
