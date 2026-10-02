# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.plan — Compositional planning and form structure layer.

Houses album narrative workflows, section planning, continuous album
compilation, motif development, and formal architectural validation.
"""

from __future__ import annotations

from melodica.plan.album import (
    Mood,
    SectionProfile,
    SECTION_PROFILES,
    AlbumNarrative,
    detect_sections_intelligently,
    produce_album,
    compile_continuous_album,
    generate_narrative_motif,
)

__all__ = [
    "Mood",
    "SectionProfile",
    "SECTION_PROFILES",
    "AlbumNarrative",
    "detect_sections_intelligently",
    "produce_album",
    "compile_continuous_album",
    "generate_narrative_motif",
]
