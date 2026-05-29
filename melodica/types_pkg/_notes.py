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

"""Primitive note value objects."""

from __future__ import annotations


import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, List

from melodica.theory import Mode, Quality, CHORD_TEMPLATES, MODE_DATABASE, get_mode_intervals

OCTAVE: int = 12


@dataclass(frozen=True)
class Note:
    """A single MIDI note. Immutable value object."""

    pitch: int  # MIDI pitch 0–127
    start: float  # beat position (quarter notes)
    duration: float  # length in beats
    velocity: int = 64
    channel: int = 0

    def __post_init__(self) -> None:
        if not (0 <= self.pitch <= 127):
            raise ValueError(f"pitch must be 0–127, got {self.pitch}")
        if self.duration <= 0:
            raise ValueError(f"duration must be > 0, got {self.duration}")
        if not (0 <= self.velocity <= 127):
            raise ValueError(f"velocity must be 0–127, got {self.velocity}")

    @property
    def pitch_class(self) -> int:
        return self.pitch % OCTAVE

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass(slots=True)
class NoteInfo:
    """Note with absolute/relative transposition flag (mirrors noteinfo in feDP blocks)."""

    pitch: int
    start: float
    duration: float
    velocity: int = 64
    absolute: bool = False
    articulation: str | None = None  # 'sustain', 'staccato', 'pizzicato', etc.
    expression: dict[int | str, int | list[tuple[float, int]]] = field(default_factory=dict)  # CC data: {cc_num: value} or {"pitch_bend": val/[(t, val)]}

    def __post_init__(self) -> None:
        if not (0 <= self.pitch <= 127):
            raise ValueError(f"pitch must be 0–127, got {self.pitch}")
        if self.duration <= 0:
            raise ValueError(f"duration must be > 0, got {self.duration}")
        if not (0 <= self.velocity <= 127):
            raise ValueError(f"velocity must be 0–127, got {self.velocity}")

    def shift_time(self, offset: float) -> NoteInfo:
        self.start += offset
        return self

    def transpose(self, semitones: int) -> NoteInfo:
        self.pitch = max(0, min(127, self.pitch + semitones))
        return self

    def scale_velocity(self, factor: float) -> NoteInfo:
        self.velocity = max(0, min(127, int(self.velocity * factor)))
        return self

    def time_stretch(self, multiplier: float) -> NoteInfo:
        self.start *= multiplier
        self.duration *= multiplier
        return self

    def morph_scale(self, from_scale: Scale, to_scale: Scale, strategy: str = "degree") -> NoteInfo:
        """
        Morphs the note's pitch from from_scale to to_scale.
        
        Strategies:
        - "degree": Maps the scale degree index directly if possible (preserves intervals).
        - "nearest": Maps to the closest pitch class in to_scale (preserves pitch proximity).
        """
        if self.absolute:
            return self

        octave = self.pitch // 12
        pc = self.pitch % 12

        from_degs = from_scale.degrees()
        to_degs = to_scale.degrees()

        if strategy == "degree":
            # Find closest degree index in from_scale
            best_idx = 0
            best_diff = 999.0
            for i, d in enumerate(from_degs):
                diff = abs(pc - d)
                if diff < best_diff:
                    best_diff = diff
                    best_idx = i

            # Map index to target scale
            if len(from_degs) == len(to_degs):
                target_idx = best_idx
            else:
                target_idx = round(best_idx * (len(to_degs) - 1) / (len(from_degs) - 1))

            target_pc = to_degs[target_idx]
            new_pitch = int(octave * 12 + target_pc)
            self.pitch = max(0, min(127, new_pitch))
        else:
            # "nearest" strategy
            best_pc = to_degs[0]
            best_diff = 999.0
            for d in to_degs:
                diff = min(abs(pc - d), 12 - abs(pc - d))
                if diff < best_diff:
                    best_diff = diff
                    best_pc = d
            new_pitch = int(octave * 12 + best_pc)
            self.pitch = max(0, min(127, new_pitch))

        return self

    def humanize(self, timing_std_beats: float = 0.01, velocity_std: float = 3.0) -> NoteInfo:
        """Slightly randomize timing and velocity for a realistic acoustic feel."""
        import random
        if timing_std_beats > 0:
            self.start = max(0.0, self.start + random.normalvariate(0, timing_std_beats))
        if velocity_std > 0:
            self.velocity = max(1, min(127, int(self.velocity + random.normalvariate(0, velocity_std))))
        return self

    def swing(self, factor: float = 0.1, grid: float = 0.25) -> NoteInfo:
        """
        Apply swing timing to notes on offbeats.
        
        factor: amount of swing delay (e.g. 0.1 beats)
        grid: resolution grid (default 0.25 is 16th note swing)
        """
        position_in_grid = self.start / grid
        if abs(round(position_in_grid) - position_in_grid) < 0.05:
            if round(position_in_grid) % 2 != 0:
                self.start += factor * grid
        return self


