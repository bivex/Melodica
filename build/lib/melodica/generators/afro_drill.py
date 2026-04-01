"""
generators/afro_drill.py — Afro Drill pattern generator.

Layer: Application / Domain
Style: Afro drill, Afro-drill fusion, Burna Boy style.

Fusion of Afrobeats melodies with drill drums:
  - African melodies over drill 808s
  - Sliding 808 with Afro rhythm
  - Drill hi-hats with Afro groove
  - Call-response elements
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
class AfroDrillGenerator(PhraseGenerator):
    """Afro Drill generator. variant: burna, rema, central, classic."""

    name: str = "Afro Drill Generator"
    variant: str = "burna"
    slide_amount: int = 7
    melody_density: float = 0.6
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "burna",
        slide_amount: int = 7,
        melody_density: float = 0.6,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.slide_amount = max(0, min(12, slide_amount))
        self.melody_density = max(0.0, min(1.0, melody_density))

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
            self._render_808(notes, bar_start, duration_beats, chord, low)
            self._render_drums(notes, bar_start, duration_beats)
            self._render_melody(notes, bar_start, duration_beats, chord, key)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_808(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        offsets = [(0.0, 1.5), (1.5, 0.5), (2.5, 1.3)]
        prev = pitch
        for off, dur in offsets:
            onset = bar_start + off
            if onset >= total:
                continue
            p = pitch
            if random.random() < 0.4 and self.slide_amount > 0:
                slide_pc = (chord.root + self.slide_amount) % 12
                p = max(low, min(low + 12, nearest_pitch(slide_pc, prev)))
            notes.append(NoteInfo(pitch=p, start=round(onset, 6), duration=dur, velocity=95))
            prev = p

    def _render_drums(self, notes, bar_start, total):
        for beat in [1, 3]:
            onset = bar_start + beat + 0.25
            if onset < total:
                notes.append(
                    NoteInfo(pitch=SNARE, start=round(onset, 6), duration=0.25, velocity=110)
                )
                notes.append(NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.2, velocity=85))
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            vel = 75 if i % 2 == 0 else 55
            notes.append(
                NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.1, velocity=vel)
            )
            if random.random() < 0.2:
                for r in range(3):
                    r_onset = onset + r * 0.125
                    if r_onset < total:
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED, start=round(r_onset, 6), duration=0.06, velocity=45
                            )
                        )

    def _render_melody(self, notes, bar_start, total, chord, key):
        mid = 72
        pentatonic = [
            chord.root,
            (chord.root + 3) % 12,
            (chord.root + 5) % 12,
            (chord.root + 7) % 12,
            (chord.root + 10) % 12,
        ]
        t = bar_start
        prev = mid
        while t < min(bar_start + 4.0, total):
            if random.random() < self.melody_density:
                pc = random.choice(pentatonic)
                pitch = nearest_pitch(pc, prev)
                dur = random.choice([0.5, 1.0])
                notes.append(
                    NoteInfo(
                        pitch=max(60, min(84, pitch)), start=round(t, 6), duration=dur, velocity=70
                    )
                )
                prev = pitch
            t += 0.5
