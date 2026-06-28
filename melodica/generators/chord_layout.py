# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
generators/chord_layout.py — Orchestral chord layout generator.
Generates voiced chord notes for a specific instrument track within an orchestral layout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.render_context import RenderContext
from melodica.composer.chord_voicing_layout import ChordVoicingLayout


@dataclass
class ChordLayoutGenerator(PhraseGenerator):
    """Orchestral chord layout generator.

    Voices chord progression across a list of instruments, returning only
    the notes for this track's instrument.
    """

    name: str = "Chord Layout Generator"
    instrument_name: str = "violin"
    instruments: list[str] = field(default_factory=lambda: ["double_bass", "cello", "viola", "violin"])
    primary_melody: list[NoteInfo] | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument_name: str = "violin",
        instruments: list[str] | None = None,
        primary_melody: list[NoteInfo] | None = None,
    ) -> None:
        super().__init__(params)
        self.instrument_name = instrument_name.lower()
        self.instruments = [inst.lower() for inst in (instruments or ["double_bass", "cello", "viola", "violin"])]
        self.primary_melody = primary_melody

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        layout = ChordVoicingLayout(instruments=self.instruments)
        voiced_map = layout.layout_progression(chords, self.primary_melody)

        # Return notes for our instrument
        notes = voiced_map.get(self.instrument_name, [])

        # Apply velocity scaling if dynamic tension is available
        return notes
