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
generators/rage_beat.py — Rage Beat pattern generator.

Layer: Application / Domain
Style: Rage beats, aggressive rap, Playboi Carti style, Opium.

Generates characteristic rage beat elements:
  - Distorted synth lead stabs
  - Aggressive 808 patterns
  - Fast hi-hat rolls
  - Hard-hitting drums
  - Minimal but impactful arrangement

Variants:
    "carti"      — Playboi Carti / Opium style
    "destroy"    — Destroy Lonely style (darker)
    "ken"        — Ken Carson style (faster, more chaotic)
    "rage"       — Classic rage beat
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
HH_OPEN = 46
CLAP = 39


@dataclass
class RageBeatGenerator(PhraseGenerator):
    """
    Rage Beat pattern generator.

    variant:
        "carti", "destroy", "ken", "rage"
    synth_distortion:
        Amount of synth distortion (0.0-1.0).
    hat_speed:
        Hi-hat subdivision: "eighth", "sixteenth", "thirty_second".
    aggression:
        Overall aggression level (0.0-1.0).
    include_synth_lead:
        Whether to include distorted synth stabs.
    """

    name: str = "Rage Beat Generator"
    variant: str = "carti"
    synth_distortion: float = 0.8
    hat_speed: str = "sixteenth"
    aggression: float = 0.7
    include_synth_lead: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "carti",
        synth_distortion: float = 0.8,
        hat_speed: str = "sixteenth",
        aggression: float = 0.7,
        include_synth_lead: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.synth_distortion = max(0.0, min(1.0, synth_distortion))
        self.hat_speed = hat_speed
        self.aggression = max(0.0, min(1.0, aggression))
        self.include_synth_lead = include_synth_lead

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

            # 808
            self._render_808(notes, bar_start, duration_beats, chord, low)

            # Kick
            self._render_kick(notes, bar_start, duration_beats)

            # Snare
            self._render_snare(notes, bar_start, duration_beats)

            # Hi-hats
            self._render_hats(notes, bar_start, duration_beats)

            # Synth lead
            if self.include_synth_lead:
                self._render_synth(notes, bar_start, duration_beats, chord)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_808(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel, low: int
    ) -> None:
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        vel = int(100 + self.aggression * 20)
        if self.variant == "ken":
            offsets = [(0.0, 1.0), (1.0, 0.5), (2.0, 1.0), (3.0, 0.8)]
        else:
            offsets = [(0.0, 1.8), (2.0, 1.8)]
        for off, dur in offsets:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=dur,
                        velocity=min(MIDI_MAX, vel),
                    )
                )

    def _render_kick(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        for off in [0.0, 2.0]:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.25, velocity=115)
                )

    def _render_snare(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total:
                vel = int(110 + self.aggression * 15)
                notes.append(
                    NoteInfo(
                        pitch=SNARE,
                        start=round(onset, 6),
                        duration=0.2,
                        velocity=min(MIDI_MAX, vel),
                    )
                )
                notes.append(
                    NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.15, velocity=90)
                )

    def _render_hats(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        sub = {"eighth": 0.5, "sixteenth": 0.25, "thirty_second": 0.125}.get(self.hat_speed, 0.25)
        t = bar_start
        idx = 0
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.9:
                vel = 75 if idx % 4 == 0 else 55
                notes.append(
                    NoteInfo(pitch=HH_CLOSED, start=round(t, 6), duration=sub * 0.6, velocity=vel)
                )
            # Stutter roll
            if self.variant == "ken" and random.random() < 0.15:
                roll_len = random.choice([3, 5])
                roll_dur = sub / roll_len
                for r in range(roll_len):
                    r_onset = t + r * roll_dur
                    if r_onset < total:
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED,
                                start=round(r_onset, 6),
                                duration=roll_dur * 0.5,
                                velocity=50,
                            )
                        )
            t += sub
            idx += 1

    def _render_synth(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        mid = 72
        root = nearest_pitch(chord.root, mid)
        fifth = nearest_pitch((chord.root + 7) % 12, root)
        # Distorted synth stab
        for off in [0.0, 1.0, 2.0, 3.0]:
            if random.random() < 0.6:
                continue
            onset = bar_start + off
            if onset >= total:
                continue
            notes.append(NoteInfo(pitch=root, start=round(onset, 6), duration=0.5, velocity=85))
            notes.append(NoteInfo(pitch=fifth, start=round(onset, 6), duration=0.5, velocity=80))
