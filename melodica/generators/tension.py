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
import math
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

    def _build_tension_note(
        self,
        pitch: int,
        onset: float,
        duration: float,
        vel: int,
        index: int = 0,
    ) -> NoteInfo:
        """
        Builds a high-fidelity tense note incorporating micro-timing staggering,
        pitch bend vibrato shiver, dynamic expression CC 11, and CC 74 cutoff decays.
        """
        # 1. Micro-timing attack staggering
        stagger = index * 0.025
        jitter = random.uniform(-0.003, 0.003)
        start_h = max(0.0, onset + stagger + jitter)
        dur = max(0.05, duration)
        v = max(1, min(127, vel))

        # 2. Continuous expression curves
        expression = {}
        steps = 10

        # CC 11 dynamic volume curves
        cc11_list = []
        for s in range(steps + 1):
            progress = s / steps
            t_rel = progress * dur
            if self.mode == "chromatic_rise":
                # Upward building swell
                val = int(35 + 85 * progress)
            elif self.mode == "chromatic_fall":
                # Fading out tension
                val = int(115 - 75 * progress)
            elif self.mode == "tritone_pulse":
                # Pulsing bell curve
                val = int(45 + 75 * math.sin(math.pi * progress))
            else:
                # Clusters, scatter: sharp attack decaying to sustained
                val = int(115 - 55 * (progress ** 0.5))
            cc11_list.append((round(t_rel, 6), max(1, min(127, val))))
        expression[11] = cc11_list

        # CC 74 cutoff sweeps: sharp attack, decaying to darker sustained tone
        cc74_list = []
        base_cutoff = 40 if self.register == "low" else 65
        for s in range(steps + 1):
            progress = s / steps
            t_rel = progress * dur
            cutoff_val = base_cutoff + int(35 * (1.0 - progress ** 0.4))
            cc74_list.append((round(t_rel, 6), max(1, min(127, cutoff_val))))
        expression[74] = cc74_list

        # Pitch Bend: creepy detuned high-frequency vibrato / shiver LFO
        freq_pb = 8.0  # Hz LFO
        pb_list = []
        for s in range(steps + 1):
            progress = s / steps
            t_rel = progress * dur
            lfo_val = int(800 * math.sin(2 * math.pi * freq_pb * t_rel + index * 0.7))
            pb_list.append((round(t_rel, 6), lfo_val))
        expression["pitch_bend"] = pb_list

        note = NoteInfo(
            pitch=max(0, min(127, pitch)),
            start=round(start_h, 6),
            duration=round(dur, 6),
            velocity=v,
        )
        note.expression = expression
        return note

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
                    notes.append(self._build_tension_note(pitch, t, self.note_duration, vel, 0))
                    pitch += 1
                t += self.note_duration

        elif self.mode == "chromatic_fall":
            pitch = reg_base + 24
            while t < duration_beats:
                if random.random() < self.density:
                    vel = int(self.velocity_level * 100) + random.randint(-10, 10)
                    notes.append(self._build_tension_note(pitch, t, self.note_duration, vel, 0))
                    pitch -= 1
                t += self.note_duration

        elif self.mode == "tritone_pulse":
            while t < duration_beats:
                if random.random() < self.density:
                    p1 = reg_base + 6
                    p2 = reg_base + 12  # tritone above
                    vel = int(self.velocity_level * 100)
                    
                    # Split or offset durations slightly for tension overlapping
                    dur_1 = self.note_duration * 0.5
                    dur_2 = self.note_duration * 0.5
                    
                    notes.append(self._build_tension_note(p1, t, dur_1, vel, 0))
                    notes.append(self._build_tension_note(p2, t + dur_1, dur_2, vel - 10, 1))
                t += self.note_duration

        else:
            # semitone_cluster, major7_tension, atonal_scatter
            while t < duration_beats:
                if random.random() < self.density:
                    chord = chord_at(chords, t) if chords else None
                    if self.mode == "atonal_scatter":
                        interval = random.choice(_DISSONANT_INTERVALS)
                        base = reg_base + random.randint(0, 12)
                        p1 = base
                        p2 = base + interval
                    elif self.mode == "major7_tension":
                        p1 = nearest_pitch(reg_base % 12, reg_base)
                        p2 = nearest_pitch((reg_base + 11) % 12, reg_base + 11)
                    else:  # semitone_cluster
                        p1 = nearest_pitch(reg_base % 12, reg_base)
                        p2 = p1 + 1

                    vel = int(self.velocity_level * 100) + random.randint(-5, 5)
                    notes.append(self._build_tension_note(p1, t, self.note_duration, vel, 0))
                    notes.append(self._build_tension_note(p2, t, self.note_duration, vel, 1))
                t += self.note_duration

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes


