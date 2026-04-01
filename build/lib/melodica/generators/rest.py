"""
generators/rest.py — Rest Generator (Silence).

Layer: Application / Domain
Outputs an empty note list. Useful for structural breaks or empty bars in arrangements.
"""

from __future__ import annotations

from dataclasses import dataclass
from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica import types


@dataclass
class RestGenerator(PhraseGenerator):
    """
    The ultimate generator: Silence.
    Good for creating placeholders, structural breaks, or "air" in the arrangement.
    """

    name: str = "Rest Generator"

    def render(
        self,
        chords: list[types.ChordLabel],
        key: types.Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[types.NoteInfo]:
        # Silence is golden.
        return []
