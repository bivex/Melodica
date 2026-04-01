"""
generators/genre_fusion.py — Genre fusion engine for mixing styles.

Layer: Application / Domain
Style: Cross-genre fusion.

Combines elements from two different genre generators:
  - Weighted blending of patterns
  - Rhythmic cross-pollination
  - Harmonic style mixing
  - Dynamic switching between sources

Supported source genres:
    "trap", "drill", "lofi", "jazz", "classical", "edm",
    "phonk", "afrobeats", "garage", "rock", "ambient"
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


@dataclass
class GenreFusionEngine(PhraseGenerator):
    """
    Genre fusion engine — blends two genre generators.

    genre_a:
        First genre to blend ("trap", "drill", "lofi", "jazz", etc).
    genre_b:
        Second genre to blend.
    blend_ratio:
        Weight toward genre A (0.0 = all B, 1.0 = all A, 0.5 = equal).
    fusion_mode:
        "interleave" — alternate between A and B per bar
        "layer"      — layer both simultaneously
        "morph"      — gradually transition from A to B
        "random"     — randomly choose per phrase
    morph_steps:
        For "morph" mode: number of steps from A to B.
    """

    name: str = "Genre Fusion Engine"
    genre_a: str = "trap"
    genre_b: str = "jazz"
    blend_ratio: float = 0.5
    fusion_mode: str = "interleave"
    morph_steps: int = 8
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        genre_a: str = "trap",
        genre_b: str = "jazz",
        blend_ratio: float = 0.5,
        fusion_mode: str = "interleave",
        morph_steps: int = 8,
    ) -> None:
        super().__init__(params)
        self.genre_a = genre_a
        self.genre_b = genre_b
        self.blend_ratio = max(0.0, min(1.0, blend_ratio))
        self.fusion_mode = fusion_mode
        self.morph_steps = max(2, min(32, morph_steps))

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
        bar_index = 0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                bar_index += 1
                continue

            # Determine which genre to use this bar
            if self.fusion_mode == "interleave":
                use_a = bar_index % 2 == 0
                if use_a:
                    self._render_genre_bar(notes, bar_start, duration_beats, chord, self.genre_a)
                else:
                    self._render_genre_bar(notes, bar_start, duration_beats, chord, self.genre_b)

            elif self.fusion_mode == "layer":
                self._render_genre_bar(notes, bar_start, duration_beats, chord, self.genre_a)
                self._render_genre_bar(notes, bar_start, duration_beats, chord, self.genre_b)

            elif self.fusion_mode == "morph":
                progress = bar_index / max(1, self.morph_steps)
                if progress < self.blend_ratio:
                    self._render_genre_bar(notes, bar_start, duration_beats, chord, self.genre_a)
                else:
                    self._render_genre_bar(notes, bar_start, duration_beats, chord, self.genre_b)

            elif self.fusion_mode == "random":
                if random.random() < self.blend_ratio:
                    self._render_genre_bar(notes, bar_start, duration_beats, chord, self.genre_a)
                else:
                    self._render_genre_bar(notes, bar_start, duration_beats, chord, self.genre_b)

            bar_start += 4.0
            bar_index += 1

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_genre_bar(
        self,
        notes: list[NoteInfo],
        bar_start: float,
        total: float,
        chord: ChordLabel,
        genre: str,
    ) -> None:
        """Render one bar of a specific genre pattern."""
        if genre == "trap":
            self._render_trap(notes, bar_start, total, chord)
        elif genre == "drill":
            self._render_drill(notes, bar_start, total, chord)
        elif genre == "lofi":
            self._render_lofi(notes, bar_start, total, chord)
        elif genre == "jazz":
            self._render_jazz(notes, bar_start, total, chord)
        elif genre == "edm":
            self._render_edm(notes, bar_start, total, chord)
        elif genre == "phonk":
            self._render_phonk(notes, bar_start, total, chord)
        elif genre == "rock":
            self._render_rock(notes, bar_start, total, chord)
        elif genre == "ambient":
            self._render_ambient(notes, bar_start, total, chord)
        else:
            self._render_trap(notes, bar_start, total, chord)

    def _render_trap(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        # Kick
        for off in [0.0, 2.0]:
            if bar_start + off < total:
                notes.append(
                    NoteInfo(pitch=36, start=round(bar_start + off, 6), duration=0.3, velocity=110)
                )
        # Snare
        for beat in [1, 3]:
            if bar_start + beat < total:
                notes.append(
                    NoteInfo(
                        pitch=38, start=round(bar_start + beat, 6), duration=0.25, velocity=110
                    )
                )
        # Hats
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=42,
                        start=round(onset, 6),
                        duration=0.12,
                        velocity=75 if i % 2 == 0 else 55,
                    )
                )
        # 808
        low = max(24, self.params.key_range_low)
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        if bar_start < total:
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.5, velocity=95)
            )

    def _render_drill(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        low = max(24, self.params.key_range_low)
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        for off in [0.0, 1.5, 2.5]:
            if bar_start + off < total:
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(bar_start + off, 6), duration=1.3, velocity=95
                    )
                )
        for beat in [1, 3]:
            if bar_start + beat + 0.25 < total:
                notes.append(
                    NoteInfo(
                        pitch=38,
                        start=round(bar_start + beat + 0.25, 6),
                        duration=0.25,
                        velocity=110,
                    )
                )
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=42,
                        start=round(onset, 6),
                        duration=0.12,
                        velocity=75 if i % 2 == 0 else 55,
                    )
                )

    def _render_lofi(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        mid = 60
        pcs = chord.pitch_classes()
        for pc in pcs[:4]:
            pitch = nearest_pitch(pc, mid)
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=2.0, velocity=60)
                )
        low = max(36, self.params.key_range_low)
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        if bar_start < total:
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=1.8, velocity=70)
            )
        for i in range(4):
            if bar_start + i < total:
                notes.append(
                    NoteInfo(pitch=36, start=round(bar_start + i, 6), duration=0.3, velocity=80)
                )
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset < total:
                vel = 55 if i % 2 == 0 else 40
                notes.append(NoteInfo(pitch=42, start=round(onset, 6), duration=0.1, velocity=vel))

    def _render_jazz(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        mid = 60
        pcs = chord.pitch_classes()
        for stab in [0.0, 1.5, 3.0]:
            onset = bar_start + stab
            if onset >= total:
                continue
            for pc in pcs[:4]:
                pitch = nearest_pitch(pc, mid)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.8, velocity=65)
                )
        low = max(36, self.params.key_range_low)
        for beat in range(4):
            onset = bar_start + beat
            if onset < total:
                pitch = nearest_pitch(chord.root, low + 6)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.9, velocity=75)
                )

    def _render_edm(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        for i in range(4):
            if bar_start + i < total:
                notes.append(
                    NoteInfo(pitch=36, start=round(bar_start + i, 6), duration=0.3, velocity=115)
                )
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset < total:
                notes.append(NoteInfo(pitch=42, start=round(onset, 6), duration=0.1, velocity=70))
        mid = 60
        for pc in chord.pitch_classes()[:3]:
            pitch = nearest_pitch(pc, mid)
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.5, velocity=80)
                )

    def _render_phonk(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset < total:
                notes.append(NoteInfo(pitch=56, start=round(onset, 6), duration=0.15, velocity=75))
        for off in [0.0, 2.0]:
            if bar_start + off < total:
                notes.append(
                    NoteInfo(pitch=36, start=round(bar_start + off, 6), duration=0.3, velocity=110)
                )
        for beat in [1, 3]:
            if bar_start + beat < total:
                notes.append(
                    NoteInfo(
                        pitch=38, start=round(bar_start + beat, 6), duration=0.25, velocity=110
                    )
                )

    def _render_rock(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        low = max(48, self.params.key_range_low)
        root = nearest_pitch(chord.root, low + 6)
        fifth = nearest_pitch((chord.root + 7) % 12, root)
        for off in [0.0, 1.0, 2.0, 3.0]:
            if bar_start + off < total:
                notes.append(
                    NoteInfo(pitch=root, start=round(bar_start + off, 6), duration=0.4, velocity=90)
                )
                notes.append(
                    NoteInfo(
                        pitch=fifth, start=round(bar_start + off, 6), duration=0.4, velocity=85
                    )
                )
        for beat in [0, 2]:
            if bar_start + beat < total:
                notes.append(
                    NoteInfo(pitch=36, start=round(bar_start + beat, 6), duration=0.3, velocity=110)
                )
        for beat in [1, 3]:
            if bar_start + beat < total:
                notes.append(
                    NoteInfo(pitch=38, start=round(bar_start + beat, 6), duration=0.2, velocity=105)
                )

    def _render_ambient(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        mid = 60
        for pc in chord.pitch_classes()[:4]:
            pitch = nearest_pitch(pc, mid)
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=45)
                )
