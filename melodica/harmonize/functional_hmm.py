# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
functional_hmm.py — Functional Harmony + HMM Emission Harmonizer.

Four-phase pipeline (inspired by FHARM — Koops, Magalhães & de Haas, 2013):
1. Functional Plan: T/S/D function sequence from tension curve or phrase patterns
2. Chord Selection: mode-specific degree tables + cadences + CoF distance + HMM emission
3. Embellishments: secondary dominants and borrowed chords
4. Assembly: ChordLabel list with function labels

Key improvements over the original single-shot approach:
- Multi-candidate generation with quality scoring (pick best of N)
- Circle-of-fifths distance for chord-melody fit (FHARM §4.2.3)
- Phrase-level functional grouping — hierarchical, not flat (FHARM §4.3.1)
- Occasional non-chord-tone harmonizations for dissonance/interest (FHARM §5.1.5)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

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
# Circle of fifths distance (FHARM §4.2.3 — Koops et al. 2013)
#
# FHARM weights chord candidates by distance in the circle of fifths
# between the melody note and the chord root, because CoF distance
# correlates better with human perception of harmonic fit than linear
# pitch-class distance.
# ---------------------------------------------------------------------------

# Pitch classes ordered by circle of fifths: F-C-G-D-A-E-B-F#-C#-G#-D#-A#
_COF_ORDER = [5, 0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10]
_COF_POS = {pc: i for i, pc in enumerate(_COF_ORDER)}


def _cof_distance(pc_a: int, pc_b: int) -> int:
    """Distance in the circle of fifths between two pitch classes (0-6)."""
    d = abs(_COF_POS[pc_a % 12] - _COF_POS[pc_b % 12])
    return min(d, 12 - d)


# ---------------------------------------------------------------------------
# Phrase-level functional patterns (FHARM §4.3.1)
#
# Instead of flat bar-by-bar cycles, group bars into 4-bar phrases with
# internal functional structure. This creates hierarchical tension arcs
# that the FHARM paper's experts rated as more musical.
# ---------------------------------------------------------------------------

