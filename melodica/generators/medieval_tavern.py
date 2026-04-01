"""
generators/medieval_tavern.py — Medieval tavern / RPG ambient music generator.

Layer: Application / Domain
Style: RPG, fantasy, medieval, tavern music.

Generates medieval/fantasy music:
  - Lute-like arpeggiated patterns
  - Flute melodies in modal scales
  - Dance rhythms (6/8, 3/4)
  - Modal scales (Dorian, Mixolydian, Aeolian)

Variants:
    "tavern"    — lively tavern music
    "court"     — noble court, stately
    "journey"   — travel/exploration
    "battle_camp" — pre-battle camp
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


@dataclass
class MedievalTavernGenerator(PhraseGenerator):
    """
    Medieval tavern / RPG ambient music generator.

    variant:
        "tavern", "court", "journey", "battle_camp"
    mode:
        "dorian", "mixolydian", "aeolian" — modal scale preference.
    lute_density:
        Density of lute arpeggios (0.0-1.0).
    include_flute:
        Whether to include flute melody.
    dance_rhythm:
        Whether to use dance-like rhythm (6/8 feel in 4/4).
    """

    name: str = "Medieval Tavern Generator"
    variant: str = "tavern"
    mode: str = "dorian"
    lute_density: float = 0.7
    include_flute: bool = True
    dance_rhythm: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "tavern",
        mode: str = "dorian",
        lute_density: float = 0.7,
        include_flute: bool = True,
        dance_rhythm: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.mode = mode
        self.lute_density = max(0.0, min(1.0, lute_density))
        self.include_flute = include_flute
        self.dance_rhythm = dance_rhythm

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
            self._render_lute(notes, bar_start, duration_beats, chord, key)
            if self.include_flute:
                self._render_flute(notes, bar_start, duration_beats, chord, key)
            self._render_drone(notes, bar_start, duration_beats, chord)
            bar_start += 4.0

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_lute(self, notes, bar_start, total, chord, key):
        mid = 66
        root = chord.root
        pcs = [root, (root + 3 if self.mode == "aeolian" else root + 4) % 12, (root + 7) % 12]
        if self.dance_rhythm:
            # 6/8 feel: groups of 3
            offsets = [0.0, 0.67, 1.33, 2.0, 2.67, 3.33]
        else:
            offsets = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
        t = bar_start
        for off in offsets:
            if random.random() > self.lute_density:
                continue
            onset = bar_start + off
            if onset >= total:
                break
            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, mid)
            notes.append(
                NoteInfo(
                    pitch=max(48, min(84, pitch)), start=round(onset, 6), duration=0.3, velocity=60
                )
            )

    def _render_flute(self, notes, bar_start, total, chord, key):
        mid = 78
        scale_pcs = [int(d) for d in key.degrees()]
        t = bar_start
        prev = mid
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.5:
                pc = random.choice(scale_pcs)
                pitch = nearest_pitch(pc, prev)
                pitch = max(60, min(96, pitch))
                dur = random.choice([0.5, 1.0, 1.5])
                vel = 55 if self.variant == "court" else 60
                notes.append(NoteInfo(pitch=pitch, start=round(t, 6), duration=dur, velocity=vel))
                prev = pitch
                t += dur
            else:
                t += 0.5

    def _render_drone(self, notes, bar_start, total, chord):
        low = max(30, self.params.key_range_low)
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        if bar_start < total:
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=40)
            )
