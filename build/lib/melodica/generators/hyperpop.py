"""
generators/hyperpop.py — Hyperpop / Glitch pattern generator.

Layer: Application / Domain
Style: Hyperpop, glitch pop, PC Music, deconstructed club.

Generates characteristic hyperpop elements:
  - Pitch-shifted vocal chops
  - Bitcrushed textures
  - Chaotic arrangements with sudden changes
  - Distorted bass
  - Rapid-fire drum fills

Variants:
    "standard"    — standard hyperpop
    "glitch"      — glitch-heavy with random artifacts
    "bubblegum"   — bubblegum bass / cute hyperpop
    "deconstructed" — deconstructed club (abstract, chaotic)
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
CLAP = 39


@dataclass
class HyperpopGenerator(PhraseGenerator):
    """
    Hyperpop / Glitch pattern generator.

    variant:
        "standard", "glitch", "bubblegum", "deconstructed"
    pitch_shift_range:
        Range of pitch shifting for vocal chops in semitones (1-24).
    glitch_density:
        Density of glitch artifacts (0.0-1.0).
    distortion_amount:
        Amount of simulated distortion (0.0-1.0).
    chaos_factor:
        How chaotic/unpredictable the arrangement is (0.0-1.0).
    include_leads:
        Whether to include hyperpop lead synth melody.
    """

    name: str = "Hyperpop Generator"
    variant: str = "standard"
    pitch_shift_range: int = 12
    glitch_density: float = 0.4
    distortion_amount: float = 0.5
    chaos_factor: float = 0.3
    include_leads: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "standard",
        pitch_shift_range: int = 12,
        glitch_density: float = 0.4,
        distortion_amount: float = 0.5,
        chaos_factor: float = 0.3,
        include_leads: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.pitch_shift_range = max(1, min(24, pitch_shift_range))
        self.glitch_density = max(0.0, min(1.0, glitch_density))
        self.distortion_amount = max(0.0, min(1.0, distortion_amount))
        self.chaos_factor = max(0.0, min(1.0, chaos_factor))
        self.include_leads = include_leads

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

            # Drums (fast, chaotic)
            self._render_drums(notes, bar_start, duration_beats)

            # Bass
            self._render_bass(notes, bar_start, duration_beats, chord)

            # Vocal chops
            self._render_vocal_chops(notes, bar_start, duration_beats, chord)

            # Lead
            if self.include_leads:
                self._render_lead(notes, bar_start, duration_beats, chord, key)

            # Glitch artifacts
            self._render_glitch(notes, bar_start, duration_beats)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_drums(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        # Fast, dense drums
        for i in range(16):
            onset = bar_start + i * 0.25
            if onset >= total:
                break

            # Kick on 1, 5, 9, 13 (four on floor) or chaotic
            if self.variant == "deconstructed":
                if random.random() < 0.4:
                    notes.append(
                        NoteInfo(
                            pitch=random.choice([KICK, SNARE, HH_CLOSED]),
                            start=round(onset, 6),
                            duration=0.1,
                            velocity=80 + random.randint(-20, 20),
                        )
                    )
            else:
                if i % 4 == 0:
                    notes.append(
                        NoteInfo(
                            pitch=KICK,
                            start=round(onset, 6),
                            duration=0.2,
                            velocity=110,
                        )
                    )
                if i % 8 == 4:
                    notes.append(
                        NoteInfo(
                            pitch=SNARE,
                            start=round(onset, 6),
                            duration=0.15,
                            velocity=105,
                        )
                    )
                    notes.append(
                        NoteInfo(
                            pitch=CLAP,
                            start=round(onset, 6),
                            duration=0.12,
                            velocity=90,
                        )
                    )
                # Hi-hats on every subdivision
                if random.random() < 0.8:
                    notes.append(
                        NoteInfo(
                            pitch=HH_CLOSED,
                            start=round(onset, 6),
                            duration=0.06,
                            velocity=60 + random.randint(-10, 10),
                        )
                    )

    def _render_bass(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        root_pc = chord.root
        low = max(30, self.params.key_range_low)
        pitch = max(low, nearest_pitch(root_pc, low + 6))

        if self.variant == "bubblegum":
            # Bouncy bass
            for off in [0.0, 1.0, 2.0, 3.0]:
                onset = bar_start + off
                if onset < total:
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=0.7,
                            velocity=95,
                        )
                    )
        else:
            # Sustained distorted bass
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(bar_start, 6),
                    duration=3.8,
                    velocity=int(100 * (1.0 + self.distortion_amount * 0.2)),
                )
            )

    def _render_vocal_chops(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        root_pc = chord.root
        mid = 72
        scale_pcs = [0, 2, 4, 5, 7, 9, 11]  # Major scale

        for i in range(8):
            if random.random() > 0.6:
                continue
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            # Pitch-shifted vocal chop
            offset_pc = random.choice(scale_pcs)
            pc = (root_pc + offset_pc) % 12
            pitch = nearest_pitch(
                pc, mid + random.randint(-self.pitch_shift_range // 2, self.pitch_shift_range // 2)
            )
            dur = random.choice([0.15, 0.25, 0.5])
            notes.append(
                NoteInfo(
                    pitch=max(48, min(96, pitch)),
                    start=round(onset, 6),
                    duration=dur,
                    velocity=70 + random.randint(-10, 10),
                )
            )

    def _render_lead(
        self,
        notes: list[NoteInfo],
        bar_start: float,
        total: float,
        chord: ChordLabel,
        key: Scale,
    ) -> None:
        root_pc = chord.root
        high = min(96, self.params.key_range_high)
        scale_pcs = [int(d) for d in key.degrees()]

        pos = bar_start
        prev = high
        while pos < min(bar_start + 4.0, total):
            if random.random() < 0.7:
                pc = random.choice(scale_pcs)
                pitch = nearest_pitch(pc, prev)
                pitch = max(60, min(high, pitch))
                dur = random.choice([0.25, 0.5])
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(pos, 6),
                        duration=dur,
                        velocity=75 + random.randint(-10, 10),
                    )
                )
                prev = pitch
            pos += 0.5

    def _render_glitch(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        if random.random() > self.glitch_density:
            return
        # Random glitch hits
        num_glitches = random.randint(1, 4)
        for _ in range(num_glitches):
            onset = bar_start + random.uniform(0, 4)
            if onset >= total:
                continue
            pitch = random.randint(60, 84)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=random.choice([0.03, 0.05, 0.08]),
                    velocity=random.randint(40, 80),
                )
            )
