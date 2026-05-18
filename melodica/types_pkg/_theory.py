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

"""Scales, chords, and harmonic analysis."""

from __future__ import annotations

import dataclasses
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, List

from melodica.theory import Mode, Quality, CHORD_TEMPLATES, MODE_DATABASE, get_mode_intervals
from melodica.theory.chord_registry import ROMAN_QUALITY_MAP, _CUSTOM_PATTERN

# Compile the Roman numeral parser regex once at startup
_Q = (
    _CUSTOM_PATTERN + r"|"
    r"maj13|maj11|maj9|maj7|maj"
    r"|m7b5|m13|m11|m9|m6|m7|m"
    r"|dim7|dim"
    r"|aug"
    r"|sus4|sus2|sus"
    r"|add13|add11|add9"
    r"|13|11|9|7|6"
    r"|5"          # power chord
)
_ROMAN_REGEX = re.compile(
    r"^([#b])?"                        # optional root accidental prefix
    r"([IViv]+)"                       # Roman numeral
    r"([#b])?"                        # optional root accidental suffix
    rf"({_Q})?"                        # optional quality token
    r"(?:/([#b]?[IViv\d]+))?$"         # optional slash bass (accidental/numeral/digit)
)

OCTAVE: int = 12


class HarmonicFunction(Enum):
    """Tonal function of a chord within a key."""

    TONIC = "T"
    SUBDOMINANT = "S"
    DOMINANT = "D"
    SECONDARY = "X"  # secondary dominant / applied chord


