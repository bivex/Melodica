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
    IONIAN = "ionian"  # Alias for MAJOR
    NATURAL_MINOR = "natural_minor"
    AEOLIAN = "aeolian"  # Alias for NATURAL_MINOR
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

    # --- Streaming & Production Extensions ---
    PHRYGIAN_DOMINANT = "phrygian_dominant"
    DOUBLE_HARMONIC = "double_harmonic"
    DORIAN_PENTATONIC = "dorian_pentatonic"
    MINOR_HEXATONIC = "minor_hexatonic"
    SUSPENDED_PENTA = "suspended_penta"
    ACOUSTIC_MINOR = "acoustic_minor"
    LYDIAN_MINOR = "lydian_minor"
    SUPER_LOCRIAN = "super_locrian"
    DOUBLE_HARM_MAJOR = "double_harmonic_major"
    LYDIAN_AUG_MODE = "lydian_aug_mode"
    ACOUSTIC_MAJOR = "acoustic_major"

@dataclass
class ScaleDefinition:
    intervals: List[float]
    category: str = "Uncategorized"
    mood: List[str] = field(default_factory=list)
    recommended_instruments: List[str] = field(default_factory=list)
    microtonal_support: bool = False
    bpm_range: tuple[int, int] = (60, 180)
    genres: List[str] = field(default_factory=list)
    energy: float = 0.5

MODE_DATABASE: dict[Mode, ScaleDefinition] = {
    # Common
    Mode.MAJOR: ScaleDefinition([0, 2, 4, 5, 7, 9, 11], "Common", ["Happy", "Heroic", "Bright"]),
    Mode.IONIAN: ScaleDefinition([0, 2, 4, 5, 7, 9, 11], "Common", ["Happy", "Heroic", "Bright"]),
    Mode.NATURAL_MINOR: ScaleDefinition([0, 2, 3, 5, 7, 8, 10], "Common", ["Sad", "Serious"]),
    Mode.AEOLIAN: ScaleDefinition([0, 2, 3, 5, 7, 8, 10], "Common", ["Sad", "Serious"]),
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
    Mode.MYSTIC: ScaleDefinition([0, 2, 4, 6, 9, 11], "Scriabin", ["Mystic"]),
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

    # Blues & Pentatonic
    Mode.BLUES:              ScaleDefinition([0, 3, 5, 6, 7, 10], "Blues", ["Blues", "Raw"]),
    Mode.MAJOR_PENTATONIC:   ScaleDefinition([0, 2, 4, 7, 9], "Pentatonic", ["Open", "Folk"]),
    Mode.MINOR_PENTATONIC:   ScaleDefinition([0, 3, 5, 7, 10], "Pentatonic", ["Blues", "Rock"]),

    # Symmetric
    Mode.WHOLE_TONE:         ScaleDefinition([0, 2, 4, 6, 8, 10], "Symmetric", ["Floating", "Dreamy"]),
    Mode.DIMINISHED:         ScaleDefinition([0, 2, 3, 5, 6, 8, 9, 11], "Symmetric", ["Tense", "Jazz"]),
    Mode.HALF_WHOLE_DIMINISHED: ScaleDefinition([0, 1, 3, 4, 6, 7, 9, 10], "Symmetric", ["Jazz", "Dark"]),
    Mode.WHOLE_HALF_DIMINISHED: ScaleDefinition([0, 2, 3, 5, 6, 8, 9, 11], "Symmetric", ["Jazz"]),

    # Bebop
    Mode.BEBOP_MAJOR:        ScaleDefinition([0, 2, 4, 5, 7, 8, 9, 11], "Jazz", ["Bebop", "Major"]),
    Mode.BEBOP_MINOR:        ScaleDefinition([0, 2, 3, 5, 7, 8, 10, 11], "Jazz", ["Bebop", "Minor"]),
    Mode.BEBOP_DOMINANT:     ScaleDefinition([0, 2, 4, 5, 7, 9, 10, 11], "Jazz", ["Bebop", "Dominant"]),
    Mode.BEBOP_DOM_6:        ScaleDefinition([0, 2, 4, 5, 7, 9, 10], "Jazz", ["Bebop"]),
    Mode.BEBOP_DOM_7:        ScaleDefinition([0, 1, 2, 4, 5, 7, 9, 10], "Jazz", ["Bebop"]),
    Mode.BEBOP_DOM_8:        ScaleDefinition([0, 2, 3, 5, 6, 7, 9, 10], "Jazz", ["Bebop"]),

    # Hungarian / Gypsy
    Mode.HUNGARIAN_MINOR:    ScaleDefinition([0, 2, 3, 6, 7, 8, 11], "Ethnic", ["Hungarian", "Dark"]),
    Mode.HUNGARIAN_MAJOR:    ScaleDefinition([0, 3, 4, 6, 7, 9, 10], "Ethnic", ["Hungarian"]),
    Mode.GYPSY:              ScaleDefinition([0, 1, 4, 5, 7, 8, 11], "Ethnic", ["Gypsy", "Exotic"]),

    # Japanese
    Mode.HIROJOSHI:          ScaleDefinition([0, 2, 3, 7, 8], "Ethnic", ["Japanese", "Zen"]),
    Mode.KUMOI:              ScaleDefinition([0, 2, 5, 7, 10], "Ethnic", ["Japanese"]),
    Mode.JAPANESE:           ScaleDefinition([0, 1, 5, 7, 8], "Ethnic", ["Japanese", "Pentatonic"]),

    # Exotic
    Mode.SPANISH_8_TONE:     ScaleDefinition([0, 1, 2, 3, 5, 6, 7, 8], "Exotic", ["Spanish", "Flamenco"]),
    Mode.BYZANTINE:          ScaleDefinition([0, 1, 4, 5, 7, 8, 11], "Exotic", ["Byzantine", "Eastern"]),
    Mode.PERSIAN:            ScaleDefinition([0, 1, 4, 5, 6, 8, 11], "Exotic", ["Persian", "Ancient"]),
    Mode.ARABIAN:            ScaleDefinition([0, 2, 3, 6, 7, 8, 11], "Exotic", ["Arabian", "Desert"]),
    Mode.ALTERED:            ScaleDefinition([0, 1, 3, 4, 6, 8, 10], "Jazz", ["Altered", "Tension"]),
    Mode.LYDIAN_DOMINANT:    ScaleDefinition([0, 2, 4, 6, 7, 9, 10], "Jazz", ["Lydian Dom", "Jazz"]),

    # Neapolitan
    Mode.NEAPOLITAN_MAJOR:   ScaleDefinition([0, 1, 3, 5, 7, 9, 11], "Classical", ["Neapolitan"]),
    Mode.NEAPOLITAN_MINOR:   ScaleDefinition([0, 1, 3, 5, 7, 8, 11], "Classical", ["Neapolitan", "Dark"]),

    # Other theoretical
    Mode.AEOLIAN_BB7:        ScaleDefinition([0, 2, 3, 5, 7, 8, 9], "Theoretical", ["Minor variant"]),
    Mode.AUGMENTED:          ScaleDefinition([0, 3, 4, 7, 8, 11], "Symmetric", ["Augmented", "Alien"]),
    Mode.AUGMENTED_MODE_2:   ScaleDefinition([0, 1, 4, 5, 8, 9], "Symmetric", ["Augmented"]),
    Mode.ALT_BB3:            ScaleDefinition([0, 1, 3, 4, 6, 8, 10], "Jazz", ["Altered"]),
    Mode.ALT_BB3_BB7:        ScaleDefinition([0, 1, 3, 4, 6, 8, 9], "Jazz", ["Altered", "Dark"]),

    # --- Streaming & Production Extensions ---
    # Block 1 - Trap / Drill / Hip-hop
    Mode.PHRYGIAN_DOMINANT: ScaleDefinition(
        [0, 1, 4, 5, 7, 8, 10], "Trap",
        ["Dark", "Arabic", "Drill"], ["808", "Piano"],
        bpm_range=(120, 160), genres=["trap", "drill", "hiphop"], energy=0.85
    ),
    Mode.DOUBLE_HARMONIC: ScaleDefinition(
        [0, 1, 4, 5, 7, 8, 11], "Trap",
        ["Evil", "Middle-Eastern", "Dissonant"], ["Strings", "Piano"],
        bpm_range=(110, 150), genres=["trap", "dark_trap"], energy=0.9
    ),
    
    # Block 2 - Lo-Fi / Chillhop
    Mode.DORIAN_PENTATONIC: ScaleDefinition(
        [0, 2, 3, 7, 9], "Lo-Fi",
        ["Chill", "Study", "Nostalgic"], ["Piano", "Rhodes", "Guitar"],
        bpm_range=(70, 95), genres=["lofi", "chillhop"], energy=0.3
    ),
    Mode.MINOR_HEXATONIC: ScaleDefinition(
        [0, 2, 3, 5, 7, 10], "Lo-Fi",
        ["Smooth", "Mellow", "Dreamy"], ["Guitar", "Keys"],
        bpm_range=(65, 90), genres=["lofi", "jazzhop"], energy=0.25
    ),
    Mode.SUSPENDED_PENTA: ScaleDefinition(
        [0, 2, 5, 7, 10], "Lo-Fi",
        ["Open", "Ambient", "Spacious"], ["Piano", "Synth Pad"],
        bpm_range=(60, 100), genres=["lofi", "ambient"], energy=0.2
    ),

    # Block 3 - Cinematic / Epic
    Mode.ACOUSTIC_MINOR: ScaleDefinition(
        [0, 2, 3, 6, 7, 9, 10], "Cinematic",
        ["Dorian #4", "Bartók", "Mysterious"], ["Strings", "Woodwinds"],
        bpm_range=(80, 140), genres=["cinematic", "epic"], energy=0.6
    ),
    Mode.LYDIAN_MINOR: ScaleDefinition(
        [0, 2, 4, 6, 7, 8, 10], "Cinematic",
        ["Epic", "Bittersweet", "Zimmer"], ["Strings", "Brass", "Choir"],
        bpm_range=(70, 130), genres=["cinematic", "epic"], energy=0.75
    ),
    Mode.SUPER_LOCRIAN: ScaleDefinition(
        [0, 1, 3, 4, 6, 8, 10], "Cinematic",
        ["Maximum Tension", "Climax"], ["Brass", "Percussion", "Synthesizer"],
        bpm_range=(90, 160), genres=["cinematic", "industrial"], energy=0.95
    ),
    Mode.DOUBLE_HARM_MAJOR: ScaleDefinition(
        [0, 1, 4, 5, 7, 8, 11], "Cinematic",
        ["Epic", "Ancient", "Boss-Fight"], ["Orchestra", "Choir"],
        bpm_range=(100, 150), genres=["cinematic", "epic"], energy=0.88
    ),

    # Block 4 - Ambient / Space
    Mode.ACOUSTIC_MAJOR: ScaleDefinition(
        [0, 2, 4, 6, 7, 9, 10], "Ambient",
        ["Floating", "Overtone", "Debussy"], ["Piano", "Harp", "Strings"],
        bpm_range=(50, 110), genres=["ambient", "impressionism"], energy=0.2
    ),
    Mode.LYDIAN_AUG_MODE: ScaleDefinition(
        [0, 2, 4, 6, 8, 9, 11], "Ambient",
        ["Ethereal", "Sci-Fi", "Floating"], ["Synth", "Piano", "Flute"],
        bpm_range=(55, 115), genres=["ambient", "scifi"], energy=0.3
    )
}

