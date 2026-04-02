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
rhythm/motif.py — MotifRhythmGenerator.

Layer: Application / Domain
"""

from __future__ import annotations

import typing
from dataclasses import dataclass

from melodica.rhythm import RhythmEvent, RhythmGenerator


@dataclass
class MotifRhythmGenerator(RhythmGenerator):
    """
    Takes an inner rhythm generator and loops its output every `motif_length` beats.
    This creates consistent rhythmic structures like (AA-AA).
    """

    inner: RhythmGenerator
    motif_length: float = 4.0

    def __init__(self, inner: RhythmGenerator, motif_length: float = 4.0) -> None:
        super().__init__()
        self.inner = inner
        self.motif_length = max(0.1, motif_length)

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        # Generate the single motif pattern
        motif_events = self.inner.generate(self.motif_length)

        # In case the inner generator doesn't strictly adhere to motif_length,
        # we filter out any events that start beyond it
        motif_events = [e for e in motif_events if e.onset < self.motif_length]

        all_events = []
        current_offset = 0.0

        while current_offset < duration_beats:
            for event in motif_events:
                onset = current_offset + event.onset
                if onset >= duration_beats:
                    break

                # 1. Truncate to total duration
                # 2. ALSO truncate to motif boundary so events don't leak into next cycle
                max_dur_in_motif = self.motif_length - event.onset
                max_dur_total = duration_beats - onset
                dur = min(event.duration, max_dur_in_motif, max_dur_total)

                all_events.append(
                    RhythmEvent(
                        onset=round(onset, 6),
                        duration=round(dur, 6),
                        velocity_factor=event.velocity_factor,
                    )
                )

            current_offset += self.motif_length

        return all_events
