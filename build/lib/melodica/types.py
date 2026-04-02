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
types.py -- Core domain types (re-export hub).
"""

from __future__ import annotations

# Constants
OCTAVE: int = 12
MIDI_MAX: int = 127
TICKS_PER_BEAT: int = 480
VELOCITY_DEFAULT: int = 64
VELOCITY_MAX: int = 127

from melodica.types_pkg._notes import (
    Note,
    NoteInfo,
)

from melodica.types_pkg._theory import (
    HarmonicFunction,
    Scale,
    ChordLabel,
)

from melodica.types_pkg._timeline import (
    KeyLabel,
    TimeSignatureLabel,
    MarkerLabel,
    MusicTimeline,
)

from melodica.types_pkg._phrases import (
    StaticPhrase,
    HarmonizationRequest,
    PhraseGeneratorProtocol,
    PhraseInstance,
    ArrangementSlot,
    IdeaTrack,
    Track,
    Arrangement,
)

from melodica.types_pkg._theory import parse_progression

# Re-export theory types that were historically in types.py
from melodica.theory import Mode, Quality, CHORD_TEMPLATES

__all__ = [
    "OCTAVE",
    "MIDI_MAX",
    "TICKS_PER_BEAT",
    "VELOCITY_DEFAULT",
    "VELOCITY_MAX",
    "Note",
    "NoteInfo",
    "HarmonicFunction",
    "Scale",
    "ChordLabel",
    "KeyLabel",
    "TimeSignatureLabel",
    "MarkerLabel",
    "MusicTimeline",
    "StaticPhrase",
    "HarmonizationRequest",
    "PhraseGeneratorProtocol",
    "PhraseInstance",
    "ArrangementSlot",
    "IdeaTrack",
    "Track",
    "Arrangement",
    "parse_progression",
]
