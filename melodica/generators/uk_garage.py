"""
generators/uk_garage.py — UK Garage / 2-Step pattern generator.

Layer: Application / Domain
Style: UK Garage, 2-Step, Speed Garage, Bassline.

Generates characteristic UK Garage elements:
  - Shuffled 2-step drum patterns
  - Skippy hi-hat patterns
  - Vocal-style chopped stabs
  - Deep bass wobbles
  - Organ-style chord stabs

Variants:
    "2step"         — classic 2-step garage
    "speed_garage"  — speed garage (faster, more aggressive)
    "bassline"      — Niche/bassline (heavy bass focus)
    "dark_garage"   — dark garage (atmospheric, minimal)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
CLAP = 39
RIM = 37


@dataclass
class UKGarageGenerator(PhraseGenerator):
    """
    UK Garage / 2-Step pattern generator.

    variant:
        "2step", "speed_garage", "bassline", "dark_garage"
    shuffle_amount:
        Amount of shuffle/swing (0.0-1.0). 2-step uses moderate shuffle.
    skippy_hats:
        Whether to use skippy, off-beat hi-hat patterns.
    include_stabs:
        Whether to include organ-style chord stabs.
    bass_wobble:
        Whether to include wobbly bass line.
    chop_density:
        Density of vocal-style chopped stabs (0.0-1.0).
    """

    name: str = "UK Garage Generator"
    variant: str = "2step"
    shuffle_amount: float = 0.55
    skippy_hats: bool = True
    include_stabs: bool = True
    bass_wobble: bool = True
    chop_density: float = 0.3
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "2step",
        shuffle_amount: float = 0.55,
        skippy_hats: bool = True,
        include_stabs: bool = True,
        bass_wobble: bool = True,
        chop_density: float = 0.3,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.shuffle_amount = max(0.0, min(1.0, shuffle_amount))
        self.skippy_hats = skippy_hats
        self.include_stabs = include_stabs
        self.bass_wobble = bass_wobble
        self.chop_density = max(0.0, min(1.0, chop_density))

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

            # 2-step kick pattern
            self._render_kick(notes, bar_start, duration_beats)

            # Snare/Clap
            self._render_snare(notes, bar_start, duration_beats)

            # Skippy hats
            if self.skippy_hats:
                self._render_hihats(notes, bar_start, duration_beats)

            # Organ stabs
            if self.include_stabs:
                self._render_stabs(notes, bar_start, duration_beats, chord)

            # Bass
            if self.bass_wobble:
                self._render_bass(notes, bar_start, duration_beats, chord)

            # Vocal chops
            self._render_chops(notes, bar_start, duration_beats, chord)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_kick(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        # 2-step: kick on 1, skip 2, kick on 3 (slightly off), skip 4
        if self.variant == "bassline":
            offsets = [0.0, 2.5]
        elif self.variant == "speed_garage":
            offsets = [0.0, 1.5, 2.0, 3.5]
        else:
            offsets = [0.0, 2.25]  # Characteristic 2-step placement

        for off in offsets:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=KICK,
                        start=round(onset, 6),
                        duration=0.3,
                        velocity=110,
                    )
                )

    def _render_snare(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        # Snare on 2 and 4, with ghost snares
        for beat in [1.0, 3.0]:
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=SNARE,
                        start=round(onset, 6),
                        duration=0.2,
                        velocity=105,
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=CLAP,
                        start=round(onset, 6),
                        duration=0.15,
                        velocity=85,
                    )
                )
            # Ghost snare
            ghost_onset = onset + 0.25
            if ghost_onset < total and random.random() < 0.4:
                notes.append(
                    NoteInfo(
                        pitch=RIM,
                        start=round(ghost_onset, 6),
                        duration=0.1,
                        velocity=40,
                    )
                )

    def _render_hihats(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        shuffle = self.shuffle_amount
        for beat in range(4):
            # First eighth
            onset1 = bar_start + beat
            if onset1 < total:
                notes.append(
                    NoteInfo(
                        pitch=HH_CLOSED,
                        start=round(onset1, 6),
                        duration=0.1,
                        velocity=65,
                    )
                )
            # Shuffled second eighth
            onset2 = bar_start + beat + shuffle * 0.5
            if onset2 < total and random.random() < 0.85:
                notes.append(
                    NoteInfo(
                        pitch=HH_CLOSED,
                        start=round(onset2, 6),
                        duration=0.1,
                        velocity=45,
                    )
                )
            # Skip hat (characteristic 2-step)
            if random.random() < 0.3:
                skip_onset = bar_start + beat + 0.75
                if skip_onset < total:
                    notes.append(
                        NoteInfo(
                            pitch=HH_OPEN,
                            start=round(skip_onset, 6),
                            duration=0.25,
                            velocity=50,
                        )
                    )

    def _render_stabs(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        root_pc = chord.root
        mid = 60
        is_minor = chord.quality.name in ("MINOR", "MIN7")
        third_pc = (root_pc + (3 if is_minor else 4)) % 12
        fifth_pc = (root_pc + 7) % 12

        pcs = [root_pc, third_pc, fifth_pc]

        # Rhythmic stab pattern
        for offset in [0.0, 1.5, 3.0]:
            if offset > 0 and random.random() < 0.3:
                continue
            onset = bar_start + offset
            if onset >= total:
                continue
            for pc in pcs:
                pitch = nearest_pitch(pc, mid)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=0.5,
                        velocity=70,
                    )
                )

    def _render_bass(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        root_pc = chord.root
        low = max(30, self.params.key_range_low)
        pitch = max(low, nearest_pitch(root_pc, low + 6))

        if self.variant == "bassline":
            # Heavy bassline
            offsets = [(0.0, 0.8), (1.0, 0.8), (2.0, 0.8), (3.0, 0.8)]
        else:
            offsets = [(0.0, 1.8), (2.5, 1.3)]

        for off, dur in offsets:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=dur,
                        velocity=90,
                    )
                )

    def _render_chops(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        """Vocal-style chopped stabs."""
        if random.random() > self.chop_density:
            return
        root_pc = chord.root
        mid = 72
        # Short pitched hits
        for off in [0.5, 1.75, 3.25]:
            if random.random() < 0.5:
                continue
            onset = bar_start + off
            if onset >= total:
                continue
            pitch = nearest_pitch(root_pc, mid + random.choice([0, 3, 5, 7]))
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=0.15,
                    velocity=55 + random.randint(0, 15),
                )
            )
