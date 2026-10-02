# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/chromatic_percussion.py — Chromatic and Mallet Percussion instruments.

Layer 2/3: Celesta (8), Glockenspiel (9), Music Box (10), Vibraphone (11),
Marimba (12), Xylophone (13), and Dulcimer (15).
Refactored to inherit from MalletFamily, backed by Layer 1 TOML profiles and kernel functions.
"""

from __future__ import annotations

from abc import ABC

from melodica.generate.family import MalletFamily
from melodica.generators import GeneratorParams
from melodica.generators._solo_base import _SoloInstrumentBase


class _ChromaticPercussionBase(MalletFamily, _SoloInstrumentBase, ABC):
    """Abstract base class for chromatic and mallet percussion generators."""

    def __init__(
        self,
        profile_id: str,
        params: GeneratorParams | None = None,
        *,
        pattern: str | None = None,
        pedal: bool | None = None,
        motor_speed_hz: float | None = None,
        mallets: int | None = None,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            profile=profile_id,
            params=params,
            pattern=pattern,
            pedal=pedal,
            motor_speed_hz=motor_speed_hz,
            mallets=mallets,
            note_density=note_density,
        )


class CelestaGenerator(_ChromaticPercussionBase):
    """
    Celesta Generator (GM program 8).
    Creates dreamy, bell-like, pearly high-register arpeggios or sparkling bell chords.
    """
    name: str = "Celesta Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "dreamy_arpeggio",  # dreamy_arpeggio, sparkling_chords
        pedal: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "celesta",
            params=params,
            pattern=pattern,
            pedal=pedal,
            note_density=note_density,
        )


class GlockenspielGenerator(_ChromaticPercussionBase):
    """
    Glockenspiel Generator (GM program 9).
    Renders extremely bright, high-pitched ringing bells, simple melodies, or sparkling runs.
    """
    name: str = "Glockenspiel Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "melodic_accent",  # melodic_accent, sparkling_run
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "glockenspiel",
            params=params,
            pattern=pattern,
            note_density=note_density,
        )


class MusicBoxGenerator(_ChromaticPercussionBase):
    """
    Music Box Generator (GM program 10).
    Renders clockwork mechanical ostinatos, slightly vintage, highly structured.
    """
    name: str = "Music Box Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "clockwork_ostinato",  # clockwork_ostinato, gentle_melody
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "music_box",
            params=params,
            pattern=pattern,
            note_density=note_density,
        )


class VibraphoneGenerator(_ChromaticPercussionBase):
    """
    Vibraphone Generator (GM program 11).
    Creates warm chords (up to 4 mallets), sustain pedaling, and motor vibrato sweeps.
    """
    name: str = "Vibraphone Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "warm_chords",  # warm_chords, motor_arpeggio
        motor_speed_hz: float = 6.0,   # motor tremolo speed
        pedal: bool = True,            # sustain pedaling (CC 64)
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "vibraphone",
            params=params,
            pattern=pattern,
            pedal=pedal,
            motor_speed_hz=motor_speed_hz,
            note_density=note_density,
        )


class MarimbaGenerator(_ChromaticPercussionBase):
    """
    Marimba Generator (GM program 12).
    Generates warm woody arpeggios, double strokes, or continuous rolling tremolos.
    """
    name: str = "Marimba Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "woody_arpeggio",  # woody_arpeggio, rolling_tremolo
        mallets: int = 4,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "marimba",
            params=params,
            pattern=pattern,
            mallets=mallets,
            note_density=note_density,
        )


class XylophoneGenerator(_ChromaticPercussionBase):
    """
    Xylophone Generator (GM program 13).
    Renders sharp, bright, dry staccato lines, rapid runs, or dry skeletal wood accents.
    """
    name: str = "Xylophone Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "dry_staccato_run",  # dry_staccato_run, skeletal_accents
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "xylophone",
            params=params,
            pattern=pattern,
            note_density=note_density,
        )


class DulcimerGenerator(_ChromaticPercussionBase):
    """
    Hammered Dulcimer Generator (GM program 15).
    Struck wire strings with hand-held mallets. Creates rapid rolls, ringing percussive arpeggios.
    """
    name: str = "Hammered Dulcimer Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "rapid_arpeggio",  # rapid_arpeggio, hammered_roll
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "dulcimer",
            params=params,
            pattern=pattern,
            note_density=note_density,
        )
