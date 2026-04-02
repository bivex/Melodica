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
generators/phrase_container.py — PhraseContainer.

Combines multiple generators sequentially or in parallel.
Like a DAW track that layers different generators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import chord_at


@dataclass
class PhraseContainer(PhraseGenerator):
    """
    Combines multiple generators.

    mode:   "sequential" — generators play one after another
            "parallel"   — generators play simultaneously (layered)
    layers: list of (generator, duration_fraction) pairs
            duration_fraction: 0.0-1.0, portion of total duration (sequential only)
    """

    name: str = "Phrase Container"
    mode: str = "sequential"
    layers: list[tuple[PhraseGenerator, float]] = field(default_factory=list)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        mode: str = "sequential",
        layers: list[tuple[PhraseGenerator, float]] | None = None,
    ) -> None:
        super().__init__(params)
        if mode not in {"sequential", "parallel"}:
            raise ValueError(f"mode must be 'sequential' or 'parallel'; got {mode!r}")
        self.mode = mode
        self.layers = layers if layers is not None else []
        self._last_context: RenderContext | None = None

    def add(self, generator: PhraseGenerator, duration_fraction: float = 1.0) -> "PhraseContainer":
        """Add a generator to the container."""
        self.layers.append((generator, duration_fraction))
        return self

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords or not self.layers:
            return []

        all_notes: list[NoteInfo] = []
        last_chord = chords[-1]

        if self.mode == "sequential":
            # Normalize fractions
            total_frac = sum(f for _, f in self.layers)
            if total_frac <= 0:
                total_frac = len(self.layers)

            t = 0.0
            for gen, frac in self.layers:
                slot_dur = duration_beats * (frac / total_frac)
                if slot_dur <= 0:
                    continue
                # Get chords for this time slot
                slot_chords = [c for c in chords if c.start < t + slot_dur and c.end > t]
                if not slot_chords:
                    slot_chords = chords[:1]

                ctx = context if t == 0 else None
                notes = gen.render(slot_chords, key, slot_dur, ctx)
                # Offset notes to global time
                for n in notes:
                    all_notes.append(
                        NoteInfo(
                            pitch=n.pitch,
                            start=round(n.start + t, 6),
                            duration=n.duration,
                            velocity=n.velocity,
                        )
                    )
                t += slot_dur

        else:  # parallel
            for gen, _ in self.layers:
                notes = gen.render(chords, key, duration_beats, context)
                all_notes.extend(notes)

        # Sort by onset
        all_notes.sort(key=lambda n: n.start)

        if all_notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=all_notes[-1].pitch,
                last_velocity=all_notes[-1].velocity,
                last_chord=last_chord,
            )

        return all_notes
