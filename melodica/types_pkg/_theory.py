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
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, List

from melodica.theory import Mode, Quality, CHORD_TEMPLATES, MODE_DATABASE, get_mode_intervals

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
        ivls = self.intervals()
        return [(self.root + i) % OCTAVE for i in ivls]

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
        Parse a Roman numeral like 'Im7', 'V', 'bVIImaj7', 'Im7/VII'.
        Always relative to this scale.
        """
        import re

        pattern = r"^([#b])?([IViv]+)(m|maj)?(7)?(?:/([IViv]+))?$"
        match = re.match(pattern, roman)
        if not match:
            raise ValueError(f"Invalid Roman numeral: {roman!r}")

        accidental, numeral, quality_str, has_7, inv_numeral = match.groups()
        mapping = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
        degree = mapping.get(numeral.upper(), 1)

        is_minor = numeral.islower() or quality_str == "m"
        is_maj7 = quality_str == "maj"
        wants_seventh = has_7 is not None or is_maj7

        # Get diatonic chord (correctly handles 7th quality via fix #1)
        chord = self.diatonic_chord(degree, seventh=wants_seventh)

        # Explicit quality overrides — only override triad quality, keep 7th from diatonic
        if is_maj7 and has_7:
            chord = dataclasses.replace(chord, quality=Quality.MAJOR7)
        elif is_minor and has_7:
            chord = dataclasses.replace(chord, quality=Quality.MINOR7)
        elif numeral.isupper() and not wants_seventh and not is_maj7:
            chord = dataclasses.replace(chord, quality=Quality.MAJOR)
        elif is_minor and not wants_seventh:
            chord = dataclasses.replace(chord, quality=Quality.MINOR)

        if inv_numeral:
            inv_deg = mapping.get(inv_numeral.upper(), 1)
            inv_pc = self.degrees()[inv_deg - 1]
            chord.bass = inv_pc

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
            root=root_pc,
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
