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
variations.py — Re-export hub.
"""

from __future__ import annotations


import random
from dataclasses import dataclass
from melodica.types import NoteInfo
from melodica.modifiers import ModifierContext

from melodica.modifiers.variations_articulation import (
    MirrorModifier,
    StaccatoLegatoModifier,
    AccentModifier,
    ReRhythmizeModifier,
    MonophonicModifier,
    MIDIEchoModifier,
    StrumModifier,
    ArpeggiateModifier,
)
from melodica.modifiers.variations_harmonic import (
    DoublingModifier,
    AddIntervalModifier,
    AddChordNotesModifier,
    SpreadChordNotesModifier,
    VelocityGeneratorModifier,
    SlicePhraseModifier,
    RotateNotesModifier,
    RemoveShortNotesModifier,
)

__all__ = [
    "MirrorModifier",
    "StaccatoLegatoModifier",
    "AccentModifier",
    "ReRhythmizeModifier",
    "MonophonicModifier",
    "MIDIEchoModifier",
    "StrumModifier",
    "ArpeggiateModifier",
    "DoublingModifier",
    "AddIntervalModifier",
    "AddChordNotesModifier",
    "SpreadChordNotesModifier",
    "VelocityGeneratorModifier",
    "SlicePhraseModifier",
    "RotateNotesModifier",
    "RemoveShortNotesModifier",
]
