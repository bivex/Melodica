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


@dataclass
class NoteInfo:
    """Note with absolute/relative transposition flag (mirrors noteinfo in feDP blocks)."""

    pitch: int
    start: float
    duration: float
    velocity: int = 64
    absolute: bool = False
    articulation: str | None = None  # 'sustain', 'staccato', 'pizzicato', etc.
    expression: dict[int, int] = field(default_factory=dict)  # CC controller data {cc_num: value}

    def __post_init__(self) -> None:
        if not (0 <= self.pitch <= 127):
            raise ValueError(f"pitch must be 0–127, got {self.pitch}")
        if self.duration <= 0:
            raise ValueError(f"duration must be > 0, got {self.duration}")
