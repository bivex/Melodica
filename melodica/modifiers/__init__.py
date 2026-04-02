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
modifiers/__init__.py — Phrase Modifiers / Variations.

Layer: Application / Domain

Modifiers sit between the generator (or static phrase) and the final output,
applying transformations to the list of notes (quantization, swing, doubling, etc.).
"""

from __future__ import annotations

import typing
from dataclasses import dataclass, field

from melodica.types import ChordLabel, NoteInfo, Scale

if typing.TYPE_CHECKING:
    from melodica.types import MusicTimeline


@dataclass(frozen=True)
class ModifierContext:
    """Context required by some modifiers (like harmonic adaptations or bound checks)."""

    duration_beats: float
    chords: list[ChordLabel]
    timeline: "MusicTimeline"
    scale: Scale
    tracks: dict[str, list[NoteInfo]] = field(default_factory=dict)


class PhraseModifier(typing.Protocol):
    """
    Protocol for all phrase modifiers / variations.
    Takes a list of generated notes and returns a transformed list.
    """

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]: ...


from melodica.modifiers.rhythmic import (
    QuantizeModifier,
    FollowRhythmModifier,
    HumanizeModifier,
    SwingController,
    AdjustNoteLengthsModifier,
)

from melodica.modifiers.harmonic import (
    NoteDoublerModifier,
    TransposeModifier,
    LimitNoteRangeModifier,
)

from melodica.modifiers.dynamic import (
    VelocityScalingModifier,
    CrescendoModifier,
    SectionIntensityModifier,
)

from melodica.modifiers.voice_leading import VoiceLeadingModifier

from melodica.modifiers.aesthetic import GrooveModifier, PolishedOctaveModifier

from melodica.modifiers.variations import (
    MirrorModifier,
    StaccatoLegatoModifier,
    AccentModifier,
    ReRhythmizeModifier,
    MonophonicModifier,
    MIDIEchoModifier,
    ArpeggiateModifier,
)

from melodica.modifiers.voicings import (
    DropVoicingModifier,
    TopNoteVoicingModifier,
    InversionModifier,
)

from melodica.modifiers.rc_variations import (
    AddChordNotesModifier,
    AddIntervalModifier,
    DelayNotesModifier,
    DoublePhraseModifier,
    TriplePhraseModifier,
    ExtractRhythmModifier,
    JoinNotesModifier,
    RemoveShortNotesModifier,
    RotateNotesModifier,
    SimplifyPhraseModifier,
    SpreadOutChordNotesModifier,
    SwapChordNotesModifier,
    VelocityGeneratorModifier,
    PermuteChordNotesModifier,
    AudioGainModifier,
    RemoveDuplicatesModifier,
    FillGapsModifier,
)

__all__ = [
    "PhraseModifier",
    "ModifierContext",
    "QuantizeModifier",
    "FollowRhythmModifier",
    "HumanizeModifier",
    "SwingController",
    "AdjustNoteLengthsModifier",
    "NoteDoublerModifier",
    "TransposeModifier",
    "LimitNoteRangeModifier",
    "VelocityScalingModifier",
    "CrescendoModifier",
    "SectionIntensityModifier",
    "VoiceLeadingModifier",
    "GrooveModifier",
    "PolishedOctaveModifier",
    "MirrorModifier",
    "StaccatoLegatoModifier",
    "AccentModifier",
    "ReRhythmizeModifier",
    "MonophonicModifier",
    "MIDIEchoModifier",
    "ArpeggiateModifier",
    "DropVoicingModifier",
    "TopNoteVoicingModifier",
    "InversionModifier",
    "AddChordNotesModifier",
    "AddIntervalModifier",
    "DelayNotesModifier",
    "DoublePhraseModifier",
    "TriplePhraseModifier",
    "ExtractRhythmModifier",
    "JoinNotesModifier",
    "RemoveShortNotesModifier",
    "RotateNotesModifier",
    "SimplifyPhraseModifier",
    "SpreadOutChordNotesModifier",
    "SwapChordNotesModifier",
    "VelocityGeneratorModifier",
    "PermuteChordNotesModifier",
    "AudioGainModifier",
    "RemoveDuplicatesModifier",
    "FillGapsModifier",
]
