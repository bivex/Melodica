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
engines/hmm_engine.py — Adapter for HMMHarmonizer to engine protocol.
"""

from __future__ import annotations

from melodica.harmonize.advanced import HMM2Harmonizer
from melodica.types import ChordLabel, HarmonizationRequest, NoteInfo


class HMMEngine:
    """HMM-based harmonization engine (pro level with cadences and functional layer)."""

    def __init__(
        self,
        melody_weight: float = 0.30,
        voice_weight: float = 0.25,
        transition_weight: float = 0.25,
    ) -> None:
        self._hmm = HMM2Harmonizer(
            melody_weight=melody_weight,
            functional_weight=voice_weight,
            transition_weight=transition_weight,
        )

    def harmonize(self, req: HarmonizationRequest) -> list[ChordLabel]:
        notes = _to_note_infos(req.melody)
        duration = max(n.start + n.duration for n in notes) if notes else 4.0
        chords = self._hmm.harmonize(notes, req.key, duration)
        if req.chord_rhythm != 4.0 and chords:
            chords = self._resample(chords, req.chord_rhythm, duration)
        return chords

    def _resample(
        self, chords: list[ChordLabel], new_rhythm: float, duration: float
    ) -> list[ChordLabel]:
        result = []
        t = 0.0
        idx = 0
        while t < duration and idx < len(chords):
            for c in chords:
                if c.start <= t < c.start + c.duration:
                    result.append(
                        ChordLabel(
                            root=c.root,
                            quality=c.quality,
                            start=round(t, 6),
                            duration=round(new_rhythm, 6),
                            degree=c.degree,
                            function=c.function,
                        )
                    )
                    break
            t += new_rhythm
            idx += 1
        return result


def _to_note_infos(melody: list) -> list[NoteInfo]:
    """Convert list[Note] to list[NoteInfo], handling both types safely."""
    if not melody:
        return []
    result = []
    for n in melody:
        if isinstance(n, NoteInfo):
            result.append(n)
        else:
            result.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=getattr(n, "velocity", 64),
                )
            )
    return result
