# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
composer/chord_enrichers.py — Pluggable progression enrichers.
These transform a generated list of ChordLabels before track rendering.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from melodica.types import ChordLabel, Scale, HarmonicFunction, Quality, Mode

if TYPE_CHECKING:
    from melodica.idea_tool import IdeaPart

logger = logging.getLogger(__name__)


def applied_dominant_enricher(
    chords: list[ChordLabel], parts: list[IdeaPart]
) -> list[ChordLabel]:
    """
    Applied (secondary) dominant enricher:
    Before a target diatonic major/minor chord (ii, iii, IV, V, vi in major; III, iv, V, VI, VII in minor),
    inserts its secondary dominant (V7 of the target) by splitting the second half of the
    preceding chord's duration.
    """
    if not chords:
        return chords

    # Find fallback scale
    fallback_scale = None
    for part in parts:
        if part.scale is not None:
            fallback_scale = part.scale
            break
    if fallback_scale is None:
        fallback_scale = Scale(root=0, mode=Mode.MAJOR)

    # Build part intervals
    part_intervals = []
    current_beat = 0.0
    for part in parts:
        bars = part.bars if part.bars is not None else 8
        time_sig = part.time_signature or (4, 4)
        part_beats = bars * time_sig[0]
        part_intervals.append((current_beat, current_beat + part_beats, part.scale))
        current_beat += part_beats

    def get_scale_at(beat: float) -> Scale:
        for start, end, sc in part_intervals:
            if start <= beat < end and sc is not None:
                return sc
        return fallback_scale

    enriched: list[ChordLabel] = []
    for c in chords:
        # Copy to avoid mutating original chord definitions globally
        c_copy = ChordLabel(
            root=c.root,
            quality=c.quality,
            extensions=list(c.extensions),
            bass=c.bass,
            inversion=c.inversion,
            start=c.start,
            duration=c.duration,
            degree=c.degree,
            function=c.function,
        )

        if enriched:
            prev = enriched[-1]
            scale = get_scale_at(c_copy.start)
            scale_pcs = {int(round(d)) % 12 for d in scale.degrees()}
            is_diatonic = (c_copy.root % 12) in scale_pcs
            is_tonic = (c_copy.root % 12) == (scale.root % 12)

            is_target = (
                is_diatonic
                and not is_tonic
                and not c_copy.quality.is_diminished
            )

            # Check if preceding chord can be split
            can_split = prev.duration >= 2.0

            # Check if preceding is already the secondary dominant
            sec_root = (c_copy.root + 7) % 12
            is_already_sec = (prev.root == sec_root and prev.quality == Quality.DOMINANT7)

            if is_target and can_split and not is_already_sec:
                # Split prev chord
                d_sec = 2.0 if prev.duration >= 4.0 else prev.duration / 2.0
                prev.duration -= d_sec

                # Insert secondary dominant
                sec_dom = ChordLabel(
                    root=sec_root,
                    quality=Quality.DOMINANT7,
                    start=prev.start + prev.duration,
                    duration=d_sec,
                    function=HarmonicFunction.DOMINANT,
                )
                enriched.append(sec_dom)

        enriched.append(c_copy)

    return enriched
