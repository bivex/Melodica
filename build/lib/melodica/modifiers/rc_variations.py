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
