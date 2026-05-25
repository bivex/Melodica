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

"""
rhythm/library.py — Preset Rhythm Library.

Contains standard 4/4 rhythms (straight, dotted, triplets, rests) loaded from JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Any
from melodica.rhythm import RhythmEvent, RhythmGenerator


@dataclass
class StaticRhythmGenerator(RhythmGenerator):
    """Simple generator that returns a fixed list of events, optionally looped."""
    events: list[RhythmEvent]
    loop: bool = True

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        if not self.events:
            return []
        
        # Calculate full pattern length from last event
        pattern_len = max((e.onset + e.duration for e in self.events), default=4.0)
        
        result = []
        t = 0.0
        while t < duration_beats:
            for e in self.events:
                onset = t + e.onset
                if onset >= duration_beats:
                    break
                duration = min(e.duration, duration_beats - onset)
                result.append(RhythmEvent(onset=onset, duration=duration, velocity_factor=e.velocity_factor))
            
            if not self.loop:
                break
            t += pattern_len
            
        return result


# ---------------------------------------------------------------------------
# Rhythm Presets Library (Loaded dynamically from JSON presets)
# ---------------------------------------------------------------------------

RHYTHM_LIBRARY: dict[str, list[RhythmEvent]] = {}
_RHYTHM_LOOP_PREFERENCE: dict[str, bool] = {}

# Registry for dynamic generators (Markov, Probabilistic, etc.)
DYNAMIC_RHYTHM_REGISTRY: dict[str, Callable[..., RhythmGenerator]] = {}


def register_dynamic_rhythm(name: str, factory: Callable[..., RhythmGenerator]):
    """Register a factory function for a dynamic rhythm generator."""
    DYNAMIC_RHYTHM_REGISTRY[name] = factory


def _load_file(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            events = [
                RhythmEvent(
                    onset=e["onset"],
                    duration=e["duration"],
                    velocity_factor=e.get("velocity_factor", 1.0)
                )
                for e in data.get("events", [])
            ]
            name = data.get("name", path.stem)
            RHYTHM_LIBRARY[name] = events
            
            # Map space-sanitized version
            sanitized = name.replace(" ", "_")
            RHYTHM_LIBRARY[sanitized] = events
            
            # Save loop preference
            loop = data.get("loop", True)
            _RHYTHM_LOOP_PREFERENCE[name] = loop
            _RHYTHM_LOOP_PREFERENCE[sanitized] = loop
    except Exception:
        pass


def _populate_library():
    # 1. Load packaged presets from inside the package distribution
    package_dir = Path(__file__).parent / "presets"
    if package_dir.is_dir():
        for path in package_dir.glob("*.json"):
            _load_file(path)
            
    # 2. Load project/cwd presets (can override packaged presets or define custom ones)
    cwd_dir = Path("presets/rhythms")
    if cwd_dir.is_dir():
        for path in cwd_dir.glob("*.json"):
            _load_file(path)
            
    # 3. Hardcoded fallback in case both directories are missing or unreadable
    if "straight_quarters" not in RHYTHM_LIBRARY:
        fallback_events = [RhythmEvent(float(i), 1.0) for i in range(4)]
        RHYTHM_LIBRARY["straight_quarters"] = fallback_events
        _RHYTHM_LOOP_PREFERENCE["straight_quarters"] = True

    # 4. Register standard dynamic rhythms
    from melodica.rhythm.markov_rhythm import MarkovRhythmGenerator
    from melodica.rhythm.probabilistic import ProbabilisticRhythmGenerator
    
    # Generic factories that pass through all kwargs
    register_dynamic_rhythm("markov", lambda **kw: MarkovRhythmGenerator(**kw))
    register_dynamic_rhythm("probabilistic", lambda **kw: ProbabilisticRhythmGenerator(**kw))

    # Named presets (can still be overridden by kwargs)
    register_dynamic_rhythm(
        "markov:syncopated", 
        lambda **kw: MarkovRhythmGenerator(**{"style": "straight", "syncopation": 0.3, "downbeat_preference": 0.2, **kw})
    )
    register_dynamic_rhythm(
        "markov:swing", 
        lambda **kw: MarkovRhythmGenerator(**{"style": "swing", "syncopation": 0.2, "phrase_length": 8, **kw})
    )
    register_dynamic_rhythm(
        "markov:ballad", 
        lambda **kw: MarkovRhythmGenerator(**{"style": "ballad", "syncopation": 0.1, **kw})
    )
    register_dynamic_rhythm(
        "probabilistic:dense", 
        lambda **kw: ProbabilisticRhythmGenerator(**{"grid_resolution": 0.25, "density": 0.55, "syncopation": 0.25, **kw})
    )
    register_dynamic_rhythm(
        "probabilistic:sparse", 
        lambda **kw: ProbabilisticRhythmGenerator(**{"grid_resolution": 0.5, "density": 0.3, "syncopation": 0.1, **kw})
    )


# Populate library on module load
_populate_library()


def get_rhythm(name: str, **kwargs) -> RhythmGenerator:
    """
    Helper to get a generator for a named preset.
    
    Supports:
    1. Static presets (from JSON files or RHYTHM_LIBRARY)
    2. Dynamic presets (starting with 'markov:', 'probabilistic:', etc.)
    """
    # Check dynamic registry first
    if name in DYNAMIC_RHYTHM_REGISTRY:
        return DYNAMIC_RHYTHM_REGISTRY[name](**kwargs)

    # Fallback to static library
    events = RHYTHM_LIBRARY.get(name)
    if events is None:
        # Fallback to straight_quarters
        events = RHYTHM_LIBRARY.get("straight_quarters")
        loop = True
    else:
        loop = _RHYTHM_LOOP_PREFERENCE.get(name, True)
        
    return StaticRhythmGenerator(events=events, loop=loop)
