# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/_solo_base.py — Common base class for solo, acoustic, wind, and electronic instruments.

Layer: Application / Domain
"""

from __future__ import annotations

import random
from abc import ABC

from melodica.generators import PhraseGenerator
from melodica.generators.density import DensityStrategy
from melodica.types import ChordLabel


class _SoloInstrumentBase(PhraseGenerator, ABC):
    """Abstract base class for solo instruments with configurable velocity jitter and density."""

    note_density: float = 1.0

    def _apply_note_density(self, chords: list[ChordLabel]) -> list[ChordLabel]:
        return DensityStrategy.apply(chords, getattr(self, "note_density", 1.0))

    def _velocity(self, base_val: int, jitter: int = 8) -> int:
        if self.params.velocity_range:
            v_min, v_max = self.params.velocity_range
            return random.randint(v_min, v_max)
        return max(1, min(127, base_val + random.randint(-jitter, jitter)))
