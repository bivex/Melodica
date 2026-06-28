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


class SectionRole(StrEnum):
    """What a section IS in the arrangement structure (structural role)."""

    INTRO = "intro"
    VERSE = "verse"
    PRE_CHORUS = "pre_chorus"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    OUTRO = "outro"
    HOOK = "hook"
    REFRAIN = "refrain"
    SOLO = "solo"
    BREAKDOWN = "breakdown"
    CODA = "coda"
    INTERLUDE = "interlude"
    DROP = "drop"
    CLIMAX = "climax"
    TAG = "tag"


class SectionFunction(StrEnum):
    """What a section DOES in the arrangement (functional behavior)."""

    BUILD = "build"
    RELEASE = "release"
    SUSTAIN = "sustain"
    BREAK = "break"
    FADE = "fade"
    HOLD = "hold"


# Backward compat alias
SectionType = SectionRole


# Default energy baselines by role (can be overridden by function/context)
SECTION_ROLE_ENERGY: dict[SectionRole, float] = {
    SectionRole.INTRO: 0.3,
    SectionRole.VERSE: 0.5,
    SectionRole.PRE_CHORUS: 0.65,
    SectionRole.CHORUS: 0.85,
    SectionRole.BRIDGE: 0.6,
    SectionRole.OUTRO: 0.35,
    SectionRole.HOOK: 0.85,
    SectionRole.REFRAIN: 0.8,
    SectionRole.SOLO: 0.75,
    SectionRole.BREAKDOWN: 0.25,
    SectionRole.CODA: 0.4,
    SectionRole.INTERLUDE: 0.35,
    SectionRole.DROP: 1.0,
    SectionRole.CLIMAX: 0.95,
    SectionRole.TAG: 0.3,
}

# Energy modifiers applied by function (additive)
SECTION_FUNCTION_ENERGY: dict[SectionFunction, float] = {
    SectionFunction.BUILD: 0.15,
    SectionFunction.RELEASE: -0.1,
    SectionFunction.SUSTAIN: 0.0,
    SectionFunction.BREAK: -0.2,
    SectionFunction.FADE: -0.15,
    SectionFunction.HOLD: 0.0,
}

# Backward compat (copy to avoid shared mutation)
SECTION_ENERGY = dict(SECTION_ROLE_ENERGY)


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
    TempoLabel,
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
    "SectionRole",
    "SectionFunction",
    "SectionType",
    "SECTION_ROLE_ENERGY",
    "SECTION_FUNCTION_ENERGY",
    "SECTION_ENERGY",
    "Note",
    "NoteInfo",
    "HarmonicFunction",
    "Scale",
    "ChordLabel",
    "KeyLabel",
    "TimeSignatureLabel",
    "TempoLabel",
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
