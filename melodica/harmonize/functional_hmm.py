# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
functional_hmm.py — Functional Harmony + HMM Emission Harmonizer.

Three-phase pipeline:
1. Functional Plan: T/S/D function sequence from tension curve
2. Chord Selection: mode-specific degree tables + cadences + HMM emission scoring
3. Assembly: ChordLabel list with function labels

This replaces pure Viterbi over trained transitions with musically informed
functional harmony, using HMM emission (pnote) only for voice-leading scoring.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

import numpy as np

from melodica.harmonize.coupled_hmm import LOG_PNOTE, N_TONES, TYPE_TO_QUALITY
from melodica.harmonize._hmm_helpers import (
    MODAL_CADENCES,
    MODAL_GRAVITY,
    _build_diatonic_chords,
    _voice_leading_cost,
)
from melodica.composer.tension_curve import TensionCurve, TensionPhase
from melodica.types import (
    BarGrid,
    ChordLabel,
    HarmonicFunction,
    Mode,
    NoteInfo,
    Quality,
    Scale,
)

# ---------------------------------------------------------------------------
# Functional degree classification
# ---------------------------------------------------------------------------

_TONIC_DEGREES = {1, 3, 6}
_SUBDOMINANT_DEGREES = {2, 4}
_DOMINANT_DEGREES = {5, 7}


def _degree_to_function(degree: int) -> HarmonicFunction:
    if degree in _TONIC_DEGREES:
        return HarmonicFunction.TONIC
    if degree in _SUBDOMINANT_DEGREES:
        return HarmonicFunction.SUBDOMINANT
    if degree in _DOMINANT_DEGREES:
        return HarmonicFunction.DOMINANT
    return HarmonicFunction.TONIC


def _build_functional_degrees(scale: Scale) -> dict[HarmonicFunction, list[int]]:
    """Map scale degrees to functional categories."""
    degs = scale.degrees()
    n = len(degs)
    result: dict[HarmonicFunction, list[int]] = {
        HarmonicFunction.TONIC: [],
        HarmonicFunction.SUBDOMINANT: [],
        HarmonicFunction.DOMINANT: [],
    }
    for i in range(n):
        deg = i + 1
        fn = _degree_to_function(deg)
        result[fn].append(deg)
    return result


# ---------------------------------------------------------------------------
# Cadence templates
# ---------------------------------------------------------------------------

_CADENCE_TEMPLATES = {
    "authentic": [
        (HarmonicFunction.DOMINANT, 5),
        (HarmonicFunction.TONIC, 1),
    ],
    "plagal": [
        (HarmonicFunction.SUBDOMINANT, 4),
        (HarmonicFunction.TONIC, 1),
    ],
    "deceptive": [
        (HarmonicFunction.DOMINANT, 5),
        (HarmonicFunction.TONIC, 6),
    ],
    "half": [
        (HarmonicFunction.SUBDOMINANT, 2),
        (HarmonicFunction.DOMINANT, 5),
    ],
}

# Quality → type index for HMM emission scoring
_QUALITY_TO_TYPE_IDX = {q: i for i, q in enumerate(TYPE_TO_QUALITY)}


# ---------------------------------------------------------------------------
# FunctionalHMMHarmonizer
# ---------------------------------------------------------------------------

@dataclass
class FunctionalHMMHarmonizer:
    """Functional Harmony + HMM Emission Harmonizer."""

    beam_width: int = 8
    chord_change: str = "bars"
    bar_grid: BarGrid | None = None
    embellish_rate: float = 0.30  # probability of embellishing a bar

    def harmonize(
        self,
        melody: list[NoteInfo],
        initial_scale: Scale,
        duration_beats: float,
        constraints: list[ChordLabel] | None = None,
        tension_curve: TensionCurve | None = None,
    ) -> list[ChordLabel]:
        if not melody:
            return []

        scale = initial_scale
        change_points = self._get_change_points(duration_beats)
        T = len(change_points)

        # Phase 1: Functional plan
        func_plan = self._plan_functions(T, change_points, tension_curve)

        # Phase 2: Chord selection
        diatonic = _build_diatonic_chords(scale)
        func_degrees = _build_functional_degrees(scale)
        observations = self._extract_observations(melody, change_points)
        gravity = MODAL_GRAVITY.get(scale.mode, [0])

        chords = self._select_chords(
            func_plan, scale, diatonic, func_degrees, observations, gravity, T, change_points
        )

        # Phase 3: Embellishments
        if self.embellish_rate > 0:
            chords = self._apply_embellishments(chords, scale, T)

        # Phase 4: Assembly
        return self._build_labels(chords, change_points, duration_beats)

    # ------------------------------------------------------------------
    # Phase 1: Functional Plan
    # ------------------------------------------------------------------

    def _plan_functions(
        self,
        n_bars: int,
        change_points: list[float],
        tension: TensionCurve | None,
    ) -> list[HarmonicFunction]:
        """Generate T/S/D function sequence from tension curve."""
        plan: list[HarmonicFunction] = []

        for i in range(n_bars):
            beat = change_points[i]
            if tension:
                phase = tension.phase_at(beat)
                if phase == TensionPhase.REST:
                    plan.append(HarmonicFunction.TONIC)
                elif phase == TensionPhase.BUILD:
                    plan.append(HarmonicFunction.SUBDOMINANT)
                elif phase == TensionPhase.CLIMAX:
                    plan.append(HarmonicFunction.DOMINANT)
                elif phase == TensionPhase.RESOLUTION:
                    plan.append(HarmonicFunction.TONIC)
                elif phase == TensionPhase.SUSTAIN:
                    plan.append(random.choice([HarmonicFunction.SUBDOMINANT, HarmonicFunction.DOMINANT]))
                else:
                    plan.append(HarmonicFunction.TONIC)
            else:
                # Varied functional cycles for musical interest
                cycle_patterns = [
                    [HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT, HarmonicFunction.DOMINANT, HarmonicFunction.TONIC],      # T S D T
                    [HarmonicFunction.TONIC, HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT, HarmonicFunction.DOMINANT],       # T T S D
                    [HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT, HarmonicFunction.TONIC, HarmonicFunction.DOMINANT],       # T S T D
                    [HarmonicFunction.SUBDOMINANT, HarmonicFunction.TONIC, HarmonicFunction.DOMINANT, HarmonicFunction.TONIC],       # S T D T
                    [HarmonicFunction.TONIC, HarmonicFunction.DOMINANT, HarmonicFunction.SUBDOMINANT, HarmonicFunction.DOMINANT],    # T D S D (needs grammar fix)
                ]
                if i % 4 == 0 or i == 0:
                    cycle = random.choice(cycle_patterns)
                pos = i % 4
                plan.append(cycle[pos])

        # Enforce grammar: no D→S (weak progression)
        for i in range(1, len(plan)):
            if plan[i - 1] == HarmonicFunction.DOMINANT and plan[i] == HarmonicFunction.SUBDOMINANT:
                plan[i] = HarmonicFunction.TONIC

        return plan

    # ------------------------------------------------------------------
    # Phase 2: Chord Selection
    # ------------------------------------------------------------------

    def _select_chords(
        self,
        func_plan: list[HarmonicFunction],
        scale: Scale,
        diatonic: list[tuple[int, Quality]],
        func_degrees: dict[HarmonicFunction, list[int]],
        observations: list[list[tuple[int, float]]],
        gravity: list[int],
        n_bars: int,
        change_points: list[float],
    ) -> list[tuple[int, int, HarmonicFunction]]:
        """Select concrete chords for each functional slot.

        Returns list of (root_pc, degree_1based, function).
        """
        result: list[tuple[int, int, HarmonicFunction]] = []
        degs = scale.degrees()

        # Cadence positions: only every 4 bars at a T-after-D boundary
        cadence_positions = set()
        for i in range(2, n_bars):
            if func_plan[i] == HarmonicFunction.TONIC and func_plan[i - 1] == HarmonicFunction.DOMINANT:
                if (i + 1) % 4 == 0 or i == n_bars - 1:  # every 4 bars or final bar
                    cadence_positions.add(i - 1)  # V
                    cadence_positions.add(i)       # I

        for i in range(n_bars):
            fn = func_plan[i]

            # Cadence override: force V→I ONLY at structural cadence positions
            if i in cadence_positions and func_plan[i] == HarmonicFunction.DOMINANT:
                deg = 5
                root_pc = int(round(degs[(deg - 1) % len(degs)]))
                quality = diatonic[(deg - 1) % len(diatonic)][1]
                if quality == Quality.MAJOR:
                    quality = Quality.DOMINANT7
                result.append((root_pc, deg, fn))
                continue

            if i in cadence_positions and func_plan[i] == HarmonicFunction.TONIC:
                deg = 1
                root_pc = int(round(degs[(deg - 1) % len(degs)]))
                quality = diatonic[(deg - 1) % len(diatonic)][1]
                result.append((root_pc, deg, fn))
                continue

            # Get candidate degrees for this function
            candidates = func_degrees.get(fn, [1])
            if not candidates:
                candidates = [1]

            # Score each candidate using HMM emission + gravity + diversity
            best_deg = candidates[0]
            best_score = -1e9

            for deg in candidates:
                root_pc = int(round(degs[(deg - 1) % len(degs)]))
                quality = diatonic[(deg - 1) % len(diatonic)][1]

                # HMM emission score (scaled down — functional fit matters more)
                emit_score = self._score_emission(root_pc, quality, observations[i]) * 0.3

                # Gravity bonus (characteristic degrees of the mode)
                grav_bonus = 3.0 if (deg - 1) in gravity else 0.0

                # Avoid repeating same degree
                deg_penalty = 0.0
                if result and result[-1][1] == deg:
                    deg_penalty = -6.0

                # Avoid repeating same root
                root_penalty = 0.0
                if result and result[-1][0] == root_pc:
                    root_penalty = -5.0

                # Avoid repeating same root INTERVAL as the previous transition
                interval_penalty = 0.0
                if len(result) >= 2:
                    prev_interval = (result[-1][0] - result[-2][0]) % 12
                    this_interval = (root_pc - result[-1][0]) % 12
                    if prev_interval == this_interval and prev_interval != 0:
                        interval_penalty = -4.0

                # Avoid same root as 2 bars ago (prevents ABA pattern)
                aba_penalty = 0.0
                if len(result) >= 2 and result[-2][0] == root_pc:
                    aba_penalty = -3.0

                score = emit_score + grav_bonus + deg_penalty + root_penalty + interval_penalty + aba_penalty
                if score > best_score:
                    best_score = score
                    best_deg = deg

            root_pc = int(round(degs[(best_deg - 1) % len(degs)]))
            result.append((root_pc, best_deg, fn))

        return result

    def _score_emission(
        self, root: int, quality: Quality, obs: list[tuple[int, float]]
    ) -> float:
        """Score how well a chord fits the melody observations using HMM emission."""
        t_idx = _QUALITY_TO_TYPE_IDX.get(quality)
        if t_idx is None or not obs:
            return 0.0

        score = 0.0
        total_w = 0.0
        for pc, w in obs:
            off = (pc - root) % N_TONES
            score += w * LOG_PNOTE[off, t_idx]
            total_w += w

        return score / (total_w + 1e-6) if total_w > 0 else 0.0

    # ------------------------------------------------------------------
    # Phase 3: Embellishments
    # ------------------------------------------------------------------

    def _apply_embellishments(
        self,
        chords: list[tuple[int, int, HarmonicFunction]],
        scale: Scale,
        n_bars: int,
    ) -> list[tuple[int, int, HarmonicFunction]]:
        """Apply secondary dominants and borrowed chords probabilistically."""
        result = list(chords)
        degs = scale.degrees()

        for i in range(len(result)):
            if random.random() > self.embellish_rate:
                continue

            root_pc, deg, fn = result[i]

            # Secondary dominant: replace with V7/x where x is the next chord
            if i + 1 < len(result) and fn == HarmonicFunction.DOMINANT:
                next_root = result[i + 1][0]
                # V7 of next chord: root is a P5 above (or P4 below) the target
                sec_dom_root = (next_root + 7) % 12
                # Only if sec_dom_root is NOT the same as current
                if sec_dom_root != root_pc:
                    result[i] = (sec_dom_root, deg, HarmonicFunction.SECONDARY)

            # Borrowed chord: use parallel mode's degree (only for S/T functions)
            elif fn == HarmonicFunction.SUBDOMINANT and random.random() < 0.3:
                # Borrow from parallel major/minor
                if scale.mode in (Mode.HARMONIC_MINOR, Mode.MELODIC_MINOR, Mode.NATURAL_MINOR, Mode.AEOLIAN, Mode.DORIAN, Mode.PHRYGIAN):
                    parallel = Mode.MAJOR
                else:
                    parallel = Mode.HARMONIC_MINOR

                try:
                    parallel_scale = Scale(root=scale.root, mode=parallel)
                    parallel_degs = parallel_scale.degrees()
                    if deg <= len(parallel_degs):
                        borrowed_root = int(round(parallel_degs[(deg - 1) % len(parallel_degs)]))
                        if borrowed_root != root_pc:
                            result[i] = (borrowed_root, deg, fn)
                except (ValueError, IndexError):
                    pass

        return result

    # ------------------------------------------------------------------
    # Phase 4: Assembly
    # ------------------------------------------------------------------

    def _build_labels(
        self,
        chords: list[tuple[int, int, HarmonicFunction]],
        change_points: list[float],
        duration_beats: float,
    ) -> list[ChordLabel]:
        """Build ChordLabel list from chord tuples."""
        result = []
        n = len(chords)

        for i, (root_pc, deg, fn) in enumerate(chords):
            # Determine quality from root and context
            quality = self._quality_for_context(root_pc, deg, fn, i, n)

            start = change_points[i]
            dur = (change_points[i + 1] - start) if i + 1 < n else duration_beats - start

            result.append(ChordLabel(
                root=root_pc,
                quality=quality,
                start=round(start, 6),
                duration=round(dur, 6),
                degree=deg,
                function=fn,
            ))

        return result

    def _quality_for_context(
        self, root: int, deg: int, fn: HarmonicFunction, idx: int, total: int
    ) -> Quality:
        """Choose appropriate quality based on function and context."""
        if fn == HarmonicFunction.DOMINANT:
            # Dominant function: prefer Dom7, especially at cadences
            if idx + 1 < total:
                return Quality.DOMINANT7
            return Quality.MAJOR
        if fn == HarmonicFunction.SECONDARY:
            return Quality.DOMINANT7
        if fn == HarmonicFunction.SUBDOMINANT:
            # Subdominant: minor for ii, major for IV
            if deg == 2:
                return Quality.MINOR7
            if deg == 4:
                return Quality.MAJOR
        # Tonic: basic triad or Maj7
        if deg == 1:
            return Quality.MAJOR if random.random() < 0.6 else Quality.MAJOR7
        if deg in (3, 6):
            return Quality.MINOR
        return Quality.MAJOR

    # ------------------------------------------------------------------
    # Observation extraction (simplified from CoupledHMMHarmonizer)
    # ------------------------------------------------------------------

    def _get_change_points(self, duration: float) -> list[float]:
        if self.bar_grid:
            mode_map = {"bars": "bars", "half": "strong_beats", "beats": "beats"}
            return self.bar_grid.change_points(duration, mode=mode_map.get(self.chord_change, "bars"))

        step = 4.0 if self.chord_change == "bars" else 2.0
        pts = []
        t = 0.0
        while t < duration - 0.01:
            pts.append(round(t, 6))
            t += step
        return pts

    def _extract_observations(
        self, melody: list[NoteInfo], change_points: list[float]
    ) -> list[list[tuple[int, float]]]:
        """Extract pitch-class observations per change point."""
        bpb = self.bar_grid.beats_per_bar if self.bar_grid else 4.0
        observations = []

        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")
            pc_weights: dict[int, float] = {}

            for n in melody:
                n_end = n.start + n.duration
                overlap_start = max(cp, n.start)
                overlap_end = min(next_cp, n_end)

                if overlap_end > overlap_start:
                    active_dur = overlap_end - overlap_start
                    pc = n.pitch % 12
                    weight = math.sqrt(active_dur)
                    pc_weights[pc] = pc_weights.get(pc, 0.0) + weight

            observations.append(list(pc_weights.items()))

        return observations
