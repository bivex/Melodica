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
generators/hihat_stutter.py — Hi-hat stutter, triplet, and roll generator.

Layer: Application / Domain
Style: Trap, drill, hip-hop, modern rap, electronic.

Generates complex hi-hat patterns with stutter rolls, triplet subdivisions,
velocity accents, and pitch variations. Essential for modern trap/drill grooves.

Patterns:
    "trap_eighth"    — standard eighth-note hats with occasional rolls
    "trap_triplet"   — triplet-based hat pattern
    "drill_stutter"  — drill-style stutter rolls (3-5-7 note groups)
    "rapid_fire"     — continuous 32nd note rolls
    "sparse"         — minimal open-hat focused pattern
    "velocity_wave"  — hats with wave-like velocity contour
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import chord_at


HH_CLOSED = 42
HH_OPEN = 46
RIDE = 51
SHAKER = 70


@dataclass
class HiHatStutterGenerator(PhraseGenerator):
    """
    Hi-hat stutter/triplet/roll generator.

    pattern:
        "trap_eighth", "trap_triplet", "drill_stutter",
        "rapid_fire", "sparse", "velocity_wave"
    roll_density:
        Probability of inserting a stutter roll at any subdivision (0.0-1.0).
    open_hat_probability:
        Probability of open hi-hat hits (0.0-1.0).
    velocity_accent:
        Whether to apply velocity accents on downbeats.
    pitch_variation:
        Whether to vary hi-hat pitch (simulates tuning).
    stutter_lengths:
        Possible stutter roll lengths in subdivisions.
    instrument:
        "hh_closed", "ride", "shaker" — which percussion sound to use.
    """

    name: str = "Hi-Hat Stutter Generator"
    pattern: str = "trap_eighth"
    roll_density: float = 0.4
    open_hat_probability: float = 0.15
    velocity_accent: bool = True
    pitch_variation: bool = True
    stutter_lengths: list[int] = field(default_factory=lambda: [3, 5, 7])
    instrument: str = "hh_closed"
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "trap_eighth",
        roll_density: float = 0.4,
        open_hat_probability: float = 0.15,
        velocity_accent: bool = True,
        pitch_variation: bool = True,
        stutter_lengths: list[int] | None = None,
        instrument: str = "hh_closed",
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.roll_density = max(0.0, min(1.0, roll_density))
        self.open_hat_probability = max(0.0, min(1.0, open_hat_probability))
        self.velocity_accent = velocity_accent
        self.pitch_variation = pitch_variation
        self.stutter_lengths = stutter_lengths if stutter_lengths is not None else [3, 5, 7]
        self.instrument = instrument

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        last_chord = chords[-1] if chords else None
        base_pitch = self._get_base_pitch()

        bar_start = 0.0
        while bar_start < duration_beats:
            if self.pattern == "trap_eighth":
                self._render_trap_eighth(notes, bar_start, duration_beats, base_pitch)
            elif self.pattern == "trap_triplet":
                self._render_trap_triplet(notes, bar_start, duration_beats, base_pitch)
            elif self.pattern == "drill_stutter":
                self._render_drill_stutter(notes, bar_start, duration_beats, base_pitch)
            elif self.pattern == "rapid_fire":
                self._render_rapid_fire(notes, bar_start, duration_beats, base_pitch)
            elif self.pattern == "sparse":
                self._render_sparse(notes, bar_start, duration_beats, base_pitch)
            elif self.pattern == "velocity_wave":
                self._render_velocity_wave(notes, bar_start, duration_beats, base_pitch)
            else:
                self._render_trap_eighth(notes, bar_start, duration_beats, base_pitch)
            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _get_base_pitch(self) -> int:
        return {
            "hh_closed": HH_CLOSED,
            "hh_open": HH_OPEN,
            "ride": RIDE,
            "shaker": SHAKER,
        }.get(self.instrument, HH_CLOSED)

    def _render_trap_eighth(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break

            # Stutter roll insertion
            if random.random() < self.roll_density and i < 7:
                roll_len = random.choice(self.stutter_lengths)
                roll_dur = 0.5 / roll_len
                for r in range(roll_len):
                    roll_onset = onset + r * roll_dur
                    if roll_onset >= total:
                        break
                    vel = self._roll_velocity(r, roll_len)
                    pitch_use = self._vary_pitch(pitch, roll_onset - bar_start)
                    notes.append(
                        NoteInfo(
                            pitch=pitch_use,
                            start=round(roll_onset, 6),
                            duration=roll_dur * 0.7,
                            velocity=vel,
                        )
                    )
                continue

            is_open = random.random() < self.open_hat_probability
            hat_pitch = HH_OPEN if is_open else pitch
            vel = self._accent_velocity(i, 8)

            notes.append(
                NoteInfo(
                    pitch=hat_pitch,
                    start=round(onset, 6),
                    duration=0.3 if is_open else 0.15,
                    velocity=vel,
                )
            )

    def _render_trap_triplet(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        triplet_dur = 1.0 / 3.0
        for beat in range(4):
            for t in range(3):
                onset = bar_start + beat + t * triplet_dur
                if onset >= total:
                    break
                # Skip some triplets for groove
                if t > 0 and random.random() < 0.2:
                    continue
                vel = self._accent_velocity(beat * 3 + t, 12)
                pitch_use = self._vary_pitch(pitch, beat + t * triplet_dur)
                notes.append(
                    NoteInfo(
                        pitch=pitch_use,
                        start=round(onset, 6),
                        duration=triplet_dur * 0.7,
                        velocity=vel,
                    )
                )

    def _render_drill_stutter(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        # Drill: eighth notes with burst stutter rolls
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break

            # Drill stutter: bursts of 3, 5, or 7 rapid notes
            if i in (3, 5, 7) and random.random() < self.roll_density:
                burst_len = random.choice(self.stutter_lengths)
                burst_dur = 0.25 / burst_len
                for r in range(burst_len):
                    burst_onset = onset - 0.25 + r * burst_dur
                    if burst_onset < bar_start or burst_onset >= total:
                        continue
                    vel = int(50 + (r / burst_len) * 40)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(burst_onset, 6),
                            duration=burst_dur * 0.6,
                            velocity=vel,
                        )
                    )

            vel = self._accent_velocity(i, 8)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=0.15,
                    velocity=vel,
                )
            )

    def _render_rapid_fire(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        sub = 0.125  # 32nd notes
        i = 0
        t = bar_start
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.85:
                vel = 60 + random.randint(-10, 10)
                pitch_use = self._vary_pitch(pitch, t - bar_start)
                notes.append(
                    NoteInfo(
                        pitch=pitch_use,
                        start=round(t, 6),
                        duration=sub * 0.6,
                        velocity=max(1, min(MIDI_MAX, vel)),
                    )
                )
            t += sub
            i += 1

    def _render_sparse(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        # Sparse: open hats on beats, closed on offbeats
        for beat in range(4):
            onset = bar_start + beat
            if onset >= total:
                break
            notes.append(
                NoteInfo(
                    pitch=HH_OPEN,
                    start=round(onset, 6),
                    duration=0.8,
                    velocity=75,
                )
            )
            if random.random() < 0.5:
                off_onset = onset + 0.5
                if off_onset < total:
                    notes.append(
                        NoteInfo(
                            pitch=HH_CLOSED,
                            start=round(off_onset, 6),
                            duration=0.15,
                            velocity=55,
                        )
                    )

    def _render_velocity_wave(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        import math

        for i in range(16):
            onset = bar_start + i * 0.25
            if onset >= total:
                break
            # Sine wave velocity: soft-loud-soft-loud
            wave = math.sin(i * math.pi / 4)
            vel = int(60 + wave * 30)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=0.1,
                    velocity=max(30, min(MIDI_MAX, vel)),
                )
            )

    def _accent_velocity(self, position: int, total: int) -> int:
        if not self.velocity_accent:
            return 75
        if position % 2 == 0:
            return 85
        return 65

    def _roll_velocity(self, roll_index: int, roll_length: int) -> int:
        # Crescendo through the roll
        return int(45 + (roll_index / max(1, roll_length - 1)) * 40)

    def _vary_pitch(self, base: int, beat_offset: float) -> int:
        if not self.pitch_variation:
            return base
        # Small pitch variations (±1 semitone) for realistic hi-hat tuning
        if random.random() < 0.15:
            return base + random.choice([-1, 0, 1])
        return base
