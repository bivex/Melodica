# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.score.chord_parser — High-level music chord & key signature parser.

Translates human-readable lead-sheet chord symbols ('Am7', 'Fmaj7', 'C/E', 'E7sus4')
and Roman numerals ('ii7', 'V7', 'Imaj7') into domain ChordLabel objects.
"""

from __future__ import annotations

import re
from melodica.theory.chords import Quality
from melodica.types import ChordLabel, Mode, Scale

_PITCH_CLASSES: dict[str, int] = {
    "c": 0, "b#": 0,
    "c#": 1, "db": 1,
    "d": 2,
    "d#": 3, "eb": 3,
    "e": 4, "fb": 4,
    "f": 5, "e#": 5,
    "f#": 6, "gb": 6,
    "g": 7,
    "g#": 8, "ab": 8,
    "a": 9,
    "a#": 10, "bb": 10,
    "b": 11, "cb": 11,
}

_ROMAN_REGEX = re.compile(
    r"^(b|#)?(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i)(.*)$"
)

_CHORD_REGEX = re.compile(
    r"^([a-gA-G][#b]?)([^/]*)(?:/([a-gA-G][#b]?))?$"
)

_QUALITY_MAP: list[tuple[re.Pattern, Quality]] = [
    # Complex 7th / 9th / alterations
    (re.compile(r"^(maj9|m9|min9|add9|9)$", re.IGNORECASE), None),  # handled individually
    (re.compile(r"^(m7b5|min7b5|ø|half-dim)$", re.IGNORECASE), Quality.HALF_DIM7),
    (re.compile(r"^(dim7|°7|o7)$", re.IGNORECASE), Quality.FULL_DIM7),
    (re.compile(r"^(dim|°|o)$", re.IGNORECASE), Quality.DIMINISHED),
    (re.compile(r"^(aug|\+|aug7|\+7)$", re.IGNORECASE), Quality.AUGMENTED),
    (re.compile(r"^(maj7|m7|min7|\-7|7|dom7|Δ7|Δ)$", re.IGNORECASE), None),  # handled below
    (re.compile(r"^(7sus4|sus4|sus)$", re.IGNORECASE), Quality.SUS4),
    (re.compile(r"^sus2$", re.IGNORECASE), Quality.SUS2),
    (re.compile(r"^5$", re.IGNORECASE), Quality.POWER),
]


def parse_key_signature(key_str: str) -> Scale:
    """
    Parse a key signature string into a Scale object.
    Examples: 'Am', 'A minor', 'C', 'C major', 'D dorian', 'F#m', 'Bb'.
    """
    s = key_str.strip()
    if not s:
        return Scale(root=0, mode=Mode.MAJOR)

    # Check for two-part: "D dorian", "F# minor", "Eb major"
    parts = s.split(maxsplit=1)
    root_str = parts[0].lower()
    mode_str = parts[1].lower() if len(parts) > 1 else ""

    # Check if root has minor suffix attached: "Am", "F#m", "Dm"
    if not mode_str:
        if len(root_str) > 1 and root_str.endswith("m") and root_str not in ("dim",):
            mode_str = "minor"
            root_str = root_str[:-1]

    if root_str not in _PITCH_CLASSES:
        raise ValueError(f"Unknown root pitch in key signature: '{key_str}'")

    root = _PITCH_CLASSES[root_str]

    if not mode_str or mode_str in ("maj", "major", "ionian"):
        mode = Mode.MAJOR
    elif mode_str in ("m", "min", "minor", "aeolian", "natural_minor"):
        mode = Mode.NATURAL_MINOR
    elif mode_str in ("dorian",):
        mode = Mode.DORIAN
    elif mode_str in ("phrygian",):
        mode = Mode.PHRYGIAN
    elif mode_str in ("lydian",):
        mode = Mode.LYDIAN
    elif mode_str in ("mixolydian",):
        mode = Mode.MIXOLYDIAN
    elif mode_str in ("locrian",):
        mode = Mode.LOCRIAN
    elif mode_str in ("harmonic_minor", "harmonic minor"):
        mode = Mode.HARMONIC_MINOR
    elif mode_str in ("melodic_minor", "melodic minor"):
        mode = Mode.MELODIC_MINOR
    else:
        # Fallback to major
        mode = Mode.MAJOR

    return Scale(root=root, mode=mode)


def parse_chord_symbol(
    sym: str,
    scale: Scale | None = None,
    start: float = 0.0,
    duration: float = 4.0,
) -> ChordLabel | None:
    """
    Parse a single chord symbol string into a ChordLabel.
    Accepts:
      - Rests / blanks: '-', '|', 'none', 'rest', '' -> returns None
      - Roman numerals: 'i', 'ii7', 'V7', 'IVmaj7', 'vi', 'bVII'
      - Standard chord symbols: 'Am7', 'Fmaj7', 'Dm7', 'E7sus4', 'C/E', 'G7'
    """
    token = sym.strip()
    if not token or token in ("-", "|", "none", "rest", ".", "x"):
        return None

    # 1. Try Roman numeral if matching Roman pattern
    if _ROMAN_REGEX.match(token):
        ref_scale = scale or Scale(root=0, mode=Mode.MAJOR)
        try:
            ch = ref_scale.parse_roman(token)
            ch.start = start
            ch.duration = duration
            return ch
        except Exception:
            pass  # Fallback to standard chord symbol parser

    # 2. Parse standard chord symbol
    m = _CHORD_REGEX.match(token)
    if not m:
        raise ValueError(f"Cannot parse chord symbol: '{token}'")

    root_name, suffix, bass_name = m.group(1), m.group(2).strip(), m.group(3)
    root_l = root_name.lower()
    if root_l not in _PITCH_CLASSES:
        raise ValueError(f"Invalid chord root: '{root_name}' in '{token}'")
    root = _PITCH_CLASSES[root_l]

    bass = _PITCH_CLASSES[bass_name.lower()] if bass_name else None

    # Parse quality
    quality = _parse_quality_suffix(suffix)

    return ChordLabel(
        root=root,
        quality=quality,
        start=start,
        duration=duration,
        bass=bass,
    )


_SUFFIX_EXACT_MAP: dict[str, Quality] = {
    "": Quality.MAJOR,
    "maj": Quality.MAJOR,
    "m": Quality.MINOR,
    "min": Quality.MINOR,
    "-": Quality.MINOR,
    "maj7": Quality.MAJOR7,
    "m7": Quality.MINOR7,
    "min7": Quality.MINOR7,
    "-7": Quality.MINOR7,
    "7": Quality.DOMINANT7,
    "dom7": Quality.DOMINANT7,
    "δ7": Quality.MAJOR7,
    "δ": Quality.MAJOR7,
    "maj9": Quality.MAJOR9,
    "m9": Quality.MINOR9,
    "min9": Quality.MINOR9,
    "9": Quality.DOMINANT7,
    "add9": Quality.ADD9,
    "7sus4": Quality.SUS4,
    "sus4": Quality.SUS4,
    "sus": Quality.SUS4,
    "sus2": Quality.SUS2,
    "dim": Quality.DIMINISHED,
    "°": Quality.DIMINISHED,
    "o": Quality.DIMINISHED,
    "dim7": Quality.FULL_DIM7,
    "°7": Quality.FULL_DIM7,
    "o7": Quality.FULL_DIM7,
    "m7b5": Quality.HALF_DIM7,
    "min7b5": Quality.HALF_DIM7,
    "ø": Quality.HALF_DIM7,
    "half-dim": Quality.HALF_DIM7,
    "aug": Quality.AUGMENTED,
    "+": Quality.AUGMENTED,
    "aug7": Quality.AUGMENTED,
    "+7": Quality.AUGMENTED,
    "5": Quality.POWER,
    "power": Quality.POWER,
}


def _parse_quality_suffix(sfx: str) -> Quality:
    """Resolve quality suffix string into Quality enum."""
    return _SUFFIX_EXACT_MAP.get(sfx.lower(), Quality.MAJOR)
