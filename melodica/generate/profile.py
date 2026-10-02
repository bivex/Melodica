# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.generate.profile — Declarative instrument profiles and configuration loader.

Layer 1 of the architecture: instrument capabilities as data (physical ranges, GM programs,
articulations, sustain behaviours, default velocities and parameters) rather than code.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_NOTE_NAMES = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def parse_pitch(val: int | str) -> int:
    """
    Parse a pitch specification into a MIDI note number (0..127).
    Accepts integers (e.g. 60) or standard musical strings (e.g. 'C4', 'Eb3', 'F#5', 'B-flat5').
    """
    if isinstance(val, int):
        return max(0, min(127, val))

    s = str(val).strip()
    if s.isdigit():
        return max(0, min(127, int(s)))

    # Parse letter, accidental, octave
    m = re.match(r"^([a-gA-G])([#b♯♭]|-flat|-sharp)?(-?\d+)$", s)
    if not m:
        raise ValueError(f"Invalid pitch representation: {val!r}")

    letter = m.group(1).lower()
    acc = m.group(2) or ""
    octave = int(m.group(3))

    semitone = _NOTE_NAMES[letter]
    if acc in ("#", "♯", "-sharp"):
        semitone += 1
    elif acc in ("b", "♭", "-flat"):
        semitone -= 1

    midi_pitch = (octave + 1) * 12 + semitone
    return max(0, min(127, midi_pitch))


@dataclass(frozen=True)
class InstrumentProfile:
    """
    Data profile defining physical instrument constraints, MIDI mappings, and defaults.
    """
    id: str
    family: str
    gm_program: int
    range_low: int
    range_high: int
    name: str = ""
    max_polyphony: int = 4
    default_pattern: str = ""
    sustain_pedal: bool = False
    sustain_factor: float = 1.0
    base_velocity: int = 70
    velocity_jitter: int = 8
    articulations: dict[str, Any] = field(default_factory=dict)
    features: dict[str, Any] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            object.__setattr__(self, "name", self.id.replace("_", " ").title())

    def pitch_in_range(self, pitch: int) -> bool:
        """Check whether pitch is within the physical instrument range."""
        return self.range_low <= pitch <= self.range_high


# Search paths for instrument TOML files
_DEFAULT_SEARCH_PATHS: list[Path] = [
    Path("instruments"),
    Path(__file__).parent.parent / "data" / "instruments",
    Path.home() / ".melodica" / "instruments",
]


def load_profile_from_dict(data: dict[str, Any]) -> InstrumentProfile:
    """Instantiate an InstrumentProfile from a parsed dictionary."""
    inst_id = data.get("id") or data.get("name", "unknown").lower().replace(" ", "_")
    family = data.get("family", "generic")
    gm_program = int(data.get("gm_program", 0))

    # Parse range: can be table { low = ..., high = ... } or tuple/list [low, high]
    raw_range = data.get("range", {})
    if isinstance(raw_range, dict):
        low = parse_pitch(raw_range.get("low", 48))
        high = parse_pitch(raw_range.get("high", 84))
    elif isinstance(raw_range, (list, tuple)) and len(raw_range) >= 2:
        low = parse_pitch(raw_range[0])
        high = parse_pitch(raw_range[1])
    else:
        low, high = 48, 84

    # Sustain settings
    raw_sustain = data.get("sustain", {})
    if isinstance(raw_sustain, dict):
        sustain_pedal = bool(raw_sustain.get("pedal", False))
        sustain_factor = float(raw_sustain.get("factor", 1.0))
    elif isinstance(raw_sustain, bool):
        sustain_pedal = raw_sustain
        sustain_factor = 1.6 if raw_sustain else 0.8
    else:
        sustain_pedal = False
        sustain_factor = 1.0

    return InstrumentProfile(
        id=inst_id,
        family=family,
        name=data.get("name", ""),
        gm_program=gm_program,
        range_low=low,
        range_high=high,
        max_polyphony=int(data.get("max_polyphony", 4)),
        default_pattern=str(data.get("default_pattern", "")),
        sustain_pedal=sustain_pedal,
        sustain_factor=sustain_factor,
        base_velocity=int(data.get("base_velocity", 70)),
        velocity_jitter=int(data.get("velocity_jitter", 8)),
        articulations=dict(data.get("articulations", {})),
        features=dict(data.get("features", {})),
        defaults=dict(data.get("defaults", {})),
    )


def load_profile(source: str | Path | dict[str, Any]) -> InstrumentProfile:
    """
    Load an instrument profile from a TOML file path, raw string, ID, or dictionary.
    """
    if isinstance(source, dict):
        return load_profile_from_dict(source)

    if isinstance(source, Path) or (isinstance(source, str) and (source.endswith(".toml") or "/" in source)):
        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(f"Instrument profile file not found: {path}")
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return load_profile_from_dict(data)

    # Otherwise treat as instrument ID (e.g. 'vibraphone')
    return get_profile(str(source))


def get_profile(instrument_id: str, search_paths: list[Path] | None = None) -> InstrumentProfile:
    """Find and load an instrument profile by ID across search paths."""
    clean_id = instrument_id.lower().strip().replace(" ", "_")
    paths = search_paths or _DEFAULT_SEARCH_PATHS

    for base in paths:
        candidate = base / f"{clean_id}.toml"
        if candidate.is_file():
            with open(candidate, "rb") as f:
                data = tomllib.load(f)
            return load_profile_from_dict(data)

    raise KeyError(f"Instrument profile '{instrument_id}' not found in search paths: {[str(p) for p in paths]}")


def list_profiles(search_paths: list[Path] | None = None) -> list[str]:
    """List all available instrument profile IDs found across search paths."""
    paths = search_paths or _DEFAULT_SEARCH_PATHS
    found = set()
    for base in paths:
        if base.is_dir():
            for p in base.glob("*.toml"):
                found.add(p.stem)
    return sorted(found)
