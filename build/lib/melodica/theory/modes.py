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

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import List

class Mode(Enum):
    """Scale modes supported by the engine."""
    MAJOR = "major"
    NATURAL_MINOR = "natural_minor"
    HARMONIC_MINOR = "harmonic_minor"
    MELODIC_MINOR = "melodic_minor"
    DORIAN = "dorian"
    PHRYGIAN = "phrygian"
    LYDIAN = "lydian"
    MIXOLYDIAN = "mixolydian"
    LOCRIAN = "locrian"
    WHOLE_TONE = "whole_tone"
    DIMINISHED = "diminished"
    
    # Bebop
    BEBOP_MAJOR = "bebop_major"
    BEBOP_MINOR = "bebop_minor"
    BEBOP_DOMINANT = "bebop_dominant"
    
    # Blues
    BLUES = "blues"
    
    # Hungarian/Gypsy
    HUNGARIAN_MINOR = "hungarian_minor"
    HUNGARIAN_MAJOR = "hungarian_major"
    GYPSY = "gypsy"
    
    # Japanese/Oriental
    HIROJOSHI = "hirojoshi"
    KUMOI = "kumoi"
    JAPANESE = "japanese"
    
    # Exotic/Other
    SPANISH_8_TONE = "spanish_8_tone"
    BYZANTINE = "byzantine"
    PERSIAN = "persian"
    ARABIAN = "arabian"
    ALTERED = "altered"
    LYDIAN_DOMINANT = "lydian_dominant"
    
    # Pentatonics
    MAJOR_PENTATONIC = "major_pentatonic"
    MINOR_PENTATONIC = "minor_pentatonic"
    
    # Final theoretical batch
    NEAPOLITAN_MAJOR = "neapolitan_major"
    NEAPOLITAN_MINOR = "neapolitan_minor"
    HALF_WHOLE_DIMINISHED = "half_whole_diminished"
    WHOLE_HALF_DIMINISHED = "whole_half_diminished"
    AEOLIAN_BB7 = "aeolian_bb7"
    AUGMENTED = "augmented"
    AUGMENTED_MODE_2 = "augmented_mode_2"
    ALT_BB3 = "alt_bb3"
    ALT_BB3_BB7 = "alt_bb3_bb7"
    BEBOP_DOM_6 = "bebop_dominant_mode_vi"
    BEBOP_DOM_7 = "bebop_dominant_mode_vii"
    BEBOP_DOM_8 = "bebop_dominant_mode_viii"
    
    # --- Messiaen Modes ---
    MESSIAEN_1 = "messiaen_1"  # Whole Tone
    MESSIAEN_2 = "messiaen_2"  # Half-Whole Diminished
    MESSIAEN_3 = "messiaen_3"  # Augmented Mode 2
    MESSIAEN_4 = "messiaen_4"  
    MESSIAEN_5 = "messiaen_5"
    MESSIAEN_6 = "messiaen_6"
    
    # --- Scriabin & Mystic ---
    PROMETHEUS = "prometheus"
    MYSTIC = "mystic"
    ENIGMATIC = "enigmatic"
    
    # --- Modern Jazz/Fusion ---
    LOCRIAN_NAT_2 = "locrian_nat_2"
    MIXOLYDIAN_B6 = "mixolydian_b6"
    DORIAN_B2 = "dorian_b2"
    IONIAN_B5 = "ionian_b5"
    
    # --- Film & Atmosphere ---
    SUSPENSE = "suspense"
    HORROR_CLUSTER = "horror_cluster"
    PEDAL_MINOR = "pedal_minor"
    
    # --- World/Ethnic ---
    SLENDRO_APPROX = "slendro_approx"
    PELOG_APPROX = "pelog_approx"
    BHUPALI = "bhupali"
    YAMAN = "yaman"
    BAYATI = "bayati"
    
    # --- Microtonal Examples ---
    QUARTER_TONE_MINOR = "quarter_tone_minor"
    ARABIC_SIKAH = "arabic_sikah"

@dataclass
class ScaleDefinition:
    intervals: List[float]
    category: str = "Uncategorized"
    mood: List[str] = field(default_factory=list)
    recommended_instruments: List[str] = field(default_factory=list)
    microtonal_support: bool = False

