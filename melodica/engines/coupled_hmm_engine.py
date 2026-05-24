# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
engines/coupled_hmm_engine.py — Adapter for CoupledHMMHarmonizer (Engine 4).
"""

from __future__ import annotations

from melodica.engines._adapter_utils import to_note_infos
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.types import ChordLabel, HarmonizationRequest


class CoupledHMMEngine:
    """Engine 4 — Hierarchical coupled HMM (Tymoczko/Newman)."""

    def __init__(self, **kwargs: object) -> None:
        self._hmm = CoupledHMMHarmonizer(**kwargs)

    def harmonize(self, req: HarmonizationRequest) -> list[ChordLabel]:
        notes = to_note_infos(req.melody)
        duration = max(n.start + n.duration for n in notes) if notes else 4.0
        return self._hmm.harmonize(notes, req.key, duration)