@dataclass(frozen=True)
class Scale:
    """
    A musical scale defined by root pitch class and mode.
    Immutable value object; equality is structural.
    """

    root: int  # pitch class 0=C … 11=B
    mode: Mode

    def __post_init__(self) -> None:
        if not (0 <= self.root <= 11):
            raise ValueError(f"root must be 0–11, got {self.root}")

    def intervals(self) -> list[float]:
        """Raw intervals above root (now supporting floats for microtonality)."""
        return get_mode_intervals(self.mode)

    def degrees(self) -> list[float]:
        """Pitch classes of the scale tones (0-11.99), ordered by degree."""
        try:
            return self._degrees_cache  # type: ignore
        except AttributeError:
            ivls = self.intervals()
            val = [(self.root + i) % OCTAVE for i in ivls]
            object.__setattr__(self, "_degrees_cache", val)
            return val

    def contains(self, pc: float) -> bool:
        return any(abs(pc - d) < 0.01 for d in self.degrees())

    def degree_of(self, pitch_class: float) -> int | None:
        """1-based degree of a pitch class in this scale, or None."""
        degs = self.degrees()
        for i, d in enumerate(degs):
            if abs((pitch_class % OCTAVE) - d) < 0.01:
                return i + 1
        return None

    def parse_roman(self, roman: str) -> "ChordLabel":
        """
        Parse a Roman numeral chord symbol relative to this scale.

        Supported formats
        -----------------
        Triads      : I  ii  bVII  #IV  Idim  Iaug  Isus  Isus2  Isus4  I5
        Sevenths    : Imaj7  Im7  I7  Idim7  Im7b5  IIdim7
        Extensions  : Imaj9  Imaj11  Imaj13  I9  I11  I13
                      Im9  Im11  Im6  I6  Iadd9  Iadd11
        Slash chords: I/V  Im7/III  bVII/IV  (bass note supports b/# accidentals)
        Inversions  : I/3 (first inversion), I/5 (second inversion), I/7 (third inversion)

        All accidentals (b / #) may precede the root numeral.
        """
        match = _ROMAN_REGEX.match(roman)
        if not match:
            raise ValueError(f"Invalid Roman numeral: {roman!r}")

        acc_pref, numeral, acc_suff, quality_str, inv_numeral = match.groups()
        accidental = acc_pref or acc_suff
        quality_str = quality_str or ""

        mapping = {
            "I": 1, "II": 2, "III": 3, "IV": 4,
            "V": 5, "VI": 6, "VII": 7, "VIII": 8,
        }
        degree = mapping.get(numeral.upper(), 1)

        # --- Decode quality token ---
        q = quality_str

        def _resolve_quality(token: str, is_upper: bool) -> Quality:
            if token in ROMAN_QUALITY_MAP:
                return ROMAN_QUALITY_MAP[token]
            if token in ("maj7", "maj", "maj9", "maj11", "maj13"):
                return Quality.MAJOR7
            if token in ("m7", "m9", "m11", "m13"):
                return Quality.MINOR7
            if token in ("7", "9", "11", "13"):
                return Quality.DOMINANT7
            if token == "dim7":
                return Quality.FULL_DIM7
            if token == "m7b5":
                return Quality.HALF_DIM7
            if token == "dim":
                return Quality.DIMINISHED
            if token == "aug":
                return Quality.AUGMENTED
            if token in ("sus4", "sus"):
                return Quality.SUS4
            if token == "sus2":
                return Quality.SUS2
            if token == "5":
                return Quality.POWER
            # Default fallback based on numeral casing
            return Quality.MAJOR if is_upper else Quality.MINOR

        # Whether to request a seventh from the diatonic builder
        wants_seventh = (
            q in ("maj7", "maj", "maj9", "maj11", "maj13", "m7", "m9", "m11", "m13", "m7b5", "dim7", "7", "9", "11", "13")
            or q in ROMAN_QUALITY_MAP
        )

        # --- Get diatonic base chord ---
        chord = self.diatonic_chord(degree, seventh=wants_seventh)

        # --- Apply root accidental ---
        if accidental == 'b':
            chord = dataclasses.replace(chord, root=(chord.root - 1) % 12)
        elif accidental == '#':
            chord = dataclasses.replace(chord, root=(chord.root + 1) % 12)

        # --- Quality override ---
        chord = dataclasses.replace(chord, quality=_resolve_quality(q, numeral.isupper()))

        # --- Extension annotations (stored in ChordLabel.extensions) ---
        exts: list[int] = []
        root = chord.root
        if q in ("add9", "9", "maj9", "m9"):
            exts.append((root + 14) % 12)   # 9th
        if q in ("add11", "11", "maj11", "m11"):
            exts.append((root + 17) % 12)   # 11th
        if q in ("add13", "13", "maj13", "m13"):
            exts.append((root + 21) % 12)   # 13th
        if q in ("6", "m6"):
            exts.append((root + 9) % 12)    # added 6th
        if exts:
            chord = dataclasses.replace(chord, extensions=sorted(set(exts)))

        # --- Slash bass / Inversions ---
        if inv_numeral:
            if inv_numeral.isdigit():
                # Chord inversion mode (3 = third of chord, 5 = fifth, 7 = seventh)
                digit = int(inv_numeral)
                if digit == 3:
                    # First inversion (bass = third)
                    # For major: +4 semitones; minor: +3 semitones; else default to minor
                    ivl = 3 if chord.quality in (Quality.MINOR, Quality.MINOR7, Quality.HALF_DIM7, Quality.FULL_DIM7) else 4
                    chord.bass = (chord.root + ivl) % 12
                elif digit == 5:
                    # Second inversion (bass = fifth)
                    chord.bass = (chord.root + 7) % 12
                elif digit == 7:
                    # Third inversion (bass = seventh)
                    ivl = 10 if chord.quality in (Quality.DOMINANT7, Quality.MINOR7, Quality.HALF_DIM7) else 11
                    chord.bass = (chord.root + ivl) % 12
                else:
                    chord.bass = chord.root
            else:
                # Specific scale degree slash bass mode
                bass_acc = ""
                bass_num = inv_numeral
                if inv_numeral and inv_numeral[0] in ("#", "b"):
                    bass_acc = inv_numeral[0]
                    bass_num = inv_numeral[1:]
                inv_deg = mapping.get(bass_num.upper(), 1)
                inv_pc = self.degrees()[inv_deg - 1]
                if bass_acc == 'b':
                    inv_pc = (inv_pc - 1) % 12
                elif bass_acc == '#':
                    inv_pc = (inv_pc + 1) % 12
                chord.bass = int(round(inv_pc))

        return chord

    def diatonic_chord(self, degree: int, seventh: bool = False) -> "ChordLabel":
        degs = self.degrees()
        n = len(degs)
        if not (1 <= degree <= n):
            raise ValueError(f"degree must be 1–{n}, got {degree}")
        root_pc = degs[(degree - 1) % n]
        third_pc = degs[(degree + 1) % n]
        fifth_pc = degs[(degree + 3) % n]
        seventh_pc = degs[(degree + 5) % n] if seventh else None

        third_ivl = (third_pc - root_pc) % 12
        fifth_ivl = (fifth_pc - root_pc) % 12

        if third_ivl == 4 and fifth_ivl == 7:
            if seventh and seventh_pc is not None:
                seventh_ivl = (seventh_pc - root_pc) % 12
                quality = Quality.DOMINANT7 if seventh_ivl == 10 else Quality.MAJOR7
            else:
                quality = Quality.MAJOR
        elif third_ivl == 3 and fifth_ivl == 7:
            quality = Quality.MINOR7 if seventh else Quality.MINOR
        elif third_ivl == 3 and fifth_ivl == 6:
            if seventh:
                seventh_ivl = (seventh_pc - root_pc) % 12  # type: ignore[operator]
                quality = Quality.FULL_DIM7 if seventh_ivl == 9 else Quality.HALF_DIM7
            else:
                quality = Quality.DIMINISHED
        elif third_ivl == 4 and fifth_ivl == 8:
            quality = Quality.AUGMENTED
        else:
            quality = Quality.MAJOR  # fallback
        return ChordLabel(
            root=int(round(root_pc)),
            quality=quality,
            extensions=[],
            degree=degree,
        )

    def get_parallel_scale(self, new_mode: Mode) -> "Scale":
        return Scale(root=self.root, mode=new_mode)

    def borrowed_chord(self, degree: int, mode: Mode, seventh: bool = False) -> "ChordLabel":
        parallel_scale = self.get_parallel_scale(mode)
        return parallel_scale.diatonic_chord(degree, seventh=seventh)