# Known intentional interval-set aliases (different names, same scale by design)
_INTENTIONAL_ALIASES: set[frozenset[Mode]] = {
    frozenset({Mode.MAJOR, Mode.IONIAN}),
    frozenset({Mode.NATURAL_MINOR, Mode.AEOLIAN, Mode.QUARTER_TONE_MINOR}),
    frozenset({Mode.WHOLE_TONE, Mode.MESSIAEN_1}),
    frozenset({Mode.MESSIAEN_2, Mode.HALF_WHOLE_DIMINISHED}),
    frozenset({Mode.MESSIAEN_3, Mode.AUGMENTED_MODE_2}),
    frozenset({Mode.DOUBLE_HARMONIC, Mode.DOUBLE_HARM_MAJOR, Mode.BYZANTINE, Mode.GYPSY, Mode.SUSPENSE}),
    frozenset({Mode.ALTERED, Mode.ALT_BB3, Mode.SUPER_LOCRIAN}),
    frozenset({Mode.DIMINISHED, Mode.WHOLE_HALF_DIMINISHED}),
    frozenset({Mode.ENIGMATIC, Mode.DORIAN_B2}),
    frozenset({Mode.HUNGARIAN_MINOR, Mode.ARABIAN}),
    frozenset({Mode.KUMOI, Mode.SUSPENDED_PENTA}),
    frozenset({Mode.LYDIAN_DOMINANT, Mode.ACOUSTIC_MAJOR}),
    frozenset({Mode.LYDIAN, Mode.YAMAN}),
    frozenset({Mode.MIXOLYDIAN, Mode.BEBOP_DOM_6}),
    frozenset({Mode.SLENDRO_APPROX, Mode.BHUPALI, Mode.MAJOR_PENTATONIC}),
}