_PHRASE_PATTERNS_4 = [
    # Authentic cadence phrase — complete T→S→D→T cycle
    [HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT, HarmonicFunction.DOMINANT, HarmonicFunction.TONIC],
    # Half cadence phrase — ends on dominant (suspended feeling)
    [HarmonicFunction.TONIC, HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT, HarmonicFunction.DOMINANT],
    # Tonic return — S→T interplay before dominant
    [HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT, HarmonicFunction.TONIC, HarmonicFunction.DOMINANT],
    # Subdominant opening — starts away from tonic
    [HarmonicFunction.SUBDOMINANT, HarmonicFunction.TONIC, HarmonicFunction.DOMINANT, HarmonicFunction.TONIC],
    # Extended dominant preparation
    [HarmonicFunction.TONIC, HarmonicFunction.DOMINANT, HarmonicFunction.SUBDOMINANT, HarmonicFunction.DOMINANT],
]

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
    """Functional Harmony + HMM Emission Harmonizer.

    Generates multiple candidate progressions (FHARM §4) and selects the
    best one using a quality scoring function inspired by FHARM's HarmTrace
    parsing approach. Instead of counting CFG parse errors, we score on
    functional diversity, cadence quality, root variety, and CoF fit.
    """

    beam_width: int = 8
    chord_change: str = "bars"
    bar_grid: BarGrid | None = None
    embellish_rate: float = 0.30
    n_candidates: int = 8           # how many candidates to generate
    dissonance_rate: float = 0.15   # prob of considering non-plan chords

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

        diatonic = _build_diatonic_chords(scale)
        func_degrees = _build_functional_degrees(scale)
        observations = self._extract_observations(melody, change_points)
        gravity = MODAL_GRAVITY.get(scale.mode, [0])

        # FHARM §4: generate multiple candidates, select best
        best_result: list[ChordLabel] = []
        best_score = -1e9

        for _ in range(self.n_candidates):
            func_plan = self._plan_functions(T, change_points, tension_curve)
            chords = self._select_chords(
                func_plan, scale, diatonic, func_degrees, observations, gravity, T, change_points
            )
            if self.embellish_rate > 0:
                chords = self._apply_embellishments(chords, scale, T)
            labels = self._build_labels(chords, change_points, duration_beats)
            score = self._score_progression(labels, observations, gravity, scale)
            if score > best_score:
                best_score = score
                best_result = labels

        return best_result

    # ------------------------------------------------------------------
    # Phase 1: Functional Plan
    # ------------------------------------------------------------------

    def _plan_functions(
        self,
        n_bars: int,
        change_points: list[float],
        tension: TensionCurve | None,
    ) -> list[HarmonicFunction]:
        """Generate T/S/D function sequence."""
        if tension:
            plan = self._tension_based_plan(n_bars, change_points, tension)
        else:
            plan = self._phrase_based_plan(n_bars)

        # Enforce grammar: no D→S (weak progression)
        for i in range(1, len(plan)):
            if plan[i - 1] == HarmonicFunction.DOMINANT and plan[i] == HarmonicFunction.SUBDOMINANT:
                plan[i] = HarmonicFunction.TONIC

        return plan

    def _tension_based_plan(
        self,
        n_bars: int,
        change_points: list[float],
        tension: TensionCurve,
    ) -> list[HarmonicFunction]:
        """Map tension curve phases to functional categories."""
        plan: list[HarmonicFunction] = []
        for i in range(n_bars):
            beat = change_points[i]
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
        return plan

    def _phrase_based_plan(self, n_bars: int) -> list[HarmonicFunction]:
        """Group bars into 4-bar phrases with internal functional structure.

        Each phrase forms a hierarchical functional unit rather than a flat
        bar-by-bar sequence. The last phrase always resolves to tonic.
        """
        plan: list[HarmonicFunction] = []
        remaining = n_bars

        while remaining > 0:
            phrase_len = min(4, remaining)
            is_last = (remaining <= 4)

            if is_last and phrase_len >= 4:
                # Final phrase: force authentic cadence
                pattern = [
                    HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT,
                    HarmonicFunction.DOMINANT, HarmonicFunction.TONIC,
                ]
            elif is_last and phrase_len == 3:
                pattern = [
                    HarmonicFunction.SUBDOMINANT,
                    HarmonicFunction.DOMINANT,
                    HarmonicFunction.TONIC,
                ]
            elif is_last and phrase_len == 2:
                pattern = [HarmonicFunction.DOMINANT, HarmonicFunction.TONIC]
            elif is_last:
                pattern = [HarmonicFunction.TONIC]
            else:
                pattern = random.choice(_PHRASE_PATTERNS_4)

            plan.extend(pattern[:phrase_len])
            remaining -= phrase_len

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

        For each bar, score candidate degrees using HMM emission, CoF
        distance, gravity, and anti-repetition penalties. Occasionally
        consider degrees from other functional categories (dissonance).
        """
        result: list[tuple[int, int, HarmonicFunction]] = []
        degs = scale.degrees()

        # Cadence positions: only at structural D→T boundaries
        cadence_positions = set()
        for i in range(2, n_bars):
            if func_plan[i] == HarmonicFunction.TONIC and func_plan[i - 1] == HarmonicFunction.DOMINANT:
                if (i + 1) % 4 == 0 or i == n_bars - 1:
                    cadence_positions.add(i - 1)
                    cadence_positions.add(i)

        for i in range(n_bars):
            fn = func_plan[i]

            # Cadence override: force V→I at structural positions
            if i in cadence_positions and fn == HarmonicFunction.DOMINANT:
                deg = 5
                root_pc = int(round(degs[(deg - 1) % len(degs)]))
                result.append((root_pc, deg, HarmonicFunction.DOMINANT))
                continue

            if i in cadence_positions and fn == HarmonicFunction.TONIC:
                deg = 1
                root_pc = int(round(degs[(deg - 1) % len(degs)]))
                result.append((root_pc, deg, HarmonicFunction.TONIC))
                continue

            # Get candidates — primary function + occasional dissonance
            candidates = list(func_degrees.get(fn, [1]))
            if not candidates:
                candidates = [1]

            if random.random() < self.dissonance_rate:
                other_fns = [
                    f for f in (HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT, HarmonicFunction.DOMINANT)
                    if f != fn
                ]
                if other_fns:
                    alt_degs = func_degrees.get(random.choice(other_fns), [])
                    candidates.extend(alt_degs)

            # Dominant melody pitch class for CoF scoring
            melody_pc = self._dominant_melody_pc(observations[i]) if i < len(observations) else None

            best_deg = candidates[0]
            best_score = -1e9

            for deg in candidates:
                root_pc = int(round(degs[(deg - 1) % len(degs)]))
                quality = diatonic[(deg - 1) % len(diatonic)][1]

                # HMM emission score (scaled down — functional fit matters more)
                obs = observations[i] if i < len(observations) else []
                emit_score = self._score_emission(root_pc, quality, obs) * 0.3

                # Circle of fifths distance to melody (FHARM §4.2.3)
                cof_score = 0.0
                if melody_pc is not None:
                    cof_score = -_cof_distance(root_pc, melody_pc) * 0.5

                # Gravity bonus (characteristic degrees of the mode)
                grav_bonus = 3.0 if (deg - 1) in gravity else 0.0

                # Function match bonus — prefer chords matching the plan
                chord_fn = _degree_to_function(deg)
                fn_match = 2.0 if chord_fn == fn else -1.0

                # Anti-repetition penalties
                deg_penalty = -6.0 if result and result[-1][1] == deg else 0.0
                root_penalty = -5.0 if result and result[-1][0] == root_pc else 0.0

                # Quality repeat: penalize matching previous chord quality
                prev_quality = diatonic[(result[-1][1] - 1) % len(diatonic)][1] if result else None
                cur_quality = diatonic[(deg - 1) % len(diatonic)][1]
                quality_penalty = -8.0 if prev_quality == cur_quality else 0.0

                interval_penalty = 0.0
                if len(result) >= 2:
                    prev_iv = (result[-1][0] - result[-2][0]) % 12
                    this_iv = (root_pc - result[-1][0]) % 12
                    if prev_iv == this_iv and prev_iv != 0:
                        interval_penalty = -4.0

                aba_penalty = -3.0 if len(result) >= 2 and result[-2][0] == root_pc else 0.0

                # Random exploration noise so candidates differ
                noise = random.gauss(0, 1.5)

                score = (emit_score + cof_score + grav_bonus + fn_match
                         + deg_penalty + root_penalty + quality_penalty
                         + interval_penalty + aba_penalty + noise)
                if score > best_score:
                    best_score = score
                    best_deg = deg

            root_pc = int(round(degs[(best_deg - 1) % len(degs)]))
            actual_fn = _degree_to_function(best_deg)
            result.append((root_pc, best_deg, actual_fn))

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

    def _dominant_melody_pc(self, obs: list[tuple[int, float]]) -> int | None:
        """Extract the most prominent pitch class from observations."""
        if not obs:
            return None
        return max(obs, key=lambda x: x[1])[0]

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

            # Secondary dominant: V7/x targeting next chord
            if i + 1 < len(result) and fn == HarmonicFunction.DOMINANT:
                next_root = result[i + 1][0]
                sec_dom_root = (next_root + 7) % 12
                if sec_dom_root != root_pc:
                    result[i] = (sec_dom_root, deg, HarmonicFunction.SECONDARY)

            # Borrowed chord: from parallel mode
            elif fn == HarmonicFunction.SUBDOMINANT and random.random() < 0.3:
                if scale.mode in (Mode.HARMONIC_MINOR, Mode.MELODIC_MINOR, Mode.NATURAL_MINOR,
                                  Mode.AEOLIAN, Mode.DORIAN, Mode.PHRYGIAN):
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
            if idx + 1 < total:
                return Quality.DOMINANT7
            return Quality.MAJOR
        if fn == HarmonicFunction.SECONDARY:
            return Quality.DOMINANT7
        if fn == HarmonicFunction.SUBDOMINANT:
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
    # Candidate quality scoring (inspired by FHARM §4.3 parsing)
    #
    # FHARM uses HarmTrace CFG parsing to score candidates (fewest parse
    # errors = best). We approximate this with a weighted scoring function
    # that measures the same qualities: functional correctness, diversity,
    # cadence strength, and melody-chord fit.
    # ------------------------------------------------------------------

    def _score_progression(
        self,
        chords: list[ChordLabel],
        observations: list[list[tuple[int, float]]],
        gravity: list[int],
        scale: Scale,
    ) -> float:
        """Score a complete progression. Higher = better."""
        if len(chords) < 2:
            return 0.0

        score = 0.0
        n = len(chords)

        # Root diversity (FHARM experts preferred varied roots)
        roots = set(c.root for c in chords)
        score += len(roots) * 2.0

        # Functional completeness (all three T/S/D present)
        funcs = set(c.function for c in chords if c.function)
        if HarmonicFunction.TONIC in funcs:
            score += 3.0
        if HarmonicFunction.SUBDOMINANT in funcs:
            score += 3.0
        if HarmonicFunction.DOMINANT in funcs:
            score += 3.0

        # Cadence quality — D→T at structural positions
        for i in range(1, n):
            if (chords[i - 1].function == HarmonicFunction.DOMINANT
                    and chords[i].function == HarmonicFunction.TONIC
                    and ((i + 1) % 4 == 0 or i == n - 1)):
                score += 5.0

        # Root interval diversity (anti-monotony)
        intervals = set()
        for i in range(1, n):
            iv = (chords[i].root - chords[i - 1].root) % 12
            intervals.add(iv)
        score += len(intervals) * 1.5

        # Penalty: identical consecutive bars
        for i in range(1, n):
            if chords[i].root == chords[i - 1].root and chords[i].quality == chords[i - 1].quality:
                score -= 3.0

        # Penalty: D→S grammar violation
        for i in range(1, n):
            if (chords[i - 1].function == HarmonicFunction.DOMINANT
                    and chords[i].function == HarmonicFunction.SUBDOMINANT):
                score -= 10.0

        # Phrase-level functional completeness (each 4-bar phrase should
        # have all three functions — reflects hierarchical structure)
        for start in range(0, n - 3, 4):
            phrase_funcs = set(c.function for c in chords[start:start + 4] if c.function)
            if HarmonicFunction.TONIC in phrase_funcs:
                score += 1.0
            if HarmonicFunction.DOMINANT in phrase_funcs:
                score += 1.0
            if HarmonicFunction.SUBDOMINANT in phrase_funcs:
                score += 1.0
            if len(phrase_funcs) >= 3:
                score += 3.0

        # Circle of fifths melody-chord fit (FHARM §4.2.3)
        for i, c in enumerate(chords):
            if i < len(observations) and observations[i]:
                melody_pc = self._dominant_melody_pc(observations[i])
                if melody_pc is not None:
                    score -= _cof_distance(c.root, melody_pc) * 0.3

        # Ending quality (authentic cadence preferred)
        if chords[-1].function == HarmonicFunction.TONIC:
            score += 3.0
        if n >= 2 and chords[-1].function == HarmonicFunction.TONIC and chords[-2].function == HarmonicFunction.DOMINANT:
            score += 4.0

        # Random noise so that equally-good candidates don't collapse to one
        score += random.gauss(0, 2.0)

        return score

    # ------------------------------------------------------------------
    # Observation extraction
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