def parse_progression(prog_str: str, key: Scale) -> list[ChordLabel]:
    """Parses a Roman numeral progression like 'Im VII IIm Im'."""
    parts = prog_str.split(" - ") if " - " in prog_str else prog_str.split()
    chords = []
    t = 0.0
    for p in parts:
        p = p.strip()
        if not p:
            continue
        chord = key.parse_roman(p)
        chord.start = t
        chord.duration = 4.0  # Default 1 bar
        chords.append(chord)
        t += 4.0
    return chords


@dataclass
class ChordLabel:
    root: int  # pitch class 0=C … 11=B
    quality: Quality
    extensions: list[int] = field(default_factory=list)  # extra tones
    bass: int | None = None  # slash bass
    inversion: int = 0  # 0=root, 1=first, 2=second, 3=third
    start: float = 0.0
    duration: float = 4.0
    degree: int | None = None
    function: HarmonicFunction | None = None

    def __post_init__(self) -> None:
        if not (0 <= self.root <= 11):
            raise ValueError(f"root must be 0–11, got {self.root}")
        if self.duration <= 0:
            raise ValueError(f"duration must be > 0, got {self.duration}")

    @property
    def end(self) -> float:
        return self.start + self.duration

    def pitch_classes(self) -> list[int]:
        template = CHORD_TEMPLATES.get(self.quality, [0])
        pcs = {(self.root + ivl) % 12 for ivl in template}
        pcs.update((self.root + ext) % 12 for ext in self.extensions)
        return sorted(pcs)

    def contains_pitch_class(self, pc: int) -> bool:
        return pc % 12 in self.pitch_classes()
