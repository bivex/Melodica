# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Shared helpers for engine adapters."""

from __future__ import annotations

from melodica.types import NoteInfo


def to_note_infos(melody: list) -> list[NoteInfo]:
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