MODE_DATABASE: dict[Mode, ScaleDefinition] = {
    # Common
    Mode.MAJOR: ScaleDefinition([0, 2, 4, 5, 7, 9, 11], "Common", ["Happy", "Heroic", "Bright"]),
    Mode.NATURAL_MINOR: ScaleDefinition([0, 2, 3, 5, 7, 8, 10], "Common", ["Sad", "Serious"]),
    Mode.HARMONIC_MINOR: ScaleDefinition([0, 2, 3, 5, 7, 8, 11], "Common", ["Dramatic"]),
    Mode.MELODIC_MINOR: ScaleDefinition([0, 2, 3, 5, 7, 9, 11], "Common", ["Jazzy"]),
    
    # Church Modes
    Mode.DORIAN: ScaleDefinition([0, 2, 3, 5, 7, 9, 10], "Jazz", ["Cool", "Serious"]),
    Mode.PHRYGIAN: ScaleDefinition([0, 1, 3, 5, 7, 8, 10], "Atmospheric", ["Spanish", "Dark"]),
    Mode.LYDIAN: ScaleDefinition([0, 2, 4, 6, 7, 9, 11], "Film", ["Dreamy", "Modern"]),
    Mode.MIXOLYDIAN: ScaleDefinition([0, 2, 4, 5, 7, 9, 10], "Blues", ["Rock", "Cool"]),
    Mode.LOCRIAN: ScaleDefinition([0, 1, 3, 5, 6, 8, 10], "Atmospheric", ["Tense", "Unstable"]),
    
    # Modernist / Messiaen
    Mode.MESSIAEN_1: ScaleDefinition([0, 2, 4, 6, 8, 10], "Modernist", ["Whole Tone", "Floating"]),
    Mode.MESSIAEN_2: ScaleDefinition([0, 1, 3, 4, 6, 7, 9, 10], "Modernist", ["Diminished", "Unstable"]),
    Mode.MESSIAEN_3: ScaleDefinition([0, 1, 4, 5, 8, 9], "Modernist", ["Augmented", "Mystic"]),
    Mode.MESSIAEN_4: ScaleDefinition([0, 1, 2, 5, 6, 7, 10], "Modernist", ["Alien", "Complex"]),
    Mode.MESSIAEN_5: ScaleDefinition([0, 1, 2, 5, 6, 8, 9], "Modernist", ["Mystic"]),
    Mode.MESSIAEN_6: ScaleDefinition([0, 1, 2, 3, 5, 6, 7, 8, 10], "Modernist", ["Chromatic-ish"]),
    
    # Scriabin
    Mode.PROMETHEUS: ScaleDefinition([0, 2, 4, 6, 9, 10], "Scriabin", ["Radiant", "Ethereal"]),
    Mode.MYSTIC: ScaleDefinition([0, 2, 4, 6, 9, 10], "Scriabin", ["Mystic"]),
    Mode.ENIGMATIC: ScaleDefinition([0, 1, 3, 5, 7, 9, 10], "Verdi", ["Unusual", "Enigmatic"]),
    
    # Jazz Variations
    Mode.LOCRIAN_NAT_2: ScaleDefinition([0, 2, 3, 5, 6, 8, 10], "Jazz", ["Half-Diminished"]),
    Mode.MIXOLYDIAN_B6: ScaleDefinition([0, 2, 4, 5, 7, 8, 10], "Jazz", ["Jazz Minor 5th"]),
    Mode.DORIAN_B2:     ScaleDefinition([0, 1, 3, 5, 7, 9, 10], "Jazz", ["Phrygian #6"]),
    Mode.IONIAN_B5:     ScaleDefinition([0, 2, 4, 5, 6, 9, 11], "Jazz", ["Lydian b7/11 variant"]),
    
    # Film / Horror
    Mode.SUSPENSE:      ScaleDefinition([0, 1, 4, 5, 7, 8, 11], "Film", ["Tension", "Horror"]),
    Mode.HORROR_CLUSTER: ScaleDefinition([0, 1, 2, 5, 6, 7], "Film", ["Horror", "Cluster"]),
    Mode.PEDAL_MINOR:   ScaleDefinition([0, 3, 5, 7, 10, 11], "Film", ["Tension", "Minor-Major"]),
    
    # World
    Mode.SLENDRO_APPROX: ScaleDefinition([0, 2, 4, 7, 9], "Ethnic", ["Indonesia", "Gamelan"]),
    Mode.PELOG_APPROX:   ScaleDefinition([0, 1, 3, 7, 8], "Ethnic", ["Indonesia"]),
    Mode.BHUPALI:        ScaleDefinition([0, 2, 4, 7, 9], "Ethnic", ["India", "Raga"]),
    Mode.YAMAN:          ScaleDefinition([0, 2, 4, 6, 7, 9, 11], "Ethnic", ["India"]),
    Mode.BAYATI:         ScaleDefinition([0, 1, 3, 4, 7, 8], "Ethnic", ["Arabic", "Maqam"]),
    
    # Microtonal
    Mode.QUARTER_TONE_MINOR: ScaleDefinition([0.0, 2.0, 3.0, 5.0, 7.0, 8.0, 10.0], "Modernist", microtonal_support=True),
    Mode.ARABIC_SIKAH:       ScaleDefinition([0.0, 1.5, 3.5, 5.0, 7.0, 8.5, 10.5], "Ethnic", microtonal_support=True),
}

# Fallback/Backward compat:
def get_mode_intervals(mode: Mode) -> List[float]:
    if mode in MODE_DATABASE:
        return MODE_DATABASE[mode].intervals
    # Fallback to a plain list if not in DB (shouldn't happen with full enum mapping)
    return [0, 2, 4, 5, 7, 9, 11] # C major
