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

from enum import StrEnum

# Constants
OCTAVE: int = 12
MIDI_MAX: int = 127
TICKS_PER_BEAT: int = 480
VELOCITY_DEFAULT: int = 64
VELOCITY_MAX: int = 127


class SectionType(StrEnum):
    """Unified section type vocabulary for arrangement structure."""

    INTRO = "intro"
    VERSE = "verse"
    PRE_CHORUS = "pre_chorus"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    OUTRO = "outro"
    BUILD = "build"
    DROP = "drop"
    BREAK = "break"
    FINAL = "final"


SECTION_ENERGY: dict[SectionType, float] = {
    SectionType.INTRO: 0.3,
    SectionType.VERSE: 0.5,
    SectionType.PRE_CHORUS: 0.65,
    SectionType.CHORUS: 0.85,
    SectionType.BRIDGE: 0.6,
    SectionType.OUTRO: 0.35,
    SectionType.BUILD: 0.7,
    SectionType.DROP: 1.0,
    SectionType.BREAK: 0.2,
    SectionType.FINAL: 0.9,
}


from melodica.types_pkg._notes import (
    Note,
    NoteInfo,
)

from melodica.types_pkg._theory import (
    HarmonicFunction,
    Scale,
    ChordLabel,
    RomanNumeral,
    parse_progression_structured,
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

from melodica.types_pkg._scenes import (
    TransitionType,
    SceneTransition,
    Scene,
    SceneGraph,
)

from melodica.types_pkg._bargrid import BarGrid

from melodica.types_pkg._theory import parse_progression
from melodica.theory.modulation import ModulationEngine

# Re-export theory types that were historically in types.py
from melodica.theory import Mode, Quality, CHORD_TEMPLATES

__all__ = [
    "OCTAVE",
    "MIDI_MAX",
    "TICKS_PER_BEAT",
    "VELOCITY_DEFAULT",
    "VELOCITY_MAX",
    "SectionType",
    "SECTION_ENERGY",
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
    "RomanNumeral",
    "parse_progression_structured",
    "ModulationEngine",
    "TransitionType",
    "SceneTransition",
    "Scene",
    "SceneGraph",
    "BarGrid",
]
