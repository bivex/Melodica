# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/orchestral_score.py — Meta-generator for full orchestral scoring.

Knows all instrument families (strings, brass, woodwinds, choir, harp, percussion),
assigns generators by role/register, and manages texture density across sections.

This is the "composer's brain" — given a chord progression and structure,
it produces a complete multi-track orchestral arrangement.

Layer: Application / Domain (meta-generator)
Style: Classical, cinematic, film scoring, neoromantic.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


# ---------------------------------------------------------------------------
# Texture levels
# ---------------------------------------------------------------------------

class Texture:
    SOLO = "solo"           # 1 instrument
    CHAMBER = "chamber"     # 2-3 instruments
    SMALL_ENSEMBLE = "small"  # 4-6 instruments
    FULL = "full"           # tutti — all families
    THIN = "thin"           # 1-2 instruments, sparse


# ---------------------------------------------------------------------------
# Instrument roles in the orchestra
# ---------------------------------------------------------------------------

@dataclass
class _OrchestralVoice:
    """A single instrument track in the orchestral score."""
    name: str
    role: str           # "melody", "harmony", "bass", "pad", "countermelody", "fx"
    family: str         # "strings", "brass", "woodwinds", "choir", "harp", "percussion"
    generator: PhraseGenerator
    gm_program: int     # General MIDI program number
    default_pan: float   # -1.0 to 1.0

# GM program numbers for orchestral instruments
_GM = {
    "violin": 40, "viola": 41, "cello": 42, "contrabass": 43,
    "flute": 73, "oboe": 68, "clarinet": 71, "bassoon": 70,
    "french_horn": 60, "trumpet": 56, "trombone": 57, "tuba": 58,
    "choir_aahs": 52, "choir_oohs": 53,
    "harp": 46, "timpani": 47, "orchestral_hit": 55,
    "string_ensemble": 48, "brass_section": 61,
}

# Seating position → stereo pan (stage left to right)
_STAGE_PAN = {
    "violin":  -0.30,
    "viola":   -0.10,
    "cello":    0.15,
    "contrabass": 0.25,
    "flute":   -0.20,
    "oboe":    -0.05,
    "clarinet": 0.05,
    "bassoon":  0.20,
    "french_horn":  0.30,
    "trumpet": -0.15,
    "trombone": 0.10,
    "tuba":     0.20,
    "choir_aahs": 0.0,
    "choir_oohs": 0.0,
    "harp":    -0.35,
    "timpani":  0.00,
}


# ---------------------------------------------------------------------------
# Texture presets — which voices active at each level
# ---------------------------------------------------------------------------

_TEXTURE_VOICES = {
    Texture.SOLO: [
        ("violin", "melody"),
    ],
    Texture.CHAMBER: [
        ("violin", "melody"),
        ("cello", "bass"),
        ("viola", "harmony"),
    ],
    Texture.SMALL_ENSEMBLE: [
        ("violin", "melody"),
        ("viola", "harmony"),
        ("cello", "bass"),
        ("contrabass", "bass"),
        ("flute", "countermelody"),
        ("harp", "pad"),
    ],
    Texture.FULL: [
        ("violin", "melody"),
        ("viola", "harmony"),
        ("cello", "bass"),
        ("contrabass", "bass"),
        ("flute", "countermelody"),
        ("oboe", "countermelody"),
        ("clarinet", "harmony"),
        ("bassoon", "bass"),
        ("french_horn", "pad"),
        ("trumpet", "melody"),
        ("trombone", "harmony"),
        ("choir_aahs", "pad"),
        ("harp", "pad"),
    ],
    Texture.THIN: [
        ("violin", "melody"),
        ("cello", "bass"),
    ],
}


# ---------------------------------------------------------------------------
# Section-aware texture mapping
# ---------------------------------------------------------------------------

_SECTION_TEXTURES = {
    "intro": Texture.CHAMBER,
    "verse": Texture.SMALL_ENSEMBLE,
    "chorus": Texture.FULL,
    "bridge": Texture.CHAMBER,
    "outro": Texture.THIN,
    "interlude": Texture.CHAMBER,
    "build": Texture.SMALL_ENSEMBLE,
    "climax": Texture.FULL,
    "transition": Texture.CHAMBER,
    "solo": Texture.SOLO,
}