def _validate_mode_database() -> list[str]:
    """Validate MODE_DATABASE for structural errors. Returns list of warnings."""
    warnings: list[str] = []
    for mode, defn in MODE_DATABASE.items():
        ivs = defn.intervals
        if ivs[0] != 0:
            warnings.append(f"{mode.name}: intervals do not start with 0: {ivs}")
        if ivs != sorted(ivs):
            warnings.append(f"{mode.name}: intervals not sorted ascending: {ivs}")
        for i in range(1, len(ivs)):
            if ivs[i] - ivs[i - 1] <= 0:
                warnings.append(f"{mode.name}: non-positive gap at index {i}: {ivs}")

    seen: dict[tuple[float, ...], list[Mode]] = {}
    for mode, defn in MODE_DATABASE.items():
        key = tuple(defn.intervals)
        seen.setdefault(key, []).append(mode)
    for key, modes in seen.items():
        if len(modes) > 1:
            group = frozenset(modes)
            if not any(group <= alias for alias in _INTENTIONAL_ALIASES):
                names = ", ".join(m.name for m in modes)
                warnings.append(f"Unintentional duplicate intervals {key}: {names}")
    return warnings


_MODE_WARNINGS = _validate_mode_database()
assert not _MODE_WARNINGS, (
    "MODE_DATABASE validation failed:\n" + "\n".join(_MODE_WARNINGS)
)

# Fallback/Backward compat:
# --- Programmatic World Scale Engine ---
MELAKARTA_NAMES = [
    "kanakangi", "ratnangi", "ganamurti", "vanaspati", "manavati", "tanarupi",
    "senavati", "hanumatodi", "dhenuka", "natakapriya", "kokilapriya", "rupavati",
    "gayakapriya", "vakulabharanam", "mayamalavagowla", "chakravakam", "suryakantam", "hatakambari",
    "jhankaradhwani", "natabhairavi", "keeravani", "kharaharapriya", "gourimanohari", "varunapriya",
    "mararanjani", "charukesi", "sarasangi", "harikambhoji", "dhirasankarabharanam", "naganandini",
    "yagapriya", "ragavardhini", "gangeyabhushani", "vagadhisvari", "shulini", "chalanata",
    "salagam", "jalarnavam", "jhalavarali", "navaneetam", "pavani", "raghupriya",
    "gavambodhi", "bhavapriya", "shubhapantuvarali", "shadvidhamargini", "suvarnangi", "divyamani",
    "dhavalambari", "namanarayani", "kamavardhini", "ramapriya", "gamanashrama", "vishwambhari",
    "syamalangi", "shanmukhapriya", "simhendramadhyamam", "hemavati", "dharmavati", "nitimati",
    "kantamani", "rishabhapriya", "latangi", "vachaspati", "mechakalyani", "chitrambari",
    "sucharitra", "jyotiswarupini", "dhatuvardani", "nasikabhushani", "kosalam", "rasikapriya"
]

