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
generators/section_builder.py — Song section pattern generator.

Creates musically appropriate note patterns for different song sections
(intro, verse, chorus, bridge, outro). Each section type has a distinct
character in terms of density, register, rhythm, and dynamics.

Section types:
    "intro"    — sparse, building, often simpler patterns
    "verse"    — moderate density, supportive, repeatable
    "chorus"   — high energy, wider range, fuller texture
    "bridge"   — contrasting, new harmonic territory, transitional
    "outro"    — winding down, often echoing chorus or intro
    "pre_chorus" — building tension before chorus
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


_SECTION_CONFIGS = {
    "intro": {
        "density_factor": 0.5,
        "octave_shift": 0,
        "note_dur": 1.0,
        "velocity_factor": 0.7,
        "leap_prob": 0.2,
    },
    "verse": {
        "density_factor": 0.7,
        "octave_shift": 0,
        "note_dur": 0.5,
        "velocity_factor": 0.8,
        "leap_prob": 0.3,
    },
    "chorus": {
        "density_factor": 1.0,
        "octave_shift": 0,
        "note_dur": 0.5,
        "velocity_factor": 1.0,
        "leap_prob": 0.5,
    },
    "bridge": {
        "density_factor": 0.6,
        "octave_shift": 1,
        "note_dur": 0.75,
        "velocity_factor": 0.85,
        "leap_prob": 0.6,
    },
    "outro": {
        "density_factor": 0.4,
        "octave_shift": -1,
        "note_dur": 1.5,
        "velocity_factor": 0.6,
        "leap_prob": 0.15,
    },
    "pre_chorus": {
        "density_factor": 0.8,
        "octave_shift": 0,
        "note_dur": 0.5,
        "velocity_factor": 0.9,
        "leap_prob": 0.4,
    },
}


@dataclass
class SectionBuilderGenerator(PhraseGenerator):
    """
    Song section pattern generator.

    section_type:
        Type of song section. See _SECTION_CONFIGS.
    pattern:
        Note pattern: "melody", "chord_pulse", "arpeggio", "bass_walk".
    bars_per_section:
        Length of each section in bars (4 beats each).
    """

    name: str = "Section Builder Generator"
    section_type: str = "verse"
    pattern: str = "melody"
    bars_per_section: int = 4
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        section_type: str = "verse",
        pattern: str = "melody",
        bars_per_section: int = 4,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if section_type not in _SECTION_CONFIGS:
            raise ValueError(
                f"Unknown section_type: {section_type!r}; "
                f"expected one of {sorted(_SECTION_CONFIGS)}"
            )
        self.section_type = section_type
        self.pattern = pattern
        self.bars_per_section = max(1, min(32, bars_per_section))
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

        cfg = _SECTION_CONFIGS[self.section_type]
        notes: list[NoteInfo] = []
        t = 0.0
        dur = cfg["note_dur"]
        prev_pitch = key.root * 12 + 60 + cfg["octave_shift"] * 12

        while t < duration_beats:
            chord = chord_at(chords, t)
            pcs = chord.pitch_classes()
            if not pcs:
                t += dur
                continue

            if random.random() > cfg["density_factor"]:
                t += dur
                continue

            if self.pattern == "melody":
                if random.random() < cfg["leap_prob"]:
                    pc = random.choice(pcs)
                else:
                    pc = min(pcs, key=lambda p: abs((p + 60) - prev_pitch))
                pitch = nearest_pitch(pc, prev_pitch)
                pitch += cfg["octave_shift"] * 12
                pitch = max(0, min(127, pitch))
                vel = int(self.params.density * 100 * cfg["velocity_factor"])
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(t, 6), duration=dur, velocity=max(1, min(127, vel))
                    )
                )
                prev_pitch = pitch

            elif self.pattern == "chord_pulse":
                vel = int(self.params.density * 100 * cfg["velocity_factor"])
                for pc in pcs[:3]:
                    pitch = nearest_pitch(pc, 60 + cfg["octave_shift"] * 12)
                    pitch = max(0, min(127, pitch))
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=dur,
                            velocity=max(1, min(127, vel)),
                        )
                    )

            elif self.pattern == "arpeggio":
                ordered = sorted(pcs)
                for i, pc in enumerate(ordered):
                    pitch = nearest_pitch(pc, 60 + cfg["octave_shift"] * 12)
                    pitch = max(0, min(127, pitch))
                    vel = int(self.params.density * 100 * cfg["velocity_factor"])
                    onset = t + i * (dur / len(ordered))
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(
                                pitch=pitch,
                                start=round(onset, 6),
                                duration=dur / len(ordered) * 0.8,
                                velocity=max(1, min(127, vel)),
                            )
                        )

            elif self.pattern == "bass_walk":
                pitch = nearest_pitch(pcs[0], 36 + cfg["octave_shift"] * 12)
                pitch = max(0, min(127, pitch))
                vel = int(self.params.density * 100 * cfg["velocity_factor"])
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(t, 6), duration=dur, velocity=max(1, min(127, vel))
                    )
                )
                prev_pitch = pitch

            t += dur

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes
