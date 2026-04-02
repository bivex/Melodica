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
harmonize/auto_harmonize.py — Auto-harmonization of melodies.

Two algorithms matching Melodica:
1. FunctionalHarmonizer — 18th century functional harmony
2. RuleBasedHarmonizer — Markov chain with chord progression rules
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.types import ChordLabel, Quality, HarmonicFunction, Scale, Mode, NoteInfo

# ---------------------------------------------------------------------------
# Roman numeral → chord quality mapping (major key)
# ---------------------------------------------------------------------------

_DEGREE_QUALITY: dict[int, tuple[Quality, HarmonicFunction]] = {
    1: (Quality.MAJOR, HarmonicFunction.TONIC),
    2: (Quality.MINOR, HarmonicFunction.SUBDOMINANT),
    3: (Quality.MINOR, HarmonicFunction.SECONDARY),
    4: (Quality.MAJOR, HarmonicFunction.SUBDOMINANT),
    5: (Quality.MAJOR, HarmonicFunction.DOMINANT),
    6: (Quality.MINOR, HarmonicFunction.SECONDARY),
    7: (Quality.DIMINISHED, HarmonicFunction.DOMINANT),
}

_MINOR_DEGREE_QUALITY: dict[int, tuple[Quality, HarmonicFunction]] = {
    1: (Quality.MINOR, HarmonicFunction.TONIC),
    2: (Quality.DIMINISHED, HarmonicFunction.SUBDOMINANT),
    3: (Quality.MAJOR, HarmonicFunction.SECONDARY),
    4: (Quality.MINOR, HarmonicFunction.SUBDOMINANT),
    5: (Quality.MAJOR, HarmonicFunction.DOMINANT),
    6: (Quality.MAJOR, HarmonicFunction.SECONDARY),
    7: (Quality.DIMINISHED, HarmonicFunction.DOMINANT),
}

# Functional harmonic rules: what can follow each degree
_FUNCTIONAL_RULES: dict[int, list[list[int]]] = {
    # degree: list of typical progressions (first = most expected)
    1: [[4, 5], [2, 5], [6], [4], [5]],
    2: [[5], [5, 7]],
    3: [[6], [4], [5]],
    4: [[5], [2, 5], [1]],
    5: [[1], [6], [4]],
    6: [[2], [5], [4]],
    7: [[1], [5, 1]],
}


def _chord_for_degree(
    degree: int,
    scale: Scale,
    duration: float,
    start: float,
    is_minor_key: bool = False,
) -> ChordLabel:
    """Build a ChordLabel for a diatonic degree (1-7)."""
    degs = scale.degrees()
    root_pc = int(degs[(degree - 1) % len(degs)])
    quality_map = _MINOR_DEGREE_QUALITY if is_minor_key else _DEGREE_QUALITY
    quality, func = quality_map.get(degree, (Quality.MAJOR, HarmonicFunction.TONIC))
    return ChordLabel(
        root=root_pc,
        quality=quality,
        start=round(start, 6),
        duration=round(duration, 6),
        degree=degree,
        function=func,
    )


def _melody_contains_pc(note_pc: int, chord_pcs: list[int]) -> bool:
    """Check if a pitch class belongs to a chord."""
    return note_pc in chord_pcs


def _compatible_degrees(melody_pc: int, scale: Scale, is_minor: bool = False) -> list[int]:
    """Find diatonic degrees whose chord contains the melody pitch class."""
    degs = scale.degrees()
    result = []
    for deg in range(1, 8):
        root_pc = degs[(deg - 1) % len(degs)]
        quality, _ = (_MINOR_DEGREE_QUALITY if is_minor else _DEGREE_QUALITY).get(
            deg, (Quality.MAJOR, HarmonicFunction.TONIC)
        )
        # Build chord pitch classes
        if quality == Quality.MAJOR:
            chord_pcs = [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12]
        elif quality == Quality.MINOR:
            chord_pcs = [root_pc, (root_pc + 3) % 12, (root_pc + 7) % 12]
        elif quality == Quality.DIMINISHED:
            chord_pcs = [root_pc, (root_pc + 3) % 12, (root_pc + 6) % 12]
        else:
            chord_pcs = [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12]
        if melody_pc in chord_pcs:
            result.append(deg)
    return result


# ---------------------------------------------------------------------------
# Basic Functional Harmonizer
# ---------------------------------------------------------------------------


