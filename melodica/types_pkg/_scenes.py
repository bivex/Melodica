# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-21
# Last Updated: 2026-05-21
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
types_pkg/_scenes.py — Scene, SceneTransition, SceneGraph.

Scene is a self-contained musical unit with its own key, BPM, mood,
and tracks. SceneGraph links scenes into a directed graph with transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from melodica.types import ChordLabel, NoteInfo, Scale


class TransitionType(Enum):
    CUT = "cut"
    FADE = "fade"
    CROSSFADE = "crossfade"
    MODULATION = "modulation"


@dataclass
class Scene:
    """Self-contained musical unit with its own harmonic/tempo context."""

    id: str
    label: str
    key: "Scale"
    bpm: float
    mood: str
    time_signature: tuple[int, int] = (4, 4)
    progression: list["ChordLabel"] | None = None
    tracks: dict[str, list["NoteInfo"]] | None = None
    duration_bars: int = 8
    tags: list[str] = field(default_factory=list)
    section_type: str = "verse"

    @property
    def duration_beats(self) -> float:
        """Total duration in beats."""
        return self.duration_bars * self.time_signature[0]

    @property
    def duration_seconds(self) -> float:
        """Approximate duration in seconds at this scene's BPM."""
        return self.duration_beats / (self.bpm / 60.0)


@dataclass
class SceneTransition:
    """Transition specification between two scenes."""

    from_scene: str
    to_scene: str
    type: TransitionType = TransitionType.CUT
    duration_bars: float = 0.0
    pivot_chord: "ChordLabel | None" = None


@dataclass
class SceneGraph:
    """
    Directed graph of scenes with transitions.

    default_order defines playback sequence (scenes may repeat).
    transitions list provides per-pair transition specs.
    """

    scenes: dict[str, "Scene"]
    default_order: list[str]
    transitions: list["SceneTransition"] = field(default_factory=list)

    def __post_init__(self) -> None:
        missing = [s for s in self.default_order if s not in self.scenes]
        if missing:
            raise ValueError(f"Unknown scene IDs in default_order: {missing}")

    def get_transition(self, from_id: str, to_id: str) -> "SceneTransition | None":
        """Look up transition spec for a pair of adjacent scenes."""
        for t in self.transitions:
            if t.from_scene == from_id and t.to_scene == to_id:
                return t
        return None

    def ordered_scenes(self) -> list["Scene"]:
        """Return scenes in default_order."""
        return [self.scenes[sid] for sid in self.default_order]
