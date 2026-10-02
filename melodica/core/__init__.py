# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.core — Core domain entities and value objects.

Defines immutable, framework-independent musical representations:
- NoteInfo: Pitch, onset, duration, velocity, articulation, and expression.
- ChordLabel: Harmonic chord descriptors, quality, and roots.
- Scale: Musical mode, root key, and degree structures.
- Intervals, pitch classes, and basic domain constants.
"""

from __future__ import annotations

from melodica.types import (
    C0,
    C4,
    MIDI_MAX,
    MIDI_MIN,
    OCTAVE,
    ChordLabel,
    Key,
    Mode,
    NoteInfo,
    Phrase,
    Pitch,
    Scale,
    TimeSig,
    Velocity,
)

__all__ = [
    "NoteInfo",
    "ChordLabel",
    "Scale",
    "Mode",
    "Key",
    "Phrase",
    "Pitch",
    "Velocity",
    "TimeSig",
    "OCTAVE",
    "MIDI_MIN",
    "MIDI_MAX",
    "C0",
    "C4",
]
