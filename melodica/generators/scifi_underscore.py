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
generators/scifi_underscore.py — Sci-fi game underscore generator.

Layer: Application / Domain
Style: Sci-fi games, space, cyberpunk, Blade Runner.

Generates sci-fi underscore:
  - Analog synth pads (Vangelis/Blade Runner style)
  - Sequenced arpeggios
  - Space drones
  - Pulsing bass synths

Variants:
    "blade_runner" — dark, noir, Vangelis-inspired
    "space"        — open space, cosmic
    "cyberpunk"    — aggressive, digital
    "retro_sci_fi" — 80s sci-fi (John Carpenter)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


@dataclass
class SciFiUnderscoreGenerator(PhraseGenerator):
    """Sci-fi game underscore generator. variant: blade_runner, space, cyberpunk, retro_sci_fi."""

    name: str = "Sci-Fi Underscore Generator"
    variant: str = "blade_runner"
    pad_density: float = 0.6
    arp_speed: float = 0.25
    include_bass_synth: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "blade_runner",
        pad_density: float = 0.6,
        arp_speed: float = 0.25,
        include_bass_synth: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.pad_density = max(0.0, min(1.0, pad_density))
        self.arp_speed = max(0.0625, min(0.5, arp_speed))
        self.include_bass_synth = include_bass_synth

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
            self._render_pad(notes, bar_start, duration_beats, chord, key)
            self._render_arp(notes, bar_start, duration_beats, chord, key)
            if self.include_bass_synth:
                self._render_bass(notes, bar_start, duration_beats, chord, low, key)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_pad(self, notes, bar_start, total, chord, key):
        mid = 54
        pcs = chord.pitch_classes()
        # Add 9th for sci-fi color
        ninth = (chord.root + 14) % 12
        pcs = list(set(list(pcs[:3]) + [ninth]))
        vel = 40 if self.variant == "blade_runner" else 45 if self.variant == "space" else 55
        if bar_start < total:
            for pc in pcs:
                pitch = snap_to_scale(nearest_pitch(pc, mid), key)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=vel)
                )

    def _render_arp(self, notes, bar_start, total, chord, key):
        mid = 72
        if self.variant == "cyberpunk":
            # Aggressive sequenced arp
            pcs = chord.pitch_classes()[:4]
            t = bar_start
            idx = 0
            while t < min(bar_start + 4.0, total):
                pc = pcs[idx % len(pcs)]
                pitch = snap_to_scale(max(48, min(84, nearest_pitch(pc, mid))), key)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=self.arp_speed * 0.7,
                        velocity=75,
                    )
                )
                t += self.arp_speed
                idx += 1
        elif self.variant == "retro_sci_fi":
            # Carpenter-style: simple up-down
            root = snap_to_scale(nearest_pitch(chord.root, mid), key)
            fifth = snap_to_scale(nearest_pitch((chord.root + 7) % 12, root), key)
            seq = [root, fifth, root + 12, fifth]
            t = bar_start
            idx = 0
            while t < min(bar_start + 4.0, total):
                notes.append(
                    NoteInfo(
                        pitch=seq[idx % len(seq)],
                        start=round(t, 6),
                        duration=self.arp_speed * 0.8,
                        velocity=65,
                    )
                )
                t += self.arp_speed
                idx += 1
        else:
            # Slow, atmospheric
            t = bar_start
            while t < min(bar_start + 4.0, total):
                if random.random() < self.pad_density:
                    pc = random.choice(chord.pitch_classes())
                    pitch = snap_to_scale(max(48, min(84, nearest_pitch(pc, mid))), key)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=1.0,
                            velocity=45,
                        )
                    )
                t += 1.0

    def _render_bass(self, notes, bar_start, total, chord, low, key):
        pitch = snap_to_scale(max(low, min(low + 12, nearest_pitch(chord.root, low + 6))), key)
        if self.variant == "cyberpunk":
            for beat in range(4):
                onset = bar_start + beat
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.6, velocity=85)
                    )
        else:
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.5, velocity=65)
                )
