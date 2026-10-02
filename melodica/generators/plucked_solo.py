# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/plucked_solo.py — Plucked and percussive solo instruments.

Layer 2/3: Piano, Harpsichord, Clavinet, Acoustic & Electric Guitars, Sitar, Koto, and Kalimba.
Refactored to inherit from PluckedFamily, backed by Layer 1 TOML profiles and kernel functions.
"""

from __future__ import annotations

from abc import ABC

from melodica.generate.family import PluckedFamily
from melodica.generators import GeneratorParams
from melodica.generators._solo_base import _SoloInstrumentBase


class _PluckedSoloBase(PluckedFamily, _SoloInstrumentBase, ABC):
    """Abstract base class for all plucked and percussive solo generators."""

    def __init__(
        self,
        profile_or_params: str | InstrumentProfile | GeneratorParams | None = None,
        params: GeneratorParams | None = None,
        *,
        style: str | None = None,
        pedal: bool | None = None,
        acoustic_type: str | None = None,
        pop_intensity: float | None = None,
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
            style=style,
            pedal=pedal,
            acoustic_type=acoustic_type,
            pop_intensity=pop_intensity,
            note_density=note_density,
        )


class PianoSoloGenerator(_PluckedSoloBase):
    """
    Solo Piano & Harpsichord generator.
    Covers Acoustic Grand (0), Bright Acoustic (1), Electric Grand (2), Honky-tonk (3),
    Electric Piano 1 (4), Electric Piano 2 (5), Harpsichord (6), Clavinet (7).
    """
    name: str = "Piano Solo Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "grand_piano",
        pedal: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            instrument,
            params=params,
            pedal=pedal,
            note_density=note_density,
        )
        self.instrument = instrument
        self.pedal = pedal
        self.note_density = note_density


class AcousticGuitarGenerator(_PluckedSoloBase):
    """
    Solo Acoustic & Electric Guitar generator.
    Covers Nylon (24), Steel (25), Jazz (26), Clean Electric (27), Muted (28),
    Overdriven (29), Distortion (30), Guitar Harmonics (31).
    """
    name: str = "Acoustic Guitar Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "fingerpicking",
        acoustic_type: str = "nylon",
        note_density: float = 1.0,
    ) -> None:
        profile_map = {
            "nylon": "nylon_guitar",
            "steel": "steel_guitar",
            "clean_electric": "clean_electric_guitar",
            "muted": "muted_guitar",
            "overdriven": "overdriven_guitar",
            "distortion": "distortion_guitar",
            "harmonics": "guitar_harmonics",
        }
        profile_id = profile_map.get(acoustic_type, "nylon_guitar")
        super().__init__(
            profile_id,
            params=params,
            style=style,
            acoustic_type=acoustic_type,
            note_density=note_density,
        )
        self.style = style
        self.acoustic_type = acoustic_type
        self.note_density = note_density


class EthnicPluckedGenerator(_PluckedSoloBase):
    """
    Solo World & Ethnic Plucked generator.
    Covers Sitar (104), Koto (107), Kalimba (108).
    """
    name: str = "Ethnic Plucked Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "sitar",
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            instrument,
            params=params,
            note_density=note_density,
        )
        self.instrument = instrument
        self.note_density = note_density


class KalimbaGenerator(_PluckedSoloBase):
    """
    Kalimba Generator (African Mbira).
    Produces plucked thumb piano notes with metallic pop transients.
    """
    name: str = "Kalimba Solo"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pop_intensity: float = 0.5,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(
            "kalimba",
            params=params,
            pop_intensity=pop_intensity,
            note_density=note_density,
        )
        self.pop_intensity = max(0.0, min(1.0, pop_intensity))
        self.note_density = note_density
