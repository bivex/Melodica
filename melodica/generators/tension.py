"""
generators/tension.py — Tension / dissonance generator.

Style: Horror, thriller, dark ambient, avant-garde, experimental.

Creates patterns built on dissonant intervals (minor 2nds, tritones,
major 7ths) that create unresolved tension. Useful for scoring,
dark textures, and building unease.

Modes:
    "semitone_cluster"  — tight semitone clusters (b2, b9)
    "tritone_pulse"     — tritone oscillation (the "devil's interval")
    "major7_tension"    — major 7th dissonance patterns
    "chromatic_rise"    — slow chromatic ascending line
    "chromatic_fall"    — slow chromatic descending line
    "atonal_scatter"    — random dissonant intervals
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


_DISSONANT_INTERVALS = [1, 6, 11, 2, 10]  # m2, tritone, M7, M2, m7


@dataclass
class TensionGenerator(PhraseGenerator):
    """
    Tension / dissonance generator.

    mode:
        Type of dissonance pattern.
    note_duration:
        Duration of each note in beats.
    velocity_level:
        Base velocity (0.0-1.0). Tension is usually quiet to moderate.
    register:
        "low", "mid", "high".
    density:
        Probability of placing a note at each subdivision (0.0-1.0).
    """

    name: str = "Tension Generator"
    mode: str = "semitone_cluster"
    note_duration: float = 2.0
    velocity_level: float = 0.4
    register: str = "mid"
    density: float = 0.6
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        mode: str = "semitone_cluster",
        note_duration: float = 2.0,
        velocity_level: float = 0.4,
        register: str = "mid",
        density: float = 0.6,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if mode not in (
            "semitone_cluster",
            "tritone_pulse",
            "major7_tension",
            "chromatic_rise",
            "chromatic_fall",
            "atonal_scatter",
        ):
            raise ValueError(f"Unknown tension mode: {mode!r}")
        self.mode = mode
        self.note_duration = max(0.25, min(8.0, note_duration))
        self.velocity_level = max(0.05, min(0.8, velocity_level))
        self.register = register
        self.density = max(0.1, min(1.0, density))
        self.rhythm = rhythm

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        reg_base = {"low": 36, "mid": 48, "high": 60}.get(self.register, 48)
        t = 0.0

        if self.mode == "chromatic_rise":
            pitch = reg_base
            while t < duration_beats:
                if random.random() < self.density:
                    vel = int(self.velocity_level * 100) + random.randint(-10, 10)
                    notes.append(
                        NoteInfo(
                            pitch=max(0, min(127, pitch)),
                            start=round(t, 6),
                            duration=self.note_duration,
                            velocity=max(1, min(127, vel)),
                        )
                    )
                    pitch += 1
                t += self.note_duration

        elif self.mode == "chromatic_fall":
            pitch = reg_base + 24
            while t < duration_beats:
                if random.random() < self.density:
                    vel = int(self.velocity_level * 100) + random.randint(-10, 10)
                    notes.append(
                        NoteInfo(
                            pitch=max(0, min(127, pitch)),
                            start=round(t, 6),
                            duration=self.note_duration,
                            velocity=max(1, min(127, vel)),
                        )
                    )
                    pitch -= 1
                t += self.note_duration

        elif self.mode == "tritone_pulse":
            while t < duration_beats:
                if random.random() < self.density:
                    p1 = reg_base + 6
                    p2 = reg_base + 12  # tritone above
                    vel = int(self.velocity_level * 100)
                    notes.append(
                        NoteInfo(
                            pitch=max(0, min(127, p1)),
                            start=round(t, 6),
                            duration=self.note_duration * 0.5,
                            velocity=vel,
                        )
                    )
                    notes.append(
                        NoteInfo(
                            pitch=max(0, min(127, p2)),
                            start=round(t + self.note_duration * 0.5, 6),
                            duration=self.note_duration * 0.5,
                            velocity=max(1, min(127, vel - 10)),
                        )
                    )
                t += self.note_duration

        else:
            # semitone_cluster, major7_tension, atonal_scatter
            while t < duration_beats:
                if random.random() < self.density:
                    chord = chord_at(chords, t) if chords else None
                    if self.mode == "atonal_scatter":
                        interval = random.choice(_DISSONANT_INTERVALS)
                        base = reg_base + random.randint(0, 12)
                        p1 = max(0, min(127, base))
                        p2 = max(0, min(127, base + interval))
                    elif self.mode == "major7_tension":
                        p1 = nearest_pitch(reg_base % 12, reg_base)
                        p2 = nearest_pitch((reg_base + 11) % 12, reg_base + 11)
                    else:  # semitone_cluster
                        p1 = nearest_pitch(reg_base % 12, reg_base)
                        p2 = max(0, min(127, p1 + 1))

                    vel = int(self.velocity_level * 100) + random.randint(-5, 5)
                    vel = max(1, min(127, vel))
                    notes.append(
                        NoteInfo(
                            pitch=p1, start=round(t, 6), duration=self.note_duration, velocity=vel
                        )
                    )
                    notes.append(
                        NoteInfo(
                            pitch=p2, start=round(t, 6), duration=self.note_duration, velocity=vel
                        )
                    )
                t += self.note_duration

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes
