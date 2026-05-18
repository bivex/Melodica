"""Melody ornamentation — grace notes and embellishments.

Responsibilities:
  - Add grace notes before strong beats based on ornament_probability
  - Approach tone selection from scale degrees
"""

from __future__ import annotations

import random

from melodica.types import NoteInfo, Scale


class OrnamentProcessor:
    """Adds ornamental grace notes to melody notes."""

    def __init__(self, ornament_probability: float = 0.0) -> None:
        self.ornament_probability = max(0.0, min(1.0, ornament_probability))

    def add_ornaments(
        self, notes: list[NoteInfo], key: Scale, low: int, high: int, drama: DramaticArc | None = None
    ) -> list[NoteInfo]:
        """Add grace notes before strong beats."""
        if not notes or (self.ornament_probability <= 0 and (not drama or drama.shape == "none")):
            return notes

        scale_pcs = set(key.degrees())
        result: list[NoteInfo] = []

        for note in notes:
            is_strong = note.start % 1.0 < 0.15
            
            # Drama-aware ornament probability
            eff_prob = self.ornament_probability
            if drama:
                # More ornaments at high tension
                eff_prob = min(0.8, eff_prob + drama.tension(note.start) * 0.3)

            if is_strong and random.random() < eff_prob:
                approach_above = random.random() < 0.5
                for offset in [2, 1, 3]:  # try m2, M2, m3
                    grace_pc = (note.pitch + offset * (1 if approach_above else -1)) % 12
                    if grace_pc in scale_pcs:
                        grace_pitch = note.pitch + offset * (1 if approach_above else -1)
                        if low <= grace_pitch <= high:
                            grace_start = max(0, note.start - 0.125)
                            result.append(
                                NoteInfo(
                                    pitch=grace_pitch,
                                    start=round(grace_start, 6),
                                    duration=0.0625,
                                    velocity=max(1, int(note.velocity * 0.6)),
                                )
                            )
                        break
            result.append(note)

        result.sort(key=lambda n: n.start)
        return result
