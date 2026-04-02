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
modifiers/dynamic.py -- Dynamic Variations.

Layer: Application / Domain
"""

from __future__ import annotations

from dataclasses import dataclass

from melodica.modifiers import ModifierContext, PhraseModifier
from melodica.types import NoteInfo


@dataclass
class VelocityScalingModifier(PhraseModifier):
    """
    Scales and shifts note velocities globally.
    value = clamp(velocity * scale + add_val, 1, 127)
    """
    scale: float = 1.0
    add_val: int = 0

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        result = []
        for n in notes:
            new_vel = int(n.velocity * self.scale + self.add_val)
            new_vel = max(1, min(127, new_vel))

            result.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=new_vel,
                absolute=n.absolute,
            ))
        return result


@dataclass
class CrescendoModifier(PhraseModifier):
    """
    Applies a linear velocity ramp across the phrase duration.
    """
    start_vel: int = 40
    end_vel: int = 100

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes:
            return []

        total_len = max((n.start + n.duration for n in notes), default=1.0)
        total_len = max(total_len, 0.001)

        result = []
        for n in notes:
            progress = n.start / total_len
            progress = max(0.0, min(1.0, progress))
            new_vel = int(self.start_vel + (self.end_vel - self.start_vel) * progress)
            new_vel = max(1, min(127, new_vel))

            result.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=new_vel,
                absolute=n.absolute,
            ))
        return result


@dataclass
class SectionIntensityModifier(PhraseModifier):
    """
    Applies a dynamic intensity arc across sections of the composition.

    Takes a map of (start_beat, end_beat) -> intensity (0.0 to 1.0) and
    scales velocities to create natural dynamics:
    Intro quiet, Climax loud, Outro quiet.

    Usage:
        modifier = SectionIntensityModifier.from_labels([
            ("Intro",   0,  16, 0.3),
            ("Build",  16,  48, 0.7),
            ("Climax", 48,  64, 1.0),
            ("Outro",  64,  80, 0.4),
        ])
    """
    sections: dict[tuple[float, float], float]  # (start, end) -> intensity 0.0-1.0
    velocity_scale: float = 127.0

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if not notes or not self.sections:
            return notes

        result = []
        for n in notes:
            intensity = self._intensity_at(n.start)
            ratio = n.velocity / 127.0
            new_vel = int(self.velocity_scale * ratio * intensity)
            new_vel = max(1, min(127, new_vel))

            result.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=new_vel,
                absolute=n.absolute,
            ))
        return result

    def _intensity_at(self, beat: float) -> float:
        """Find the intensity value for a given beat position."""
        for (start, end), intensity in self.sections.items():
            if start <= beat < end:
                return max(0.05, min(1.0, intensity))
        # Fallback: find nearest section
        best_dist = float("inf")
        best_intensity = 1.0
        for (start, end), intensity in self.sections.items():
            mid = (start + end) / 2.0
            dist = abs(beat - mid)
            if dist < best_dist:
                best_dist = dist
                best_intensity = intensity
        return max(0.05, min(1.0, best_intensity))

    @classmethod
    def from_labels(
        cls,
        labels: list[tuple[str, float, float, float]],
        velocity_scale: float = 127.0,
    ) -> "SectionIntensityModifier":
        """
        Build from human-readable labels.

        Args:
            labels: list of (name, start_beat, end_beat, intensity)
        """
        sections = {(start, end): intensity for _, start, end, intensity in labels}
        return cls(sections=sections, velocity_scale=velocity_scale)