@dataclass
class _SectionMap:
    """Maps song sections to texture levels and articulation overrides."""
    name: str
    start_beat: float
    duration_beats: float
    texture: str = Texture.CHAMBER
    articulation_override: str | None = None


# ---------------------------------------------------------------------------
# Orchestral Score Generator
# ---------------------------------------------------------------------------

@dataclass
class OrchestralScoreGenerator(PhraseGenerator):
    """
    Meta-generator: produces a complete multi-track orchestral arrangement.

    Given a chord progression and optional section structure, generates
    per-instrument tracks with proper voicing, register, and texture control.

    sections:
        List of (name, start_beat, duration_beats) tuples.
        E.g. [("intro", 0, 16), ("verse", 16, 32), ("chorus", 48, 32)]
        If None, uses Texture.FULL for entire duration.

    texture:
        Default texture level when no section map is provided.

    Returns:
        This generator stores the multi-track result in self.tracks
        (dict[str, list[NoteInfo]]) and self.instruments (dict[str, int])
        after render(). The render() return value is the combined notes
        on a single track for backwards compatibility.

    Usage:
        score = OrchestralScoreGenerator(
            sections=[("intro", 0, 16), ("chorus", 16, 32)],
            texture="full",
        )
        all_notes = score.render(chords, key, duration)
        tracks = score.tracks       # per-instrument
        instruments = score.instruments  # GM programs
    """

    name: str = "Orchestral Score"

    sections: list[tuple[str, float, float]] = field(default_factory=list)
    texture: str = Texture.FULL
    include_choir: bool = True
    include_harp: bool = True
    include_brass: bool = True

    # Populated after render()
    tracks: dict[str, list[NoteInfo]] = field(default_factory=dict, init=False, repr=False)
    instruments: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    pan_map: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        sections: list[tuple[str, float, float]] | None = None,
        texture: str = Texture.FULL,
        include_choir: bool = True,
        include_harp: bool = True,
        include_brass: bool = True,
    ) -> None:
        super().__init__(params)
        self.sections = sections or []
        self.texture = texture
        self.include_choir = include_choir
        self.include_harp = include_harp
        self.include_brass = include_brass
        self.tracks = {}
        self.instruments = {}
        self.pan_map = {}

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        self.tracks = {}
        self.instruments = {}
        self.pan_map = {}

        # Build section map
        section_map = self._build_section_map(duration_beats)

        # For each section, determine active voices and render
        for sec in section_map:
            sec_chords = self._chords_in_range(chords, sec.start_beat, sec.duration_beats)
            if not sec_chords:
                continue

            voices = self._voices_for_texture(sec.texture)
            for inst_name, role in voices:
                # Skip disabled families
                if inst_name == "choir_aahs" and not self.include_choir:
                    continue
                if inst_name == "harp" and not self.include_harp:
                    continue
                if inst_name in ("french_horn", "trumpet", "trombone") and not self.include_brass:
                    continue

                gen = self._make_generator(inst_name, role, sec)
                if gen is None:
                    continue

                sec_notes = gen.render(sec_chords, key, sec.duration_beats)

                # Offset notes to section start
                for n in sec_notes:
                    n.shift_time(sec.start_beat)

                # Accumulate into tracks
                if inst_name not in self.tracks:
                    self.tracks[inst_name] = []
                self.tracks[inst_name].extend(sec_notes)

                self.instruments[inst_name] = _GM.get(inst_name, 48)
                if inst_name in _STAGE_PAN:
                    self.pan_map[inst_name] = _STAGE_PAN[inst_name]

        # Combine all notes for return value
        all_notes: list[NoteInfo] = []
        for track_notes in self.tracks.values():
            all_notes.extend(track_notes)
        all_notes.sort(key=lambda n: n.start)
        return all_notes

    def _build_section_map(self, total_duration: float) -> list[_SectionMap]:
        if not self.sections:
            return [_SectionMap("main", 0.0, total_duration, self.texture)]

        result = []
        for name, start, dur in self.sections:
            texture = _SECTION_TEXTURES.get(name, self.texture)
            result.append(_SectionMap(name, start, dur, texture))
        return result

    def _chords_in_range(
        self, chords: list[ChordLabel], start: float, dur: float,
    ) -> list[ChordLabel]:
        end = start + dur
        result: list[ChordLabel] = []
        for c in chords:
            if c.start + c.duration > start and c.start < end:
                # Shift start to be relative to section so sub-generators
                # see beats starting from 0.0
                shifted = ChordLabel(
                    root=c.root, quality=c.quality,
                    extensions=list(c.extensions) if c.extensions else [],
                    bass=c.bass, inversion=c.inversion,
                    start=c.start - start, duration=c.duration,
                    degree=c.degree, function=c.function,
                )
                result.append(shifted)
        return result

    def _voices_for_texture(self, texture: str) -> list[tuple[str, str]]:
        voices = list(_TEXTURE_VOICES.get(texture, _TEXTURE_VOICES[Texture.CHAMBER]))
        # Add some randomness for chamber/small — not always the same instruments
        if texture == Texture.CHAMBER and random.random() < 0.3:
            voices[0] = ("cello", "melody")  # cello solo instead of violin
        return voices

    def _make_generator(
        self, inst_name: str, role: str, section: _SectionMap,
    ) -> PhraseGenerator | None:
        """Create the appropriate generator for an instrument in a section."""
        from melodica.generators.orchestral_strings import (
            ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
        )
        from melodica.generators.orchestral_woodwinds import (
            FluteGenerator, OboeGenerator, ClarinetGenerator, BassoonGenerator,
        )
        from melodica.generators.orchestral_brass import (
            TrumpetGenerator, TromboneGenerator, FrenchHornGenerator,
        )
        from melodica.generators.orchestral_percussion import (
            TimpaniGenerator, MalletPercussionGenerator,
        )
        from melodica.generators.choir_ahhs import ChoirAahsGenerator
        from melodica.generators.harp import HarpGenerator

        # Determine articulation based on section + role
        art = self._articulation_for(section, role)
        dyn = self._dynamic_for(section)

        # --- Strings ---
        if inst_name == "violin":
            return ViolinGenerator(
                params=GeneratorParams(
                    density=self._role_density(role),
                    key_range_low=55, key_range_high=96,
                    complexity=self.params.complexity,
                    leap_probability=self.params.leap_probability,
                ),
                articulation=art,
                dynamic_curve=dyn,
            )

        if inst_name == "viola":
            return ViolaGenerator(
                params=GeneratorParams(
                    density=self._role_density(role),
                    key_range_low=48, key_range_high=84,
                    complexity=self.params.complexity * 0.8,
                    leap_probability=self.params.leap_probability * 0.7,
                ),
                articulation=art,
                dynamic_curve=dyn,
            )

        if inst_name == "cello":
            return CelloGenerator(
                params=GeneratorParams(
                    density=self._role_density(role),
                    key_range_low=36, key_range_high=72,
                    complexity=self.params.complexity * 0.7,
                    leap_probability=self.params.leap_probability * 0.5,
                ),
                articulation=art,
                dynamic_curve=dyn,
                bass_voice=(role == "bass"),
            )

        if inst_name == "contrabass":
            return ContrabassGenerator(
                params=GeneratorParams(
                    density=self._role_density(role),
                    key_range_low=28, key_range_high=55,
                    complexity=self.params.complexity * 0.5,
                    leap_probability=self.params.leap_probability * 0.3,
                ),
                articulation=art,
                dynamic_curve=dyn,
                bass_voice=True,
            )

        # --- Woodwinds ---
        if inst_name == "flute":
            return FluteGenerator(
                params=GeneratorParams(
                    density=self._role_density(role) * 0.7,
                    key_range_low=60, key_range_high=96,
                    complexity=self.params.complexity,
                    leap_probability=self.params.leap_probability * 0.8,
                ),
                articulation=art,
                dynamic_curve=dyn,
                vibrato=True,
            )

        if inst_name == "oboe":
            return OboeGenerator(
                params=GeneratorParams(
                    density=self._role_density(role) * 0.6,
                    key_range_low=58, key_range_high=91,
                    complexity=self.params.complexity * 0.8,
                    leap_probability=self.params.leap_probability * 0.6,
                ),
                articulation=art,
                dynamic_curve=dyn,
                vibrato=True,
            )

        if inst_name == "clarinet":
            return ClarinetGenerator(
                params=GeneratorParams(
                    density=self._role_density(role) * 0.6,
                    key_range_low=50, key_range_high=91,
                    complexity=self.params.complexity * 0.8,
                    leap_probability=self.params.leap_probability * 0.6,
                ),
                articulation=art,
                dynamic_curve=dyn,
                vibrato=False,
            )

        if inst_name == "bassoon":
            return BassoonGenerator(
                params=GeneratorParams(
                    density=self._role_density(role) * 0.5,
                    key_range_low=34, key_range_high=72,
                    complexity=self.params.complexity * 0.5,
                    leap_probability=self.params.leap_probability * 0.3,
                ),
                articulation=art,
                dynamic_curve=dyn,
                vibrato=False,
            )

        # --- Brass ---
        if inst_name == "french_horn":
            return FrenchHornGenerator(
                params=GeneratorParams(
                    density=self._role_density(role) * 0.4,
                    key_range_low=34, key_range_high=70,
                    complexity=self.params.complexity * 0.6,
                    leap_probability=self.params.leap_probability * 0.4,
                ),
                articulation=art,
                dynamic_curve=dyn,
            )

        if inst_name == "trumpet":
            return TrumpetGenerator(
                params=GeneratorParams(
                    density=self._role_density(role) * 0.6,
                    key_range_low=55, key_range_high=82,
                    complexity=self.params.complexity,
                    leap_probability=self.params.leap_probability * 0.7,
                ),
                articulation=art,
                dynamic_curve=dyn,
            )

        if inst_name == "trombone":
            return TromboneGenerator(
                params=GeneratorParams(
                    density=self._role_density(role) * 0.5,
                    key_range_low=40, key_range_high=70,
                    complexity=self.params.complexity * 0.7,
                    leap_probability=self.params.leap_probability * 0.4,
                ),
                articulation=art,
                dynamic_curve=dyn,
                bass_voice=(role == "bass"),
            )

        # --- Choir ---
        if inst_name == "choir_aahs":
            return ChoirAahsGenerator(
                params=GeneratorParams(
                    density=self._role_density(role) * 0.2,
                    key_range_low=48, key_range_high=79,
                ),
            )

        # --- Harp ---
        if inst_name == "harp":
            return HarpGenerator(
                params=GeneratorParams(
                    density=self._role_density(role) * 0.4,
                    key_range_low=24, key_range_high=91,
                ),
                pattern="arpeggio",
                direction=random.choice(["up", "up_down"]),
            )

        return None

    def _role_density(self, role: str) -> float:
        if role == "melody":
            return min(1.0, self.params.density * 1.3)
        elif role == "countermelody":
            return self.params.density * 0.7
        elif role == "bass":
            return self.params.density * 0.8
        elif role == "pad":
            return self.params.density * 0.3
        elif role == "harmony":
            return self.params.density * 0.5
        elif role == "fx":
            return self.params.density * 0.15
        return self.params.density

    def _articulation_for(self, section: _SectionMap, role: str) -> str:
        if section.articulation_override:
            return section.articulation_override

        if section.name in ("intro", "outro", "bridge"):
            return "legato"
        elif section.name in ("chorus", "climax"):
            if role == "melody":
                return "sustained"
            return "staccato" if role == "bass" else "sustained"
        elif section.name == "solo":
            return "legato"
        return "sustained"

    def _dynamic_for(self, section: _SectionMap) -> str:
        if section.name == "intro":
            return "crescendo"
        elif section.name == "outro":
            return "diminuendo"
        elif section.name == "chorus":
            return "swell"
        elif section.name == "bridge":
            return "flat"
        elif section.name == "climax":
            return "crescendo"
        return "flat"
