"""Temporal structure / labels."""

from __future__ import annotations


import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, List

from melodica.theory import Mode, Quality, CHORD_TEMPLATES, MODE_DATABASE, get_mode_intervals


from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale

@dataclass
class KeyLabel:
    """A scale active at a specific time."""
    scale: Scale
    start: float = 0.0
    duration: float = 0.0

@dataclass
class TimeSignatureLabel:
    numerator: int
    denominator: int
    start: float

@dataclass
class MarkerLabel:
    text: str
    start: float

@dataclass
class MusicTimeline:
    """Timeline for chords, keys, time signatures, and markers."""
    chords: list[ChordLabel] = field(default_factory=list)
    keys: list[KeyLabel] = field(default_factory=list)
    time_signatures: list[TimeSignatureLabel] = field(default_factory=list)
    markers: list[MarkerLabel] = field(default_factory=list)

    def get_key_at(self, time: float) -> Scale:
        if not self.keys:
            return Scale(root=0, mode=Mode.MAJOR)
        active = self.keys[0].scale
        for k in sorted(self.keys, key=lambda x: x.start):
            if k.start <= time:
                active = k.scale
            else:
                break
        return active
