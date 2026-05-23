# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica/form.py — Musical form structural definition.
Defines musical forms such as Sonata, Ternary, Rondo, and Through-Composed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional
from melodica.types import Scale


@dataclass
class FormSection:
    name: str                   # "intro", "exposition", "development", "recapitulation", "coda", "A", "B", etc.
    start_beat: float
    duration_beats: float
    dynamics: str               # "pp", "p", "mp", "mf", "f", "ff"
    tempo_multiplier: float     # 1.0 = normal, 0.75 = slower, 1.25 = faster
    active_families: list[str]  # ["strings", "brass", "woodwinds", "percussion", "choir"]
    mood: str                   # "tense", "lyrical", "triumphant", "mournful", "ethereal", etc.
    repeat_id: str | None = None  # For recurring sections, e.g. "A", "B"

    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration_beats


@dataclass
class MusicalForm:
    sections: list[FormSection]
    tempo_map: list[tuple[float, float]]  # [(beat, bpm), ...] — tempo changes

    @classmethod
    def _create_with_tempo_map(
        cls, sections: list[FormSection], base_bpm: float = 120.0
    ) -> MusicalForm:
        """Helper to build a MusicalForm with smooth tempo transitions (accel/rit)."""
        tempo_map: list[tuple[float, float]] = []
        
        for i, sec in enumerate(sections):
            target_bpm = base_bpm * sec.tempo_multiplier
            
            # If it's the first section, start immediately with its tempo
            if i == 0:
                tempo_map.append((sec.start_beat, target_bpm))
            else:
                prev_sec = sections[i - 1]
                prev_bpm = base_bpm * prev_sec.tempo_multiplier
                
                if prev_bpm != target_bpm:
                    # Generate a smooth transition (accel/rit) over a transition window.
                    # Transition window is 4 beats or 20% of previous section's duration, whichever is smaller.
                    transition_duration = min(4.0, prev_sec.duration_beats * 0.2)
                    
                    if transition_duration > 0.5:
                        transition_start = sec.start_beat - transition_duration
                        # Interpolate in 4 steps
                        steps = 4
                        for step in range(steps):
                            t = step / steps
                            curr_beat = transition_start + t * transition_duration
                            curr_bpm = prev_bpm + t * (target_bpm - prev_bpm)
                            tempo_map.append((round(curr_beat, 3), round(curr_bpm, 2)))
                
                tempo_map.append((sec.start_beat, target_bpm))
                
        # Sort and deduplicate beat triggers
        tempo_map = sorted(list(set(tempo_map)), key=lambda x: x[0])
        return cls(sections=sections, tempo_map=tempo_map)

    @staticmethod
    def sonata(key: Scale, duration_beats: float, base_bpm: float = 120.0) -> MusicalForm:
        """
        Sonata form:
        exposition (30%) -> development (35%) -> recapitulation (25%) -> coda (10%)
        Optional intro can be pre-pended, but we'll stick to a standard balanced layout:
        intro (10%) -> exposition (30%) -> development (30%) -> recapitulation (20%) -> coda (10%)
        """
        p_intro = round(duration_beats * 0.10, 3)
        p_expo = round(duration_beats * 0.30, 3)
        p_dev = round(duration_beats * 0.30, 3)
        p_recap = round(duration_beats * 0.20, 3)
        p_coda = duration_beats - (p_intro + p_expo + p_dev + p_recap)

        sections = [
            FormSection(
                name="intro",
                start_beat=0.0,
                duration_beats=p_intro,
                dynamics="pp",
                tempo_multiplier=0.85,
                active_families=["strings", "woodwinds"],
                mood="mysterious",
            ),
            FormSection(
                name="exposition",
                start_beat=p_intro,
                duration_beats=p_expo,
                dynamics="mp",
                tempo_multiplier=1.0,
                active_families=["strings", "woodwinds", "brass"],
                mood="lyrical",
            ),
            FormSection(
                name="development",
                start_beat=p_intro + p_expo,
                duration_beats=p_dev,
                dynamics="f",
                tempo_multiplier=1.15,
                active_families=["strings", "woodwinds", "brass", "percussion"],
                mood="tense",
            ),
            FormSection(
                name="recapitulation",
                start_beat=p_intro + p_expo + p_dev,
                duration_beats=p_recap,
                dynamics="mf",
                tempo_multiplier=1.0,
                active_families=["strings", "woodwinds", "brass", "percussion"],
                mood="triumphant",
            ),
            FormSection(
                name="coda",
                start_beat=p_intro + p_expo + p_dev + p_recap,
                duration_beats=p_coda,
                dynamics="ff",
                tempo_multiplier=1.2,
                active_families=["strings", "brass", "percussion"],
                mood="triumphant",
            ),
        ]
        return MusicalForm._create_with_tempo_map(sections, base_bpm)

    @staticmethod
    def ternary(key: Scale, duration_beats: float, base_bpm: float = 120.0) -> MusicalForm:
        """
        Ternary (ABA) form:
        A (40%) -> B (30%) -> A' (30%)
        """
        p_a1 = round(duration_beats * 0.40, 3)
        p_b = round(duration_beats * 0.30, 3)
        p_a2 = duration_beats - (p_a1 + p_b)

        sections = [
            FormSection(
                name="A",
                start_beat=0.0,
                duration_beats=p_a1,
                dynamics="mf",
                tempo_multiplier=1.0,
                active_families=["strings", "woodwinds"],
                mood="lyrical",
                repeat_id="A",
            ),
            FormSection(
                name="B",
                start_beat=p_a1,
                duration_beats=p_b,
                dynamics="p",
                tempo_multiplier=0.85,
                active_families=["strings", "woodwinds", "choir"],
                mood="mournful",
                repeat_id="B",
            ),
            FormSection(
                name="A_prime",
                start_beat=p_a1 + p_b,
                duration_beats=p_a2,
                dynamics="f",
                tempo_multiplier=1.0,
                active_families=["strings", "brass", "woodwinds", "percussion"],
                mood="triumphant",
                repeat_id="A",
            ),
        ]
        return MusicalForm._create_with_tempo_map(sections, base_bpm)

    @staticmethod
    def rondo(key: Scale, duration_beats: float, base_bpm: float = 120.0) -> MusicalForm:
        """
        Rondo (ABACA) form:
        A (25%) -> B (20%) -> A (20%) -> C (20%) -> A (15%)
        """
        p_a1 = round(duration_beats * 0.25, 3)
        p_b = round(duration_beats * 0.20, 3)
        p_a2 = round(duration_beats * 0.20, 3)
        p_c = round(duration_beats * 0.20, 3)
        p_a3 = duration_beats - (p_a1 + p_b + p_a2 + p_c)

        sections = [
            FormSection(
                name="A1",
                start_beat=0.0,
                duration_beats=p_a1,
                dynamics="mf",
                tempo_multiplier=1.0,
                active_families=["strings", "woodwinds"],
                mood="playful",
                repeat_id="A",
            ),
            FormSection(
                name="B",
                start_beat=p_a1,
                duration_beats=p_b,
                dynamics="f",
                tempo_multiplier=1.1,
                active_families=["strings", "brass"],
                mood="tense",
                repeat_id="B",
            ),
            FormSection(
                name="A2",
                start_beat=p_a1 + p_b,
                duration_beats=p_a2,
                dynamics="mf",
                tempo_multiplier=1.0,
                active_families=["strings", "woodwinds"],
                mood="playful",
                repeat_id="A",
            ),
            FormSection(
                name="C",
                start_beat=p_a1 + p_b + p_a2,
                duration_beats=p_c,
                dynamics="p",
                tempo_multiplier=0.8,
                active_families=["woodwinds", "choir"],
                mood="lyrical",
                repeat_id="C",
            ),
            FormSection(
                name="A3",
                start_beat=p_a1 + p_b + p_a2 + p_c,
                duration_beats=p_a3,
                dynamics="ff",
                tempo_multiplier=1.05,
                active_families=["strings", "brass", "woodwinds", "percussion"],
                mood="triumphant",
                repeat_id="A",
            ),
        ]
        return MusicalForm._create_with_tempo_map(sections, base_bpm)

    @staticmethod
    def through_composed(key: Scale, duration_beats: float, base_bpm: float = 120.0) -> MusicalForm:
        """
        Through-composed form:
        A continuous progression of contrasting sections with no repetitions.
        """
        p_sec = round(duration_beats / 4.0, 3)
        p_last = duration_beats - p_sec * 3.0

        sections = [
            FormSection(
                name="part1",
                start_beat=0.0,
                duration_beats=p_sec,
                dynamics="p",
                tempo_multiplier=0.9,
                active_families=["strings"],
                mood="ethereal",
            ),
            FormSection(
                name="part2",
                start_beat=p_sec,
                duration_beats=p_sec,
                dynamics="mp",
                tempo_multiplier=1.0,
                active_families=["strings", "woodwinds"],
                mood="lyrical",
            ),
            FormSection(
                name="part3",
                start_beat=p_sec * 2.0,
                duration_beats=p_sec,
                dynamics="f",
                tempo_multiplier=1.1,
                active_families=["strings", "brass", "woodwinds"],
                mood="tense",
            ),
            FormSection(
                name="part4",
                start_beat=p_sec * 3.0,
                duration_beats=p_last,
                dynamics="ff",
                tempo_multiplier=1.2,
                active_families=["strings", "brass", "percussion"],
                mood="triumphant",
            ),
        ]
        return MusicalForm._create_with_tempo_map(sections, base_bpm)
