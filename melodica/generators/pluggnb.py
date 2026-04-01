"""
generators/pluggnb.py — Pluggnb pattern generator.

Layer: Application / Domain
Style: Pluggnb, plugg, melodic plugg.

Generates characteristic pluggnb elements:
  - Soft pads with 7th/9th chords
  - 808 with slides
  - Minimal, sparse drums
  - R&B influenced melodies
  - Gentle hi-hats

Variants:
    "pluggnb"     — standard pluggnb (R&B influenced)
    "plugg"       — harder plugg
    "melodic"     — melody-focused pluggnb
    "dark_plugg"  — darker, minor key plugg
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
RIM = 37


@dataclass
class PluggnbGenerator(PhraseGenerator):
    """
    Pluggnb pattern generator.

    variant:
        "pluggnb", "plugg", "melodic", "dark_plugg"
    pad_voicing:
        Chord extension level: "seventh", "ninth", "eleventh".
    include_808:
        Whether to include 808 bass with slides.
    hat_style:
        "gentle", "sparse", "absent" — hi-hat density.
    melody_register:
        Preferred melody octave (3-6).
    """

    name: str = "Pluggnb Generator"
    variant: str = "pluggnb"
    pad_voicing: str = "ninth"
    include_808: bool = True
    hat_style: str = "gentle"
    melody_register: int = 5
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "pluggnb",
        pad_voicing: str = "ninth",
        include_808: bool = True,
        hat_style: str = "gentle",
        melody_register: int = 5,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.pad_voicing = pad_voicing
        self.include_808 = include_808
        self.hat_style = hat_style
        self.melody_register = max(3, min(6, melody_register))

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

            # Soft pad chords
            self._render_pad(notes, bar_start, duration_beats, chord)

            # 808 bass
            if self.include_808:
                self._render_808(notes, bar_start, duration_beats, chord, low)

            # Drums (sparse)
            self._render_drums(notes, bar_start, duration_beats)

            # Melody
            if self.variant in ("melodic", "pluggnb"):
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

    def _render_pad(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        mid = 60
        root_pc = chord.root
        is_minor = chord.quality.name in ("MINOR", "MIN7")
        third_pc = (root_pc + (3 if is_minor else 4)) % 12
        fifth_pc = (root_pc + 7) % 12
        pcs = [root_pc, third_pc, fifth_pc]

        if self.pad_voicing in ("seventh", "ninth", "eleventh"):
            pcs.append((root_pc + 10) % 12)
        if self.pad_voicing in ("ninth", "eleventh"):
            pcs.append((root_pc + 14) % 12)

        onset = bar_start
        if onset < total:
            for pc in pcs:
                pitch = nearest_pitch(pc, mid)
                vel = 50 if self.variant == "dark_plugg" else 55
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=3.8, velocity=vel)
                )

    def _render_808(
        self,
        notes: list[NoteInfo],
        bar_start: float,
        total: float,
        chord: ChordLabel,
        low: int,
    ) -> None:
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        if self.variant == "plugg":
            offsets = [(0.0, 1.8), (2.0, 1.8)]
        else:
            offsets = [(0.0, 3.5)]
        for off, dur in offsets:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=dur, velocity=85)
                )

    def _render_drums(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        # Kick — sparse
        if bar_start < total:
            notes.append(NoteInfo(pitch=KICK, start=round(bar_start, 6), duration=0.3, velocity=95))

        # Snare — soft
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total:
                pitch = RIM if self.variant == "dark_plugg" else SNARE
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.15, velocity=80)
                )

        # Hi-hats
        if self.hat_style == "gentle":
            for i in range(8):
                onset = bar_start + i * 0.5
                if onset >= total:
                    break
                if random.random() < 0.7:
                    notes.append(
                        NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.1, velocity=45)
                    )
        elif self.hat_style == "sparse":
            for beat in [0, 2]:
                onset = bar_start + beat
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=HH_CLOSED, start=round(onset, 6), duration=0.1, velocity=40)
                    )

    def _render_melody(
        self,
        notes: list[NoteInfo],
        bar_start: float,
        total: float,
        chord: ChordLabel,
        key: Scale,
    ) -> None:
        mid = self.melody_register * 12
        scale_pcs = [int(d) for d in key.degrees()]
        pos = bar_start
        prev = mid

        while pos < min(bar_start + 4.0, total):
            if random.random() < 0.65:
                pc = random.choice(scale_pcs)
                pitch = nearest_pitch(pc, prev)
                pitch = max(48, min(84, pitch))
                dur = random.choice([0.5, 1.0, 1.5])
                notes.append(NoteInfo(pitch=pitch, start=round(pos, 6), duration=dur, velocity=60))
                prev = pitch
            pos += 0.5
