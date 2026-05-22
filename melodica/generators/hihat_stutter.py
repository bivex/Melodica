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
from melodica.utils import chord_at, snap_to_scale


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
    pan_mode: str = "alternate"
    scale_snap_rolls: bool = True
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
        pan_mode: str = "alternate",
        scale_snap_rolls: bool = True,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.roll_density = max(0.0, min(1.0, roll_density))
        self.open_hat_probability = max(0.0, min(1.0, open_hat_probability))
        self.velocity_accent = velocity_accent
        self.pitch_variation = pitch_variation
        self.stutter_lengths = stutter_lengths if stutter_lengths is not None else [3, 5, 7]
        self.instrument = instrument
        self.pan_mode = pan_mode
        self.scale_snap_rolls = scale_snap_rolls

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
                self._render_trap_eighth(notes, bar_start, duration_beats, base_pitch, key)
            elif self.pattern == "trap_triplet":
                self._render_trap_triplet(notes, bar_start, duration_beats, base_pitch, key)
            elif self.pattern == "drill_stutter":
                self._render_drill_stutter(notes, bar_start, duration_beats, base_pitch, key)
            elif self.pattern == "rapid_fire":
                self._render_rapid_fire(notes, bar_start, duration_beats, base_pitch, key)
            elif self.pattern == "sparse":
                self._render_sparse(notes, bar_start, duration_beats, base_pitch, key)
            elif self.pattern == "velocity_wave":
                self._render_velocity_wave(notes, bar_start, duration_beats, base_pitch, key)
            else:
                self._render_trap_eighth(notes, bar_start, duration_beats, base_pitch, key)
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
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int, key: Scale | None = None
    ) -> None:
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break

            # Stutter roll insertion
            if random.random() < self.roll_density and i < 7:
                roll_len = random.choice(self.stutter_lengths)
                roll_dur = 0.5 / roll_len
                
                # Determine sweep offsets
                if self.pitch_variation and random.random() < 0.6:
                    start_offset = random.choice([-5, -4, -3, -2, 2, 3, 4, 5, 7])
                    end_offset = random.choice([-7, -5, -3, 0, 2, 5, 7])
                else:
                    start_offset = 0
                    end_offset = 0
                
                for r in range(roll_len):
                    roll_onset = onset + r * roll_dur
                    if roll_onset >= total:
                        break
                    
                    vel = self._roll_velocity(r, roll_len)
                    
                    # Pitch sweep with scale snapping
                    if roll_len > 1:
                        interp = r / (roll_len - 1)
                    else:
                        interp = 1.0
                    pitch_offset = int(start_offset + (end_offset - start_offset) * interp)
                    raw_pitch = pitch + pitch_offset
                    if self.scale_snap_rolls and key is not None:
                        pitch_use = snap_to_scale(raw_pitch, key)
                    else:
                        pitch_use = raw_pitch
                        if self.pitch_variation and random.random() < 0.15:
                            pitch_use += random.choice([-1, 0, 1])
                    pitch_use = max(41, pitch_use)
                    
                    note = NoteInfo(
                        pitch=max(0, min(127, pitch_use)),
                        start=round(roll_onset, 6),
                        duration=roll_dur * 0.7,
                        velocity=max(1, min(127, vel)),
                    )
                    
                    # Apply pan mode
                    if self.pan_mode == "alternate":
                        pan_val = 32 if r % 2 == 0 else 96
                    elif self.pan_mode == "sweep_lr":
                        pan_val = int(16 + interp * 96)
                    elif self.pan_mode == "sweep_rl":
                        pan_val = int(112 - interp * 96)
                    else: # "mono"
                        pan_val = 64
                    
                    note.expression[10] = max(0, min(127, pan_val + random.randint(-8, 8)))
                    notes.append(note)
                continue

            is_open = random.random() < self.open_hat_probability
            hat_pitch = HH_OPEN if is_open else pitch
            vel = self._accent_velocity(i, 8)

            note = NoteInfo(
                pitch=hat_pitch,
                start=round(onset, 6),
                duration=0.3 if is_open else 0.15,
                velocity=vel,
            )
            # Add subtle panning to normal hits
            note.expression[10] = random.randint(54, 74)
            notes.append(note)

    def _render_trap_triplet(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int, key: Scale | None = None
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
                note = NoteInfo(
                    pitch=pitch_use,
                    start=round(onset, 6),
                    duration=triplet_dur * 0.7,
                    velocity=vel,
                )
                note.expression[10] = random.randint(58, 70)
                notes.append(note)

    def _render_drill_stutter(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int, key: Scale | None = None
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
                
                # Determine sweep offsets
                if self.pitch_variation and random.random() < 0.6:
                    start_offset = random.choice([-5, -4, -3, -2, 2, 3, 4, 5, 7])
                    end_offset = random.choice([-7, -5, -3, 0, 2, 5, 7])
                else:
                    start_offset = 0
                    end_offset = 0
                
                for r in range(burst_len):
                    burst_onset = onset - 0.25 + r * burst_dur
                    if burst_onset < bar_start or burst_onset >= total:
                        continue
                    
                    vel = int(50 + (r / burst_len) * 40)
                    
                    # Pitch sweep with scale snapping
                    if burst_len > 1:
                        interp = r / (burst_len - 1)
                    else:
                        interp = 1.0
                    pitch_offset = int(start_offset + (end_offset - start_offset) * interp)
                    raw_pitch = pitch + pitch_offset
                    if self.scale_snap_rolls and key is not None:
                        pitch_use = snap_to_scale(raw_pitch, key)
                    else:
                        pitch_use = raw_pitch
                    pitch_use = max(41, pitch_use)
                    
                    note = NoteInfo(
                        pitch=max(0, min(127, pitch_use)),
                        start=round(burst_onset, 6),
                        duration=burst_dur * 0.6,
                        velocity=max(1, min(127, vel)),
                    )
                    
                    # Apply pan mode
                    if self.pan_mode == "alternate":
                        pan_val = 32 if r % 2 == 0 else 96
                    elif self.pan_mode == "sweep_lr":
                        pan_val = int(16 + interp * 96)
                    elif self.pan_mode == "sweep_rl":
                        pan_val = int(112 - interp * 96)
                    else: # "mono"
                        pan_val = 64
                    
                    note.expression[10] = max(0, min(127, pan_val + random.randint(-8, 8)))
                    notes.append(note)
                continue

            vel = self._accent_velocity(i, 8)
            note = NoteInfo(
                pitch=pitch,
                start=round(onset, 6),
                duration=0.15,
                velocity=vel,
            )
            note.expression[10] = random.randint(58, 70)
            notes.append(note)

    def _render_rapid_fire(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int, key: Scale | None = None
    ) -> None:
        sub = 0.125  # 32nd notes
        i = 0
        t = bar_start
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.85:
                vel = 60 + random.randint(-10, 10)
                pitch_use = self._vary_pitch(pitch, t - bar_start)
                note = NoteInfo(
                    pitch=pitch_use,
                    start=round(t, 6),
                    duration=sub * 0.6,
                    velocity=max(1, min(MIDI_MAX, vel)),
                )
                note.expression[10] = random.randint(48, 80)
                notes.append(note)
            t += sub
            i += 1

    def _render_sparse(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int, key: Scale | None = None
    ) -> None:
        # Sparse: open hats on beats, closed on offbeats
        for beat in range(4):
            onset = bar_start + beat
            if onset >= total:
                break
            note_o = NoteInfo(
                pitch=HH_OPEN,
                start=round(onset, 6),
                duration=0.8,
                velocity=75,
            )
            note_o.expression[10] = random.randint(50, 78)
            notes.append(note_o)
            
            if random.random() < 0.5:
                off_onset = onset + 0.5
                if off_onset < total:
                    note_c = NoteInfo(
                        pitch=HH_CLOSED,
                        start=round(off_onset, 6),
                        duration=0.15,
                        velocity=55,
                    )
                    note_c.expression[10] = random.randint(54, 74)
                    notes.append(note_c)

    def _render_velocity_wave(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int, key: Scale | None = None
    ) -> None:
        import math

        for i in range(16):
            onset = bar_start + i * 0.25
            if onset >= total:
                break
            # Sine wave velocity: soft-loud-soft-loud
            wave = math.sin(i * math.pi / 4)
            vel = int(60 + wave * 30)
            note = NoteInfo(
                pitch=pitch,
                start=round(onset, 6),
                duration=0.1,
                velocity=max(30, min(MIDI_MAX, vel)),
            )
            note.expression[10] = random.randint(56, 72)
            notes.append(note)

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
