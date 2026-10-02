# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/wind_brass_solo.py — Professional register-aware solo winds and brass.

Layer 2/3: Muted Trumpet, Synth Brass 1 & 2, Piccolo, Recorder, Pan Flute,
Blown Bottle, Shakuhachi, Whistle, Ocarina, Flugelhorn, English Horn,
Bass Clarinet, Euphonium, and Alto Flute.
Refactored to inherit from WindBrassFamily, backed by Layer 1 TOML profiles and kernel functions.
"""

from __future__ import annotations

from abc import ABC

from melodica.generate.family import WindBrassFamily
from melodica.generators import GeneratorParams
from melodica.generators._solo_base import _SoloInstrumentBase


class _WindBrassSoloBase(WindBrassFamily, _SoloInstrumentBase, ABC):
    """Abstract base class for solo winds and brass generators."""

    def __init__(
        self,
        profile_or_params: str | InstrumentProfile | GeneratorParams | None = None,
        params: GeneratorParams | None = None,
        *,
        brass_type: str | None = None,
        instrument: str | None = None,
        plunger_wah: bool = True,
        breath_vibrato: bool = True,
        vibrato: bool = True,
        harmony_count: int = 3,
        note_density: float = 1.0,
    ) -> None:
        if isinstance(profile_or_params, GeneratorParams):
            actual_params = profile_or_params
            actual_profile = None
        elif isinstance(profile_or_params, str) or hasattr(profile_or_params, "id"):
            actual_profile = profile_or_params
            actual_params = params
        else:
            actual_profile = None
            actual_params = params

        super().__init__(
            profile=actual_profile,
            params=actual_params,
            brass_type=brass_type,
            instrument=instrument,
            plunger_wah=plunger_wah,
            breath_vibrato=breath_vibrato,
            vibrato=vibrato,
            harmony_count=harmony_count,
            note_density=note_density,
        )


class MutedTrumpetGenerator(_WindBrassSoloBase):
    """
    Muted Trumpet Generator (GM 59).
    Simulates a jazz/cinematic harmon muted trumpet with plunge wah-wah plunger sweeps.
    """
    name: str = "Muted Trumpet Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        plunger_wah: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "muted_trumpet",
            params=params,
            plunger_wah=plunger_wah,
            note_density=note_density,
        )
        self.plunger_wah = plunger_wah
        self.note_density = note_density


class SynthBrassGenerator(_WindBrassSoloBase):
    """
    Synth Brass 1 & 2 Generator (GM 62, 63).
    Classic analog polyphonic synth brass with rapid brass envelope snaps.
    """
    name: str = "Synth Brass Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        brass_type: str = "synth_brass_1",  # synth_brass_1, synth_brass_2
        harmony_count: int = 3,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            brass_type,
            params=params,
            brass_type=brass_type,
            harmony_count=harmony_count,
            note_density=note_density,
        )
        self.brass_type = brass_type
        self.harmony_count = max(2, min(4, harmony_count))
        self.note_density = note_density


class WoodwindSoloGenerator(_WindBrassSoloBase):
    """
    Woodwind Solo Generator covering Piccolo (72), Recorder (74), Pan Flute (75),
    Blown Bottle (76), Shakuhachi (77), Whistle (78), and Ocarina (79).
    """
    name: str = "Woodwind Solo Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "recorder",  # piccolo, recorder, pan_flute, blown_bottle, shakuhachi, whistle, ocarina
        breath_vibrato: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            instrument,
            params=params,
            instrument=instrument,
            breath_vibrato=breath_vibrato,
            note_density=note_density,
        )
        self.instrument = instrument
        self.breath_vibrato = breath_vibrato
        self.note_density = note_density


class FlugelhornGenerator(_WindBrassSoloBase):
    """
    Flugelhorn Generator.
    Simulates a warm, lyrical jazz ballad flugelhorn with soft attacks
    and gentle vibrato expression sweeps.
    """
    name: str = "Flugelhorn Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        breath_vibrato: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "flugelhorn",
            params=params,
            breath_vibrato=breath_vibrato,
            note_density=note_density,
        )
        self.breath_vibrato = breath_vibrato
        self.note_density = note_density


class EnglishHornGenerator(_WindBrassSoloBase):
    """
    English Horn (Cor Anglais) Generator.
    Produces a warm, melancholy, lyrical alto oboe line.
    """
    name: str = "English Horn"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        vibrato: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "english_horn",
            params=params,
            vibrato=vibrato,
            note_density=note_density,
        )
        self.vibrato = vibrato
        self.note_density = note_density


class BassClarinetGenerator(_WindBrassSoloBase):
    """
    Bass Clarinet Generator.
    Low register warm woodwind generator.
    """
    name: str = "Bass Clarinet"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "bass_clarinet",
            params=params,
            note_density=note_density,
        )
        self.note_density = note_density


class EuphoniumGenerator(_WindBrassSoloBase):
    """
    Euphonium (Baritone Horn) Generator.
    Produces warm, resonant low brass solo lines with slow, swelling marcato dynamics.
    """
    name: str = "Euphonium Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "euphonium",
            params=params,
            note_density=note_density,
        )
        self.note_density = note_density


class AltoFluteGenerator(_WindBrassSoloBase):
    """
    Alto Flute Generator.
    Produces low, breathy woodwind tones with gentle pitch vibrato sweeps.
    """
    name: str = "Alto Flute"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        breath_vibrato: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "alto_flute",
            params=params,
            breath_vibrato=breath_vibrato,
            note_density=note_density,
        )
        self.breath_vibrato = breath_vibrato
        self.note_density = note_density
