"""
generators/kuduro.py — Kuduro / Kwaito pattern generator.

Layer: Application / Domain
Style: Kuduro, Kwaito, Angolan dance, South African house.

Generates:
  - Fast, aggressive kuduro rhythms
  - Kwaito slow house grooves
  - Characteristic percussion patterns

Variants:
    "kuduro"    — Angolan kuduro (fast, aggressive)
    "kwaito"    — South African kwaito (slower, groove)
    "afro_tech" — Afro-tech fusion
    "tarraxinha" — Tarraxinha (slow, sensual kuduro)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
CLAP = 39


@dataclass
class KuduroGenerator(PhraseGenerator):
    """Kuduro / Kwaito generator. variant: kuduro, kwaito, afro_tech, tarraxinha."""

    name: str = "Kuduro Generator"
    variant: str = "kuduro"
    intensity: float = 0.7
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "kuduro",
        intensity: float = 0.7,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.intensity = max(0.0, min(1.0, intensity))

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
        low = max(24, self.params.key_range_low)
        last_chord = chords[-1]
        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue
            self._render_pattern(notes, bar_start, duration_beats, chord, low)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_pattern(self, notes, bar_start, total, chord, low):
        vel = int(90 + self.intensity * 20)
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))

        if self.variant == "kuduro":
            # Fast, syncopated
            kick_offs = [0.0, 0.5, 1.0, 2.0, 2.5, 3.0, 3.5]
            for off in kick_offs:
                onset = bar_start + off
                if onset >= total:
                    continue
                is_main = off in (0.0, 2.0)
                v = vel if is_main else int(vel * 0.7)
                notes.append(NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.2, velocity=v))
                if is_main:
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.5, velocity=v)
                    )
            # Hi-hats fast
            for i in range(16):
                onset = bar_start + i * 0.25
                if onset >= total:
                    break
                if random.random() < 0.8:
                    notes.append(
                        NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.06, velocity=55)
                    )
            for beat in [1, 3]:
                if bar_start + beat < total:
                    notes.append(
                        NoteInfo(
                            pitch=SNARE,
                            start=round(bar_start + beat, 6),
                            duration=0.2,
                            velocity=105,
                        )
                    )

        elif self.variant == "kwaito":
            # Slower, groove-heavy
            for off in [0.0, 1.5, 2.0, 3.5]:
                onset = bar_start + off
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.3, velocity=vel)
                    )
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.5, velocity=vel - 5)
            )
            for i in range(8):
                if random.random() < 0.6:
                    onset = bar_start + i * 0.5
                    if onset < total:
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED, start=round(onset, 6), duration=0.1, velocity=50
                            )
                        )
            for beat in [2]:
                if bar_start + beat < total:
                    notes.append(
                        NoteInfo(
                            pitch=SNARE, start=round(bar_start + beat, 6), duration=0.2, velocity=95
                        )
                    )
                    notes.append(
                        NoteInfo(
                            pitch=CLAP, start=round(bar_start + beat, 6), duration=0.15, velocity=80
                        )
                    )

        elif self.variant == "tarraxinha":
            # Slow, sensual
            for off in [0.0, 2.0]:
                onset = bar_start + off
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.4, velocity=vel)
                    )
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=vel - 10)
            )
            for i in range(4):
                if random.random() < 0.5:
                    onset = bar_start + i
                    if onset < total:
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED, start=round(onset, 6), duration=0.1, velocity=40
                            )
                        )

        else:  # afro_tech
            for beat in range(4):
                onset = bar_start + beat
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.3, velocity=vel)
                    )
            for i in range(8):
                onset = bar_start + i * 0.5
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.08, velocity=65)
                    )
            for beat in [1, 3]:
                if bar_start + beat < total:
                    notes.append(
                        NoteInfo(
                            pitch=CLAP, start=round(bar_start + beat, 6), duration=0.15, velocity=85
                        )
                    )
