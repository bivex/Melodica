"""
generators/backbeat.py — Backbeat accent generator.

Style: Funk, rock, R&B, pop, soul.

A backbeat generator places strong accents on beats 2 and 4,
the defining rhythmic feel of popular Western music since the 1950s.
Unlike drum pattern generators, this works with pitched instruments
(melody, chords, bass) to create a backbeat emphasis layer.

Modes:
    "accent"   — place notes on beats 2 & 4 with high velocity
    "ghost"    — place ghost notes on beats 1 & 3, accented notes on 2 & 4
    "chop"     — staccato chord stabs on 2 & 4 only
    "melody"   — melody notes with backbeat velocity boost on 2 & 4
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class BackbeatGenerator(PhraseGenerator):
    """
    Backbeat accent generator for pitched instruments.

    mode:
        Generation mode. "accent", "ghost", "chop", "melody".
    accent_velocity:
        Velocity factor for backbeat notes (beats 2 & 4).
    ghost_velocity:
        Velocity factor for ghost notes (beats 1 & 3) in "ghost" mode.
    subdivision:
        Subdivision in beats (1.0 = quarter, 0.5 = eighth).
    pitch_strategy:
        How to choose pitches: "chord_tone", "root", "fifth", "octave".
    """

    name: str = "Backbeat Generator"
    mode: str = "accent"
    accent_velocity: float = 1.0
    ghost_velocity: float = 0.4
    subdivision: float = 1.0
    pitch_strategy: str = "chord_tone"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        mode: str = "accent",
        accent_velocity: float = 1.0,
        ghost_velocity: float = 0.4,
        subdivision: float = 1.0,
        pitch_strategy: str = "chord_tone",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if mode not in ("accent", "ghost", "chop", "melody"):
            raise ValueError(f"Unknown backbeat mode: {mode!r}")
        self.mode = mode
        self.accent_velocity = max(0.1, min(1.5, accent_velocity))
        self.ghost_velocity = max(0.1, min(1.0, ghost_velocity))
        self.subdivision = max(0.25, min(2.0, subdivision))
        self.pitch_strategy = pitch_strategy
        self.rhythm = rhythm

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        notes: list[NoteInfo] = []
        t = 0.0

        while t < duration_beats:
            chord = chord_at(chords, t)
            beat_in_bar = t % 4.0
            is_backbeat = abs(beat_in_bar - 1.0) < 0.01 or abs(beat_in_bar - 3.0) < 0.01
            is_downbeat = abs(beat_in_bar) < 0.01 or abs(beat_in_bar - 2.0) < 0.01

            if self.mode == "accent":
                if is_backbeat:
                    pitch = self._pick_pitch(chord, key)
                    vel = self._vel(self.accent_velocity)
                    notes.append(
                        NoteInfo(
                            pitch=pitch, start=round(t, 6), duration=self.subdivision, velocity=vel
                        )
                    )

            elif self.mode == "ghost":
                pitch = self._pick_pitch(chord, key)
                if is_backbeat:
                    vel = self._vel(self.accent_velocity)
                elif is_downbeat:
                    vel = self._vel(self.ghost_velocity)
                else:
                    vel = self._vel(self.ghost_velocity * 0.7)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=self.subdivision * 0.5,
                        velocity=vel,
                    )
                )

            elif self.mode == "chop":
                if is_backbeat:
                    pitch = self._pick_pitch(chord, key)
                    vel = self._vel(self.accent_velocity)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=self.subdivision * 0.3,
                            velocity=vel,
                        )
                    )

            elif self.mode == "melody":
                pitch = self._pick_pitch(chord, key)
                if is_backbeat:
                    vel = self._vel(self.accent_velocity)
                else:
                    vel = self._vel(0.7)
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(t, 6), duration=self.subdivision, velocity=vel
                    )
                )

            t += self.subdivision

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes

    def _pick_pitch(self, chord: ChordLabel, key: Scale) -> int:
        pcs = chord.pitch_classes()
        if not pcs:
            return key.root * 12 + 60
        if self.pitch_strategy == "root":
            return nearest_pitch(pcs[0], 60)
        if self.pitch_strategy == "fifth":
            return nearest_pitch((pcs[0] + 7) % 12, 60)
        if self.pitch_strategy == "octave":
            return nearest_pitch(pcs[0], 72)
        return nearest_pitch(random.choice(pcs), 60)

    def _vel(self, factor: float) -> int:
        base = int(self.params.density * 100)
        return max(1, min(127, int(base * factor)))
