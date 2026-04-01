"""
generators/groove.py — GrooveGenerator.

Funk/soul/Latin groove generator with ghost notes, accents, and syncopation.
Generates rhythm+velocity patterns that overlay on chord tones.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at

# Ghost note velocity threshold
GHOST_VEL = 30
ACCENT_VEL = 110

# Groove patterns: list of (beat_offset_16ths, velocity_multiplier, is_ghost)
# 16th note grid, 16 steps per bar
GROOVE_PATTERNS: dict[str, list[tuple[float, float, bool]]] = {
    "funk_1": [
        (0, 1.0, False),
        (0.25, 0.3, True),
        (0.5, 0.8, False),
        (0.75, 0.3, True),
        (1.0, 1.2, False),
        (1.25, 0.3, True),
        (1.5, 0.7, False),
        (1.75, 0.0, False),
        (2.0, 0.9, False),
        (2.25, 0.3, True),
        (2.5, 0.0, False),
        (2.75, 0.5, False),
        (3.0, 1.2, False),
        (3.25, 0.3, True),
        (3.5, 0.8, False),
        (3.75, 0.3, True),
    ],
    "funk_2": [
        (0, 1.0, False),
        (0.25, 0.0, False),
        (0.5, 0.6, False),
        (0.75, 0.3, True),
        (1.0, 0.0, False),
        (1.25, 0.8, False),
        (1.5, 0.0, False),
        (1.75, 0.5, False),
        (2.0, 1.0, False),
        (2.25, 0.3, True),
        (2.5, 0.6, False),
        (2.75, 0.0, False),
        (3.0, 0.9, False),
        (3.25, 0.0, False),
        (3.5, 0.7, False),
        (3.75, 0.3, True),
    ],
    "soul": [
        (0, 1.0, False),
        (0.5, 0.5, False),
        (0.75, 0.3, True),
        (1.0, 0.9, False),
        (1.5, 0.5, False),
        (1.75, 0.3, True),
        (2.0, 1.2, False),
        (2.5, 0.5, False),
        (2.75, 0.3, True),
        (3.0, 0.9, False),
        (3.5, 0.6, False),
        (3.75, 0.3, True),
    ],
    "latin": [
        (0, 1.0, False),
        (0.5, 0.0, False),
        (0.75, 0.7, False),
        (1.0, 0.0, False),
        (1.25, 0.8, False),
        (1.5, 0.5, False),
        (2.0, 1.0, False),
        (2.5, 0.0, False),
        (2.75, 0.7, False),
        (3.0, 0.0, False),
        (3.25, 0.8, False),
        (3.5, 0.5, False),
    ],
}


@dataclass
class GrooveGenerator(PhraseGenerator):
    """
    Funk/soul groove generator with ghost notes and accents.

    groove_pattern: named pattern or custom
    ghost_note_vel: velocity for ghost notes (default 30)
    accent_vel:     velocity for accents (default 110)
    """

    name: str = "Groove Generator"
    groove_pattern: str = "funk_1"
    ghost_note_vel: int = 30
    accent_vel: int = 110
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        groove_pattern: str = "funk_1",
        ghost_note_vel: int = 30,
        accent_vel: int = 110,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.groove_pattern = groove_pattern
        self.ghost_note_vel = max(1, min(127, ghost_note_vel))
        self.accent_vel = max(1, min(127, accent_vel))
        self.rhythm = rhythm
        self._last_context: RenderContext | None = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        pattern = GROOVE_PATTERNS.get(self.groove_pattern, GROOVE_PATTERNS["funk_1"])
        notes: list[NoteInfo] = []
        last_chord = chords[0]

        anchor = (self.params.key_range_low + self.params.key_range_high) // 2

        # Iterate bars
        bar = 0.0
        while bar < duration_beats:
            chord = chord_at(chords, bar) or last_chord
            last_chord = chord

            for beat_offset, vel_mult, is_ghost in pattern:
                onset = bar + beat_offset
                if onset >= duration_beats:
                    break

                # Skip rests (vel_mult == 0)
                if vel_mult == 0:
                    continue

                # Pitch
                if is_ghost:
                    # Ghost notes: chord tone, low register
                    pitch = nearest_pitch(chord.root, anchor - 5)
                else:
                    pcs = chord.pitch_classes()
                    pitch = nearest_pitch(random.choice(pcs) if pcs else chord.root, anchor)

                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

                # Velocity
                if is_ghost:
                    vel = self.ghost_note_vel
                elif vel_mult >= 1.2:
                    vel = self.accent_vel
                else:
                    vel = int(60 + self.params.density * 40 * vel_mult)

                # Duration: ghost notes are very short
                if is_ghost:
                    dur = 0.08
                else:
                    dur = 0.2

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=round(dur, 6),
                        velocity=max(1, min(127, vel)),
                    )
                )

            bar += 4.0  # next bar

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    def _velocity(self) -> int:
        return int(70 + self.params.density * 30)
