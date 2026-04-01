"""
generators/procedural_exploration.py — Procedural exploration music generator.

Layer: Application / Domain
Style: Open world games, exploration, No Man's Sky, Minecraft.

Generates music designed for infinite looping during exploration:
  - Self-contained musical cells that loop seamlessly
  - Parameterized mood shifts
  - Horizontal resequencing friendly
  - Low cognitive load (doesn't distract from gameplay)

Variants:
    "nature"      — natural, organic exploration
    "sci_fi"      — alien worlds, space exploration
    "underwater"  — underwater, aquatic
    "desert"      — desert/arid landscapes
    "forest"      — enchanted forest
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


@dataclass
class ProceduralExplorationGenerator(PhraseGenerator):
    """
    Procedural exploration music generator.

    variant:
        "nature", "sci_fi", "underwater", "desert", "forest"
    mood:
        "peaceful", "curious", "wonder", "uneasy" — mood shift within exploration.
    loop_length_bars:
        Length of the musical cell in bars (2-8). Shorter = more repetitive, longer = more varied.
    density:
        Overall note density (0.0-1.0). Exploration should be low (0.2-0.5).
    """

    name: str = "Procedural Exploration Generator"
    variant: str = "nature"
    mood: str = "peaceful"
    loop_length_bars: int = 4
    density: float = 0.35
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "nature",
        mood: str = "peaceful",
        loop_length_bars: int = 4,
        density: float = 0.35,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.mood = mood
        self.loop_length_bars = max(2, min(8, loop_length_bars))
        self.density = max(0.1, min(1.0, density))

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
        loop_beats = self.loop_length_bars * 4
        bar_start = 0.0

        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            self._render_pad(notes, bar_start, min(bar_start + loop_beats, duration_beats), chord)
            self._render_melody(
                notes, bar_start, min(bar_start + loop_beats, duration_beats), chord, key
            )
            if self.variant in ("nature", "forest"):
                self._render_birds(
                    notes, bar_start, min(bar_start + loop_beats, duration_beats), chord
                )

            bar_start += loop_beats

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_pad(self, notes, bar_start, total, chord):
        mid = 48 if self.variant == "underwater" else 54
        pcs = chord.pitch_classes()[:3]
        vel = {"peaceful": 35, "curious": 40, "wonder": 45, "uneasy": 30}.get(self.mood, 35)
        if bar_start < total:
            for pc in pcs:
                pitch = nearest_pitch(pc, mid)
                dur = min(total - bar_start, 3.8)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=dur, velocity=vel)
                )

    def _render_melody(self, notes, bar_start, total, chord, key):
        mid = 72
        scale_pcs = [int(d) for d in key.degrees()]
        t = bar_start
        prev = mid
        while t < total:
            if random.random() < self.density:
                pc = random.choice(scale_pcs)
                pitch = nearest_pitch(pc, prev)
                pitch = max(54, min(84, pitch))
                dur = random.choice([1.0, 1.5, 2.0, 2.5])
                vel = {"peaceful": 45, "curious": 50, "wonder": 55, "uneasy": 40}.get(self.mood, 45)
                notes.append(NoteInfo(pitch=pitch, start=round(t, 6), duration=dur, velocity=vel))
                prev = pitch
                t += dur + random.uniform(0, 1.0)
            else:
                t += 1.0

    def _render_birds(self, notes, bar_start, total, chord):
        """High-pitched random notes simulating birds/insects."""
        mid = 84
        for t_off in [0.5, 1.5, 2.5, 3.5]:
            if random.random() < self.density * 0.5:
                onset = bar_start + t_off + random.uniform(-0.2, 0.2)
                if onset < total and onset >= bar_start:
                    pitch = mid + random.randint(-6, 6)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=0.15,
                            velocity=30 + random.randint(0, 15),
                        )
                    )
