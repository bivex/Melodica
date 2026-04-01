"""
rc_variations.py — Re-export hub.
"""

from __future__ import annotations

from melodica.modifiers.rc_variations_chord import (
    AddChordNotesModifier,
    SpreadOutChordNotesModifier,
    SwapChordNotesModifier,
    PermuteChordNotesModifier,
    FillGapsModifier,
    RemoveDuplicatesModifier,
    AudioGainModifier,
    VelocityGeneratorModifier,
    SimplifyPhraseModifier,
)
from melodica.modifiers.rc_variations_structural import (
    AddIntervalModifier,
    DelayNotesModifier,
    DoublePhraseModifier,
    TriplePhraseModifier,
    ExtractRhythmModifier,
    JoinNotesModifier,
    RemoveShortNotesModifier,
    RotateNotesModifier,
)

__all__ = [
    "AddChordNotesModifier",
    "SpreadOutChordNotesModifier",
    "SwapChordNotesModifier",
    "PermuteChordNotesModifier",
    "FillGapsModifier",
    "RemoveDuplicatesModifier",
    "AudioGainModifier",
    "VelocityGeneratorModifier",
    "SimplifyPhraseModifier",
    "AddIntervalModifier",
    "DelayNotesModifier",
    "DoublePhraseModifier",
    "TriplePhraseModifier",
    "ExtractRhythmModifier",
    "JoinNotesModifier",
    "RemoveShortNotesModifier",
    "RotateNotesModifier",
]
