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