@dataclass
class FunctionalHarmonizer:
    """
    18th-century functional harmonization.

    chord_change:  "bars" | "beats" | "strong_beats"
    allow_ii_iii_vi: whether to use ii, iii, vi
    allow_dominant_7: whether to use dominant 7th
    start_with:    "any" | "I" | "V" | "I_or_V"
    end_with:      "any" | "I" | "perfect_cadence" | "imperfect_cadence"
    """

    chord_change: str = "bars"
    allow_ii_iii_vi: bool = True
    allow_dominant_7: bool = False
    start_with: str = "any"
    end_with: str = "I"
    is_minor_key: bool = False

    def harmonize(
        self,
        melody: list[NoteInfo],
        scale: Scale,
        duration_beats: float,
    ) -> list[ChordLabel]:
        if not melody or not scale.degrees():
            return []

        # Group melody notes by chord change points
        change_points = self._get_change_points(duration_beats)
        groups = self._group_notes(melody, change_points)

        chords: list[ChordLabel] = []
        prev_degree = 0

        for i, (start, notes_in_group) in enumerate(groups):
            if not notes_in_group:
                continue

            # Find compatible degrees for all notes in this group
            all_compatible: set[int] | None = None
            for n in notes_in_group:
                pc = n.pitch % 12
                compatible = set(_compatible_degrees(pc, scale, self.is_minor_key))
                if all_compatible is None:
                    all_compatible = compatible
                else:
                    all_compatible &= compatible  # intersection

            if not all_compatible:
                all_compatible = {1}  # fallback to tonic

            # Filter by allow_ii_iii_vi
            if not self.allow_ii_iii_vi:
                all_compatible = {d for d in all_compatible if d in {1, 4, 5}}

            # Apply start/end constraints
            if i == 0 and self.start_with == "I":
                if 1 in all_compatible:
                    all_compatible = {1}
            elif i == 0 and self.start_with == "V":
                if 5 in all_compatible:
                    all_compatible = {5}
            elif i == 0 and self.start_with == "I_or_V":
                filtered = {d for d in all_compatible if d in {1, 5}}
                all_compatible = filtered if filtered else all_compatible

            is_last = i == len(groups) - 1
            if is_last and self.end_with in ("I", "perfect_cadence", "imperfect_cadence"):
                if 1 in all_compatible:
                    all_compatible = {1}

            # Choose degree: prefer functional progression from previous
            if prev_degree > 0 and prev_degree in _FUNCTIONAL_RULES:
                expected = _FUNCTIONAL_RULES[prev_degree]
                chosen = None
                for progression in expected:
                    for d in progression:
                        if d in all_compatible:
                            chosen = d
                            break
                    if chosen:
                        break
                if chosen is None:
                    chosen = random.choice(list(all_compatible))
            else:
                chosen = random.choice(list(all_compatible))

            duration = groups[i + 1][0] - start if i + 1 < len(groups) else duration_beats - start
            chord = _chord_for_degree(chosen, scale, duration, start, self.is_minor_key)

            # Add dominant 7th if enabled
            if self.allow_dominant_7 and chosen == 5:
                chord = ChordLabel(
                    root=chord.root,
                    quality=Quality.DOMINANT7,
                    start=chord.start,
                    duration=chord.duration,
                    degree=chord.degree,
                    function=chord.function,
                )

            chords.append(chord)
            prev_degree = chosen

        return chords

    def _get_change_points(self, duration: float) -> list[float]:
        """Generate chord change points based on chord_change setting."""
        points = []
        if self.chord_change == "bars":
            t = 0.0
            while t < duration:
                points.append(t)
                t += 4.0
        elif self.chord_change == "strong_beats":
            t = 0.0
            while t < duration:
                points.append(t)
                points.append(t + 2.0)
                t += 4.0
        elif self.chord_change == "beats":
            t = 0.0
            while t < duration:
                points.append(t)
                t += 1.0
        else:
            points = [0.0]
        return sorted(set(p for p in points if p < duration))

    def _group_notes(
        self,
        melody: list[NoteInfo],
        change_points: list[float],
    ) -> list[tuple[float, list[NoteInfo]]]:
        """Group melody notes by change points."""
        groups = []
        sorted_melody = sorted(melody, key=lambda n: n.start)
        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")
            notes_in_group = [n for n in sorted_melody if cp <= n.start < next_cp]
            groups.append((cp, notes_in_group))
        return groups


# ---------------------------------------------------------------------------
# Rule-Based Harmonizer (Markov chain)
# ---------------------------------------------------------------------------