def get_melakarta_intervals(index: int) -> List[float]:
    """Dynamically generates the interval array of the 72 Carnatic Melakarta Ragas mathematically."""
    idx = index - 1
    m = 5.0 if idx < 36 else 6.0
    
    chakra = (idx % 36) // 6
    rg_map = [
        (1.0, 2.0), # R1, G1
        (1.0, 3.0), # R1, G2
        (1.0, 4.0), # R1, G3
        (2.0, 3.0), # R2, G2
        (2.0, 4.0), # R2, G3
        (3.0, 4.0)  # R3, G3
    ]
    r, g = rg_map[chakra]
    
    scale_in_chakra = idx % 6
    dn_map = [
        (8.0, 9.0),  # D1, N1
        (8.0, 10.0), # D1, N2
        (8.0, 11.0), # D1, N3
        (9.0, 10.0), # D2, N2
        (9.0, 11.0), # D2, N3
        (10.0, 11.0) # D3, N3
    ]
    d, n = dn_map[scale_in_chakra]
    
    return [0.0, r, g, m, 7.0, d, n]

def get_mode_intervals(mode: Mode | str) -> List[float]:
    """Resolves scale intervals, supporting both predefined Mode enums, raw strings, dynamic ragas, and exotic scales."""
    mode_name = mode.value if hasattr(mode, "value") else str(mode)
    mode_name_lower = mode_name.lower().replace("carnatic_", "")
    
    if hasattr(mode, "value") and mode in MODE_DATABASE:
        return MODE_DATABASE[mode].intervals
        
    for m, definition in MODE_DATABASE.items():
        if m.value == mode_name:
            return definition.intervals
            
    # Check exotic database
    from melodica.theory.exotic_database import EXOTIC_SCALE_DATABASE
    if mode_name_lower in EXOTIC_SCALE_DATABASE:
        return EXOTIC_SCALE_DATABASE[mode_name_lower]
            
    if mode_name_lower in MELAKARTA_NAMES:
        idx = MELAKARTA_NAMES.index(mode_name_lower) + 1
        return get_melakarta_intervals(idx)
        
    return [0.0, 2.0, 4.0, 5.0, 7.0, 9.0, 11.0] # Fallback: Major/Ionian


def pick_modes(
    genre: str | None = None,
    energy: float | None = None,
    bpm: int | None = None,
    max_results: int = 5
) -> list[Mode]:
    """
    Search and filter modes in the database based on target genre, energy, and BPM.
    Returns list of Modes matching the criteria sorted by distance to target energy level.
    """
    matches = []
    
    for m, definition in MODE_DATABASE.items():
        # 1. Filter by genre (substring case-insensitive match)
        if genre:
            genre_lower = genre.lower()
            if not any(genre_lower in g.lower() for g in definition.genres):
                continue
                
        # 2. Filter by BPM range
        if bpm:
            min_bpm, max_bpm = definition.bpm_range
            if not (min_bpm <= bpm <= max_bpm):
                continue
                
        # Calculate energy difference if target energy is specified
        energy_diff = abs(definition.energy - energy) if energy is not None else 0.0
        matches.append((m, energy_diff))
        
    # Sort matches by closest energy
    matches.sort(key=lambda x: x[1])
    return [m for m, _ in matches[:max_results]]
