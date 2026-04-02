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
generators/chiptune.py — 8-bit / Chiptune pattern generator.

Layer: Application / Domain
Style: Chiptune, 8-bit, NES, Game Boy, retro gaming.

Emulates the NES APU sound channels:
  - Pulse 1: Lead melody (square wave, duty cycle)
  - Pulse 2: Harmony/counter (square wave)
  - Triangle: Bass line
  - Noise: Drums/percussion

Each channel has characteristic behavior:
  - Pulse: arpeggios, melodies, duty cycle variations
  - Triangle: simple bass, root + fifth
  - Noise: white noise percussion patterns

Variants:
    "nes_classic"  — classic NES game style
    "gameboy"      — Game Boy (more limited, punchy)
    "modern_chip"  — modern chiptune (more complex)
    "megadrive"    — Sega Genesis/Mega Drive style
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


NOISE_KICK = 36
NOISE_SNARE = 38
NOISE_HAT = 42


@dataclass
class ChiptuneGenerator(PhraseGenerator):
    """
    8-bit / Chiptune pattern generator.

    variant:
        "nes_classic", "gameboy", "modern_chip", "megadrive"
    channels:
        Which channels to generate: ["pulse1", "pulse2", "triangle", "noise"]
    duty_cycle:
        Pulse wave duty cycle: "12.5%", "25%", "50%", "75%".
        Affects timbre brightness.
    arpeggio_speed:
        Speed of arpeggio sweeps in subdivisions (0.0625 = 64th, 0.125 = 32nd).
    melody_style:
        "stepwise", "arpeggio", "jumping" — melody movement style.
    """

    name: str = "Chiptune Generator"
    variant: str = "nes_classic"
    channels: list[str] = field(default_factory=lambda: ["pulse1", "pulse2", "triangle", "noise"])
    duty_cycle: str = "50%"
    arpeggio_speed: float = 0.125
    melody_style: str = "stepwise"
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "nes_classic",
        channels: list[str] | None = None,
        duty_cycle: str = "50%",
        arpeggio_speed: float = 0.125,
        melody_style: str = "stepwise",
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.channels = (
            channels if channels is not None else ["pulse1", "pulse2", "triangle", "noise"]
        )
        self.duty_cycle = duty_cycle
        self.arpeggio_speed = max(0.0625, min(0.25, arpeggio_speed))
        self.melody_style = melody_style

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

            if "pulse1" in self.channels:
                self._render_pulse1(notes, bar_start, duration_beats, chord, key)
            if "pulse2" in self.channels:
                self._render_pulse2(notes, bar_start, duration_beats, chord)
            if "triangle" in self.channels:
                self._render_triangle(notes, bar_start, duration_beats, chord)
            if "noise" in self.channels:
                self._render_noise(notes, bar_start, duration_beats)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_pulse1(self, notes, bar_start, total, chord, key):
        """Lead melody channel."""
        mid = 72
        scale_pcs = [int(d) for d in key.degrees()]

        if self.melody_style == "arpeggio":
            # Arpeggio sweep
            pcs = chord.pitch_classes()[:4]
            t = bar_start
            idx = 0
            while t < min(bar_start + 4.0, total):
                pc = pcs[idx % len(pcs)]
                pitch = nearest_pitch(pc, mid)
                notes.append(
                    NoteInfo(
                        pitch=max(48, min(96, pitch)),
                        start=round(t, 6),
                        duration=self.arpeggio_speed * 0.8,
                        velocity=85,
                    )
                )
                t += self.arpeggio_speed
                idx += 1
        elif self.melody_style == "jumping":
            # Wide interval jumps (classic NES)
            t = bar_start
            prev = mid
            while t < min(bar_start + 4.0, total):
                if random.random() < 0.7:
                    pc = random.choice(scale_pcs)
                    pitch = nearest_pitch(pc, prev)
                    # Jump by octave sometimes
                    if random.random() < 0.3:
                        pitch += random.choice([-12, 12])
                    pitch = max(48, min(96, pitch))
                    dur = random.choice([0.25, 0.5])
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(t, 6), duration=dur * 0.8, velocity=85)
                    )
                    prev = pitch
                t += 0.25
        else:
            # Stepwise melody
            t = bar_start
            prev = mid
            while t < min(bar_start + 4.0, total):
                if random.random() < 0.7:
                    pc = random.choice(scale_pcs)
                    pitch = nearest_pitch(pc, prev)
                    pitch = max(48, min(96, pitch))
                    dur = random.choice([0.25, 0.5, 0.5])
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(t, 6), duration=dur * 0.8, velocity=80)
                    )
                    prev = pitch
                t += 0.5

    def _render_pulse2(self, notes, bar_start, total, chord):
        """Harmony/counter channel — fills gaps in pulse1."""
        mid = 66
        pcs = chord.pitch_classes()[:3]
        t = bar_start + 0.25  # Offset from pulse1
        prev = mid
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.5:
                pc = random.choice(pcs)
                pitch = nearest_pitch(pc, prev)
                notes.append(
                    NoteInfo(
                        pitch=max(48, min(84, pitch)), start=round(t, 6), duration=0.4, velocity=65
                    )
                )
                prev = pitch
            t += 0.5

    def _render_triangle(self, notes, bar_start, total, chord):
        """Triangle wave bass — NES triangle channel."""
        low = max(24, self.params.key_range_low)
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        fifth = nearest_pitch((chord.root + 7) % 12, pitch)
        if self.variant == "gameboy":
            # Game Boy: simpler bass
            for beat in range(4):
                onset = bar_start + beat
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.4, velocity=80)
                    )
        else:
            # NES: root-fifth pattern
            seq = [pitch, pitch, fifth, pitch, pitch, fifth, pitch, fifth]
            t = bar_start
            idx = 0
            while t < min(bar_start + 4.0, total):
                notes.append(
                    NoteInfo(
                        pitch=seq[idx % len(seq)], start=round(t, 6), duration=0.4, velocity=80
                    )
                )
                t += 0.5
                idx += 1

    def _render_noise(self, notes, bar_start, total):
        """Noise channel drums."""
        if self.variant == "gameboy":
            # Game Boy: sparse
            if bar_start < total:
                notes.append(
                    NoteInfo(
                        pitch=NOISE_KICK, start=round(bar_start, 6), duration=0.15, velocity=90
                    )
                )
            if bar_start + 2 < total:
                notes.append(
                    NoteInfo(
                        pitch=NOISE_SNARE, start=round(bar_start + 2, 6), duration=0.15, velocity=90
                    )
                )
        else:
            # NES: classic pattern
            for beat in range(4):
                onset = bar_start + beat
                if onset >= total:
                    break
                if beat in (0, 2):
                    notes.append(
                        NoteInfo(
                            pitch=NOISE_KICK, start=round(onset, 6), duration=0.15, velocity=95
                        )
                    )
                else:
                    notes.append(
                        NoteInfo(
                            pitch=NOISE_SNARE, start=round(onset, 6), duration=0.15, velocity=90
                        )
                    )
            # Offbeat hats
            for i in range(4):
                onset = bar_start + i + 0.5
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=NOISE_HAT, start=round(onset, 6), duration=0.08, velocity=50)
                    )