@dataclass
class RuleBasedHarmonizer:
    """
    Markov-chain harmonization using chord progression rules.

    expectedness:  "most_expected" | "expected" | "less_expected" | "unexpected" | "random"
    allow_6th_7th: "no" | "6th" | "7th" | "both"
    chord_change:  "bars" | "beats" | "strong_beats"
    start_with:    "any" | "I" | "V"
    end_with:      "any" | "I" | "perfect_cadence" | "imperfect_cadence"
    """

    expectedness: str = "expected"
    allow_6th_7th: str = "no"
    chord_change: str = "bars"
    start_with: str = "any"
    end_with: str = "I"
    is_minor_key: bool = False

    # Transition weights: degree -> {next_degree: weight}
    transitions: dict[int, dict[int, float]] = field(
        default_factory=lambda: {
            1: {4: 0.35, 5: 0.25, 2: 0.15, 6: 0.15, 3: 0.05, 7: 0.05},
            2: {5: 0.45, 1: 0.20, 4: 0.15, 6: 0.10, 7: 0.10},
            3: {6: 0.35, 4: 0.25, 5: 0.20, 2: 0.10, 1: 0.10},
            4: {5: 0.35, 1: 0.25, 2: 0.15, 6: 0.15, 3: 0.05, 7: 0.05},
            5: {1: 0.40, 6: 0.25, 4: 0.15, 2: 0.10, 3: 0.05, 7: 0.05},
            6: {2: 0.30, 5: 0.25, 4: 0.20, 1: 0.15, 3: 0.10},
            7: {1: 0.50, 5: 0.25, 4: 0.15, 2: 0.10},
        }
    )

    def harmonize(
        self,
        melody: list[NoteInfo],
        scale: Scale,
        duration_beats: float,
    ) -> list[ChordLabel]:
        if not melody or not scale.degrees():
            return []

        change_points = self._get_change_points(duration_beats)
        chords: list[ChordLabel] = []
        prev_degree = 0

        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else duration_beats
            notes_in_group = [n for n in melody if cp <= n.start < next_cp]

            # Find compatible degrees
            all_compatible: set[int] | None = None
            for n in notes_in_group:
                pc = n.pitch % 12
                compatible = set(_compatible_degrees(pc, scale, self.is_minor_key))
                if all_compatible is None:
                    all_compatible = compatible
                else:
                    all_compatible &= compatible

            if not all_compatible:
                all_compatible = {1}

            # Filter by allow_6th/7th
            if self.allow_6th_7th == "no":
                all_compatible = {d for d in all_compatible if d in {1, 2, 3, 4, 5}}
            elif self.allow_6th_7th == "6th":
                all_compatible = {d for d in all_compatible if d in {1, 2, 3, 4, 5, 6}}
            elif self.allow_6th_7th == "7th":
                all_compatible = {d for d in all_compatible if d in {1, 2, 3, 4, 5, 7}}

            # Start/end constraints
            if i == 0 and self.start_with == "I":
                if 1 in all_compatible:
                    all_compatible = {1}
            elif i == 0 and self.start_with == "V":
                if 5 in all_compatible:
                    all_compatible = {5}

            is_last = i == len(change_points) - 1
            if is_last and self.end_with in ("I", "perfect_cadence", "imperfect_cadence"):
                if 1 in all_compatible:
                    all_compatible = {1}

            # Choose using Markov + expectedness
            chosen = self._choose_degree(prev_degree, all_compatible)

            duration = next_cp - cp
            chord = _chord_for_degree(chosen, scale, duration, cp, self.is_minor_key)
            chords.append(chord)
            prev_degree = chosen

        return chords

    def _choose_degree(self, prev: int, compatible: set[int]) -> int:
        if prev == 0 or prev not in self.transitions:
            return random.choice(list(compatible))

        weights = self.transitions[prev]
        # Filter to compatible degrees
        candidates = {d: w for d, w in weights.items() if d in compatible}
        if not candidates:
            return random.choice(list(compatible))

        # Sort by weight descending
        sorted_candidates = sorted(candidates.items(), key=lambda x: -x[1])

        if self.expectedness == "most_expected":
            return sorted_candidates[0][0]
        elif self.expectedness == "expected":
            top2 = sorted_candidates[:2]
            return random.choices([d for d, _ in top2], weights=[w for _, w in top2], k=1)[0]
        elif self.expectedness == "less_expected":
            rest = sorted_candidates[2:]
            if not rest:
                rest = sorted_candidates[1:]
            return random.choices([d for d, _ in rest], weights=[w for _, w in rest], k=1)[0]
        elif self.expectedness == "unexpected":
            rest = sorted_candidates[3:] if len(sorted_candidates) > 3 else sorted_candidates[2:]
            if not rest:
                rest = sorted_candidates
            return random.choice([d for d, _ in rest])
        else:  # random
            return random.choice(list(compatible))

    def _get_change_points(self, duration: float) -> list[float]:
        points = []
        if self.chord_change == "bars":
            t = 0.0
            while t < duration:
                points.append(t)
                t += 4.0
        elif self.chord_change == "strong_beats":
            t = 0.0
            while t < duration:
                points.append(t)
                points.append(t + 2.0)
                t += 4.0
        elif self.chord_change == "beats":
            t = 0.0
            while t < duration:
                points.append(t)
                t += 1.0
        else:
            points = [0.0]
        return sorted(set(p for p in points if p < duration))
