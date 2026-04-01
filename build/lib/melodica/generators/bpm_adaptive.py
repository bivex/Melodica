"""
generators/bpm_adaptive.py — BPM-adaptive pattern density generator.

Layer: Application / Domain
Style: All genres.

Wraps any other generator and adapts note density based on BPM.
At higher BPMs, reduces density; at lower BPMs, increases it.
This prevents patterns from sounding too sparse at slow tempos
or too cluttered at fast tempos.

Scaling modes:
    "linear"       — density scales inversely with BPM
    "logarithmic"  — logarithmic scaling (smoother)
    "genre_safe"   — genre-aware scaling with sensible defaults
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale


@dataclass
class BPMAdaptiveGenerator(PhraseGenerator):
    """
    BPM-adaptive pattern density wrapper.

    Wraps another generator and adjusts output density based on BPM.

    wrapped_generator:
        The inner generator to adapt.
    bpm:
        Current BPM of the track.
    reference_bpm:
        BPM at which the inner generator produces optimal density (default 120).
    scaling_mode:
        "linear", "logarithmic", "genre_safe"
    min_density:
        Minimum output density factor (0.0-1.0).
    max_density:
        Maximum output density factor (0.0-1.0).
    """

    name: str = "BPM Adaptive Generator"
    wrapped_generator: PhraseGenerator | None = None
    bpm: float = 120.0
    reference_bpm: float = 120.0
    scaling_mode: str = "logarithmic"
    min_density: float = 0.3
    max_density: float = 1.5
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        wrapped_generator: PhraseGenerator | None = None,
        bpm: float = 120.0,
        reference_bpm: float = 120.0,
        scaling_mode: str = "logarithmic",
        min_density: float = 0.3,
        max_density: float = 1.5,
    ) -> None:
        super().__init__(params)
        self.wrapped_generator = wrapped_generator
        self.bpm = max(40.0, min(300.0, bpm))
        self.reference_bpm = max(40.0, min(300.0, reference_bpm))
        self.scaling_mode = scaling_mode
        self.min_density = max(0.1, min(1.0, min_density))
        self.max_density = max(1.0, min(3.0, max_density))

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if self.wrapped_generator is None:
            return []

        # Get notes from inner generator
        notes = self.wrapped_generator.render(chords, key, duration_beats, context)

        # Calculate density factor
        density_factor = self._calculate_density_factor()

        # Apply density factor: thin out or duplicate notes
        if density_factor < 1.0:
            notes = self._thin_notes(notes, density_factor)
        elif density_factor > 1.0:
            notes = self._densify_notes(notes, density_factor)

        # Adjust note durations based on BPM
        tempo_ratio = self.reference_bpm / self.bpm
        notes = [
            NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration * tempo_ratio,
                velocity=n.velocity,
                articulation=n.articulation,
                expression=dict(n.expression),
            )
            for n in notes
        ]

        if notes:
            last_chord = chords[-1] if chords else None
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _calculate_density_factor(self) -> float:
        ratio = self.reference_bpm / self.bpm

        if self.scaling_mode == "linear":
            factor = ratio
        elif self.scaling_mode == "logarithmic":
            factor = math.log2(ratio + 0.5) + 0.5
        elif self.scaling_mode == "genre_safe":
            # Genre-aware: less aggressive scaling
            if self.bpm < 80:
                factor = 1.3  # Boost density for slow tempos
            elif self.bpm > 160:
                factor = 0.7  # Reduce density for fast tempos
            else:
                factor = 1.0
        else:
            factor = ratio

        return max(self.min_density, min(self.max_density, factor))

    def _thin_notes(self, notes: list[NoteInfo], factor: float) -> list[NoteInfo]:
        """Remove notes to reduce density."""
        if not notes:
            return notes
        # Keep every 1/factor-th note on average
        keep_interval = max(1, int(1.0 / factor))
        result = []
        for i, note in enumerate(notes):
            if i % keep_interval == 0 or note.velocity > 90:
                result.append(note)
        return result

    def _densify_notes(self, notes: list[NoteInfo], factor: float) -> list[NoteInfo]:
        """Add notes to increase density (ghost notes between existing notes)."""
        if not notes or len(notes) < 2:
            return notes

        result = list(notes)
        num_extra = int(len(notes) * (factor - 1.0))

        for _ in range(num_extra):
            idx = random.randint(0, len(notes) - 2)
            n1 = notes[idx]
            n2 = notes[idx + 1]

            # Insert a ghost note between
            gap = n2.start - n1.start
            if gap > 0.125:
                ghost_onset = n1.start + gap * 0.5
                ghost_pitch = n1.pitch + random.choice([-1, 0, 1])
                result.append(
                    NoteInfo(
                        pitch=ghost_pitch,
                        start=round(ghost_onset, 6),
                        duration=gap * 0.4,
                        velocity=max(1, n1.velocity - 30),
                    )
                )

        result.sort(key=lambda n: n.start)
        return result
