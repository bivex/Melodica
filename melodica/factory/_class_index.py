# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
factory/_class_index.py — Reverse lookup: generator CLASS -> generator_type string.

GENERATOR_REGISTRY maps str -> factory lambda, but the lambdas hide the concrete
class, so there is no built-in way to recover the canonical generator_type from a
generator INSTANCE. TrackConfig infers `generator_type` from a passed instance via
this map (see idea_tool.TrackConfig.__post_init__).

Scope is intentionally MINIMAL: it covers the core + orchestral generators that
album scripts typically instantiate directly. Generators not listed here fall
through to the default generator_type ("melody") — unchanged behavior for exotic
genre generators.
"""

from melodica.generators import (
    MelodyGenerator,
    ArpeggiatorGenerator,
    BassGenerator,
    ChordGenerator,
    PercussionGenerator,
    ViolinGenerator,
    ViolaGenerator,
    CelloGenerator,
    ContrabassGenerator,
    HarpGenerator,
    FluteGenerator,
    OboeGenerator,
    ClarinetGenerator,
    BassoonGenerator,
    TrumpetGenerator,
    TromboneGenerator,
    FrenchHornGenerator,
    TubaGenerator,
    TimpaniGenerator,
    MalletPercussionGenerator,
    OrchestralCymbalGenerator,
    ConcertBassDrumGenerator,
    TubularBellsGenerator,
    ShakerGenerator,
    WindMachineGenerator,
    DroneGenerator,
    BrassSectionGenerator,
    PianoCompGenerator,
    ChoirAahsGenerator,
    SnareDrumGenerator,
)

# Harmonic / pad / section voices that SHOULD receive voice-leading smoothing
# (mirror of the gate widening in idea_tool.py). Kept here as the single source
# of truth so the gate and the index agree.
HARMONIC_VL_TYPES = frozenset({
    "melody", "chord", "arpeggiator",
    "piano_comp", "choir_ahhs", "brass_section",
    "strings_ensemble", "woodwinds_ensemble", "organ_drawbars",
})

# Unpitched / percussion generator_types — used for MIDI channel-9 routing and to
# EXCLUDE these voices from melodic post-processing (voice-leading, non-chord
# tones). Single source of truth shared with idea_tool.PERCUSSION_TYPES.
PERCUSSION_TYPES = frozenset({
    "percussion", "drums",
    "snare_drum", "timpani", "mallet",
    "drum_kit_pattern", "electronic_drums", "trap_drums",
    "percussion_ensemble", "afro_percussion",
    "orchestral_cymbal", "concert_bass_drum", "tubular_bells",
    "tabla", "darbuka", "shaker", "wind_machine", "markov_rhythm",
})

GENERATOR_CLASS_TO_TYPE: dict[type, str] = {
    # melodic / harmonic core
    MelodyGenerator: "melody",
    ArpeggiatorGenerator: "arpeggiator",
    BassGenerator: "bass",
    ChordGenerator: "chord",
    # strings
    ViolinGenerator: "violin",
    ViolaGenerator: "viola",
    CelloGenerator: "cello",
    ContrabassGenerator: "contrabass",
    HarpGenerator: "harp",
    # woodwinds
    FluteGenerator: "flute",
    OboeGenerator: "oboe",
    ClarinetGenerator: "clarinet",
    BassoonGenerator: "bassoon",
    # brass
    TrumpetGenerator: "trumpet",
    TromboneGenerator: "trombone",
    FrenchHornGenerator: "french_horn",
    TubaGenerator: "tuba",
    BrassSectionGenerator: "brass_section",
    # keys / pads / voices
    PianoCompGenerator: "piano_comp",
    ChoirAahsGenerator: "choir_ahhs",
    DroneGenerator: "drone",
    # pitched + unpitched percussion
    MalletPercussionGenerator: "mallet",
    TimpaniGenerator: "timpani",
    SnareDrumGenerator: "snare_drum",
    OrchestralCymbalGenerator: "orchestral_cymbal",
    ConcertBassDrumGenerator: "concert_bass_drum",
    TubularBellsGenerator: "tubular_bells",
    ShakerGenerator: "shaker",
    WindMachineGenerator: "wind_machine",
    PercussionGenerator: "percussion",
}
