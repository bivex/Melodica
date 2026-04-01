"""
_hmm_core.py — HMM-based harmonizers.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

from melodica.harmonize._hmm_helpers import (
    _chord_pcs_for_degree, _voice_leading_cost, _melody_fits_chord, _build_diatonic_chords,
    _CADENCE_BONUSES, _FUNCTION_MAP, _FUNCTION_RULES_HMM2, _SECONDARY_DOMINANTS, _EXTENSIONS,
)
from melodica.types import ChordLabel, Quality, HarmonicFunction, Scale, Mode, NoteInfo

@dataclass
class HMMHarmonizer:
    """
    Hidden Markov Model harmonizer.

    States = diatonic chords (I, ii, iii, IV, V, vi, vii°)
    Observations = melody pitch classes
    Uses Viterbi to find most likely chord sequence.

    melody_weight:  how much melody-chord fit matters (0-1)
    voice_weight:   how much voice leading matters (0-1)
    transition_weight: how much chord transition probability matters (0-1)
    """

    melody_weight: float = 0.4
    voice_weight: float = 0.3
    transition_weight: float = 0.3
    allow_extensions: bool = False
    chord_change: str = "bars"

    def harmonize(
        self,
        melody: list[NoteInfo],
        scale: Scale,
        duration_beats: float,
    ) -> list[ChordLabel]:
        if not melody or not scale.degrees():
            return []

        # Build states (diatonic chords)
        chords_def = _build_diatonic_chords(scale)
        n_states = len(chords_def)

        # Group melody by chord change points
        change_points = self._get_change_points(duration_beats)
        observations = self._extract_observations(melody, change_points)

        if not observations:
            return []

        # Transition matrix (simple functional rules)
        trans = self._build_transition_matrix(n_states)

        # Emission probabilities
        emissions = self._build_emissions(observations, chords_def, scale)

        # Viterbi
        path = self._viterbi(trans, emissions, n_states)

        # Build ChordLabels
        result = []
        for i, state in enumerate(path):
            root_pc, quality = chords_def[state]
            start = change_points[i]
            dur = (
                (change_points[i + 1] - start)
                if i + 1 < len(change_points)
                else duration_beats - start
            )
            result.append(
                ChordLabel(
                    root=root_pc,
                    quality=quality,
                    start=round(start, 6),
                    duration=round(dur, 6),
                    degree=state + 1,
                )
            )

        return result

    def _build_transition_matrix(self, n: int) -> list[list[float]]:
        """Build chord transition probability matrix."""
        # Functional rules: T→S, S→D, D→T
        mat = [[1.0 / n] * n for _ in range(n)]
        # I→IV, I→V, IV→V, V→I, vi→IV, ii→V
        rules = {
            0: {3: 0.35, 4: 0.30, 1: 0.15, 5: 0.10, 2: 0.05, 6: 0.05},
            1: {4: 0.45, 0: 0.20, 3: 0.15, 5: 0.10, 2: 0.05, 6: 0.05},
            2: {5: 0.35, 3: 0.25, 4: 0.20, 1: 0.10, 0: 0.05, 6: 0.05},
            3: {4: 0.35, 0: 0.25, 1: 0.15, 5: 0.10, 2: 0.10, 6: 0.05},
            4: {0: 0.40, 5: 0.25, 3: 0.15, 1: 0.10, 2: 0.05, 6: 0.05},
            5: {1: 0.30, 4: 0.25, 3: 0.20, 0: 0.10, 2: 0.10, 6: 0.05},
            6: {0: 0.50, 4: 0.25, 3: 0.15, 1: 0.05, 2: 0.05},
        }
        for i, row in rules.items():
            for j, w in row.items():
                mat[i][j] = w
        return mat

    def _build_emissions(
        self,
        observations: list[list[int]],
        chords_def: list[tuple[int, Quality]],
        scale: Scale,
    ) -> list[list[float]]:
        """Build emission probabilities for each time step."""
        result = []
        for obs_pcs in observations:
            probs = []
            for root_pc, quality in chords_def:
                chord_pcs = _chord_pcs_for_degree(root_pc, quality)
                # Count how many melody notes fit this chord
                fit_count = sum(1 for pc in obs_pcs if pc in chord_pcs)
                total = len(obs_pcs) if obs_pcs else 1
                # Emission = proportion of melody notes that fit + small base
                prob = (fit_count / total) * self.melody_weight + 0.1
                # Voice leading bonus: penalize distant chords
                if len(chord_pcs) > 0:
                    avg_pc = sum(obs_pcs) / len(obs_pcs)
                    dist = _voice_leading_cost([int(avg_pc)], chord_pcs)
                    prob += (1.0 - dist / 6.0) * self.voice_weight
                probs.append(prob)
            # Normalize
            total = sum(probs)
            result.append([p / total for p in probs])
        return result

    def _viterbi(
        self,
        trans: list[list[float]],
        emissions: list[list[float]],
        n_states: int,
    ) -> list[int]:
        """Viterbi algorithm for finding most likely state sequence."""
        T = len(emissions)
        if T == 0:
            return [0]

        # Forward pass
        dp = [[0.0] * n_states for _ in range(T)]
        backtrack = [[0] * n_states for _ in range(T)]

        for s in range(n_states):
            dp[0][s] = emissions[0][s]
            backtrack[0][s] = 0

        for t in range(1, T):
            for s in range(n_states):
                best_prob = -1.0
                best_prev = 0
                for prev in range(n_states):
                    prob = dp[t - 1][prev] * trans[prev][s] * emissions[t][s]
                    if prob > best_prob:
                        best_prob = prob
                        best_prev = prev
                dp[t][s] = best_prob
                backtrack[t][s] = best_prev

        # Backtrack
        best_last = max(range(n_states), key=lambda s: dp[T - 1][s])
        path = [best_last]
        for t in range(T - 1, 0, -1):
            path.append(backtrack[t][path[-1]])
        path.reverse()
        return path

    def _extract_observations(
        self,
        melody: list[NoteInfo],
        change_points: list[float],
    ) -> list[list[int]]:
        """Extract pitch classes for each chord change interval."""
        observations = []
        sorted_m = sorted(melody, key=lambda n: n.start)
        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")
            pcs = [n.pitch % 12 for n in sorted_m if cp <= n.start < next_cp]
            observations.append(pcs if pcs else [0])
        return observations

    def _get_change_points(self, duration: float) -> list[float]:
        points = []
        step = (
            4.0
            if self.chord_change == "bars"
            else 2.0
            if self.chord_change == "strong_beats"
            else 1.0
        )
        t = 0.0
        while t < duration:
            points.append(t)
            t += step
        return points
@dataclass
class HMM2Harmonizer:
    """
    Pro-level HMM with functional layer, cadence bonuses, and repetition penalty.

    score = melody_fit + transition_prob + functional_score
          + cadence_bonus - repetition_penalty

    melody_weight:         weight for melody-chord fit
    transition_weight:     weight for chord transition probability
    functional_weight:     weight for T/S/D functional rules
    cadence_weight:        bonus for cadential patterns (V→I, etc.)
    repetition_penalty:    penalty for same chord repeated
    phrase_length:         bars per phrase (cadence prefer at phrase end)
    chord_change:          "bars" | "strong_beats" | "beats"
    """

    melody_weight: float = 0.30
    transition_weight: float = 0.25
    functional_weight: float = 0.20
    cadence_weight: float = 0.15
    repetition_penalty: float = 0.10
    phrase_length: int = 4
    chord_change: str = "bars"

    def harmonize(
        self,
        melody: list[NoteInfo],
        scale: Scale,
        duration_beats: float,
    ) -> list[ChordLabel]:
        if not melody or not scale.degrees():
            return []

        chords_def = _build_diatonic_chords(scale)
        n = len(chords_def)
        change_points = self._get_change_points(duration_beats)
        observations = self._extract_observations(melody, change_points)
        T = len(observations)
        if T == 0:
            return []

        bars_per_change = 4.0 / (4.0 if self.chord_change == "bars" else 2.0)

        # Transition matrix
        trans = self._build_transition_matrix(n)

        # Forward pass with custom scoring
        dp = [[float("-inf")] * n for _ in range(T)]
        backtrack = [[0] * n for _ in range(T)]

        for s in range(n):
            dp[0][s] = self._score_state(
                0, s, None, observations[0], chords_def, change_points, bars_per_change
            )

        for t in range(1, T):
            for s in range(n):
                for prev in range(n):
                    score = dp[t - 1][prev]
                    score += self._score_transition(prev, s, trans)
                    score += self._score_state(
                        t, s, prev, observations[t], chords_def, change_points, bars_per_change
                    )
                    if score > dp[t][s]:
                        dp[t][s] = score
                        backtrack[t][s] = prev

        # Backtrack
        best_last = max(range(n), key=lambda s: dp[T - 1][s])
        path = [best_last]
        for t in range(T - 1, 0, -1):
            path.append(backtrack[t][path[-1]])
        path.reverse()

        # Build ChordLabels
        result = []
        for i, state in enumerate(path):
            root_pc, quality = chords_def[state]
            start = change_points[i]
            dur = (
                (change_points[i + 1] - start)
                if i + 1 < len(change_points)
                else duration_beats - start
            )
            result.append(
                ChordLabel(
                    root=root_pc,
                    quality=quality,
                    start=round(start, 6),
                    duration=round(dur, 6),
                    degree=state + 1,
                )
            )
        return result

    def _score_state(
        self, t, state, prev_state, obs_pcs, chords_def, change_points, bars_per_change
    ):
        """score = melody_fit + functional + cadence - repetition."""
        rpc, quality = chords_def[state]
        chord_pcs = _chord_pcs_for_degree(rpc, quality)

        # 1. Melody fit
        melody_fit = (
            sum(1 for p in obs_pcs if p in chord_pcs) / max(1, len(obs_pcs))
        ) * self.melody_weight

        # 2. Functional score
        func = _FUNCTION_MAP.get(state, 1)  # default to subdominant
        if prev_state is not None:
            prev_func = _FUNCTION_MAP.get(prev_state, 1)
            func_weight = _FUNCTION_RULES_HMM2.get(prev_func, {}).get(func, 0.1)
        else:
            func_weight = 0.5
        func_score = func_weight * self.functional_weight

        # 3. Cadence bonus
        cadence_bonus = 0.0
        if prev_state is not None:
            pair = (prev_state, state)
            cadence_bonus = _CADENCE_BONUSES.get(pair, 0.0) * self.cadence_weight

        # Phrase-end cadence bonus
        beat_pos = change_points[t] if t < len(change_points) else 0
        bar_pos = beat_pos / 4.0
        is_phrase_end = bar_pos > 0 and bar_pos % self.phrase_length == 0
        if is_phrase_end and state == 0:  # end on tonic
            cadence_bonus += 0.3 * self.cadence_weight

        # 4. Repetition penalty
        rep_penalty = 0.0
        if prev_state is not None and state == prev_state:
            rep_penalty = self.repetition_penalty

        return melody_fit + func_score + cadence_bonus - rep_penalty

    def _score_transition(self, prev, curr, trans):
        return trans[prev][curr] * self.transition_weight

    def _build_transition_matrix(self, n):
        mat = [[0.15] * n for _ in range(n)]
        rules = {
            0: {3: 0.35, 4: 0.30, 1: 0.15, 5: 0.10, 2: 0.05, 6: 0.05},
            1: {4: 0.45, 0: 0.20, 3: 0.15, 5: 0.10, 2: 0.05, 6: 0.05},
            2: {5: 0.35, 3: 0.25, 4: 0.20, 1: 0.10, 0: 0.05, 6: 0.05},
            3: {4: 0.35, 0: 0.25, 1: 0.15, 5: 0.10, 2: 0.10, 6: 0.05},
            4: {0: 0.40, 5: 0.25, 3: 0.15, 1: 0.10, 2: 0.05, 6: 0.05},
            5: {1: 0.30, 4: 0.25, 3: 0.20, 0: 0.10, 2: 0.10, 6: 0.05},
            6: {0: 0.50, 4: 0.25, 3: 0.15, 1: 0.05, 2: 0.05},
        }
        for i, row in rules.items():
            for j, w in row.items():
                mat[i][j] = w
        return mat

    def _extract_observations(self, melody, change_points):
        sorted_m = sorted(melody, key=lambda n: n.start)
        obs = []
        for i, cp in enumerate(change_points):
            ncp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")
            obs.append([n.pitch % 12 for n in sorted_m if cp <= n.start < ncp] or [0])
        return obs

    def _get_change_points(self, duration):
        step = (
            4.0
            if self.chord_change == "bars"
            else 2.0
            if self.chord_change == "strong_beats"
            else 1.0
        )
        pts, t = [], 0.0
        while t < duration:
            pts.append(t)
            t += step
        return pts
@dataclass
class HMM3Harmonizer:
    """
    Pro-level harmonizer with beam search, secondary dominants, extensions,
    and rhythm-aware scoring.

    score = melody_fit + transition + functional + cadence + secondary_dom
          + extension_bonus - repetition - weak_beat_penalty

    beam_width:           number of candidates per time step
    allow_secondary_dom:  use V/V, V/ii, etc.
    allow_extensions:     use maj7, dom7, m7
    rhythm_aware:         weight melody fit by beat strength
    phrase_length:        bars per phrase
    """

    beam_width: int = 5
    melody_weight: float = 0.25
    transition_weight: float = 0.20
    functional_weight: float = 0.15
    cadence_weight: float = 0.15
    secondary_dom_weight: float = 0.10
    extension_weight: float = 0.05
    repetition_penalty: float = 0.10
    rhythm_aware: bool = True
    allow_secondary_dom: bool = True
    allow_extensions: bool = True
    phrase_length: int = 4
    chord_change: str = "bars"

    def harmonize(
        self,
        melody: list[NoteInfo],
        scale: Scale,
        duration_beats: float,
    ) -> list[ChordLabel]:
        if not melody or not scale.degrees():
            return []

        chords_def = _build_diatonic_chords(scale)
        change_points = self._get_change_points(duration_beats)
        observations = self._extract_observations(melody, change_points)
        T = len(observations)
        if T == 0:
            return []

        # Build extended chord catalog: (root_pc, quality, degree)
        catalog = self._build_catalog(chords_def, scale)
        n_cat = len(catalog)

        # Transition matrix over catalog
        trans = self._build_transitions(catalog, chords_def)

        # Beam search
        # State: (cumulative_score, list_of_indices)
        beams: list[tuple[float, list[int]]] = []

        # Initialize beams
        for s in range(n_cat):
            score = self._score_step(
                0, s, None, observations, catalog, change_points, melody, scale
            )
            beams.append((score, [s]))

        # Expand beam by beam
        for t in range(1, T):
            new_beams: list[tuple[float, list[int]]] = []
            for score, path in beams:
                prev = path[-1]
                for s in range(n_cat):
                    step_score = self._score_step(
                        t, s, prev, observations, catalog, change_points, melody, scale
                    )
                    trans_score = trans[prev][s] * self.transition_weight
                    new_score = score + step_score + trans_score
                    new_beams.append((new_score, path + [s]))
            # Keep top beam_width
            new_beams.sort(key=lambda x: -x[0])
            beams = new_beams[: self.beam_width]

        # Best beam
        if not beams:
            return []
        best_score, best_path = beams[0]

        # Build ChordLabels
        result = []
        for i, cat_idx in enumerate(best_path):
            root_pc, quality, degree = catalog[cat_idx]
            start = change_points[i]
            dur = (
                (change_points[i + 1] - start)
                if i + 1 < len(change_points)
                else duration_beats - start
            )
            result.append(
                ChordLabel(
                    root=root_pc,
                    quality=quality,
                    start=round(start, 6),
                    duration=round(dur, 6),
                    degree=degree,
                )
            )
        return result

    def _build_catalog(self, chords_def, scale):
        """Build full chord catalog: diatonic + secondary dominants."""
        catalog = []
        for i, (rpc, qual) in enumerate(chords_def):
            catalog.append((rpc, qual, i + 1))
            # Add extensions
            if self.allow_extensions:
                for ext_qual in _EXTENSIONS.get(i, []):
                    if ext_qual != qual:
                        catalog.append((rpc, ext_qual, i + 1))
        # Add secondary dominants
        if self.allow_secondary_dom:
            degs = scale.degrees()
            for target_deg, dom_options in _SECONDARY_DOMINANTS.items():
                for dom_offset, dom_qual in dom_options:
                    dom_root = (
                        degs[(target_deg - 1 + dom_offset) % len(degs)]
                        if target_deg - 1 + dom_offset < len(degs)
                        else (degs[target_deg - 1] + dom_offset) % 12
                    )
                    catalog.append((int(dom_root), dom_qual, 0))
        return catalog

    def _build_transitions(self, catalog, chords_def):
        n = len(catalog)
        mat = [[0.1] * n for _ in range(n)]
        # Map catalog entries to their "logical" degree for transition rules
        for i, (rpc_i, qual_i, deg_i) in enumerate(catalog):
            for j, (rpc_j, qual_j, deg_j) in enumerate(catalog):
                # Functional transition
                if deg_i > 0 and deg_j > 0:
                    di, dj = deg_i - 1, deg_j - 1
                    rules = {
                        0: {3: 0.35, 4: 0.30, 1: 0.15, 5: 0.10},
                        1: {4: 0.45, 0: 0.20},
                        3: {4: 0.35, 0: 0.25},
                        4: {0: 0.40, 5: 0.25},
                        5: {1: 0.30, 4: 0.25},
                    }
                    mat[i][j] = rules.get(di, {}).get(dj, 0.1)
                # Secondary dominant resolution
                elif deg_i == 0 and deg_j > 0:
                    mat[i][j] = 0.4  # secondary dom resolves to target
                else:
                    mat[i][j] = 0.1
        return mat

    def _score_step(
        self, t, cat_idx, prev_idx, observations, catalog, change_points, melody, scale
    ):
        rpc, quality, degree = catalog[cat_idx]
        chord_pcs = _chord_pcs_for_degree(rpc, quality)
        obs = observations[t] if t < len(observations) else [0]

        # 1. Melody fit
        beat_strength = self._beat_strength(t, change_points, melody) if self.rhythm_aware else 1.0
        melody_fit = (
            (sum(1 for p in obs if p in chord_pcs) / max(1, len(obs)))
            * self.melody_weight
            * beat_strength
        )

        # 2. Functional score
        func_score = 0.0
        if prev_idx is not None and degree > 0:
            prev_deg = catalog[prev_idx][2]
            if prev_deg > 0:
                good = {(1, 4), (1, 5), (4, 5), (5, 1), (5, 6), (6, 2), (2, 5), (4, 1)}
                if (prev_deg, degree) in good:
                    func_score = 0.8 * self.functional_weight

        # 3. Cadence bonus
        cadence = 0.0
        if prev_idx is not None:
            prev_deg = catalog[prev_idx][2]
            pair = (prev_deg - 1 if prev_deg > 0 else -1, degree - 1 if degree > 0 else -1)
            cadence = _CADENCE_BONUSES.get(pair, 0.0) * self.cadence_weight
        beat_pos = change_points[t] if t < len(change_points) else 0
        is_phrase_end = beat_pos > 0 and (beat_pos / 4.0) % self.phrase_length == 0
        if is_phrase_end and degree == 1:
            cadence += 0.3 * self.cadence_weight

        # 4. Secondary dominant bonus
        sd_bonus = 0.0
        if degree == 0:  # secondary dominant
            sd_bonus = 0.5 * self.secondary_dom_weight

        # 5. Extension bonus
        ext_bonus = 0.0
        if quality in (Quality.MAJOR7, Quality.DOMINANT7, Quality.MINOR7, Quality.HALF_DIM7):
            ext_bonus = 0.3 * self.extension_weight

        # 6. Repetition penalty
        rep = 0.0
        if prev_idx is not None and cat_idx == prev_idx:
            rep = self.repetition_penalty

        return melody_fit + func_score + cadence + sd_bonus + ext_bonus - rep

    def _beat_strength(self, t, change_points, melody):
        """Rhythm-aware: strong beats get higher melody weight."""
        beat_pos = change_points[t] if t < len(change_points) else 0
        beat_in_bar = beat_pos % 4.0
        if beat_in_bar < 0.1:
            return 1.3  # beat 1 = strongest
        elif abs(beat_in_bar - 2.0) < 0.1:
            return 1.1  # beat 3 = medium
        else:
            return 0.8  # weak beats

    def _extract_observations(self, melody, change_points):
        sorted_m = sorted(melody, key=lambda n: n.start)
        obs = []
        for i, cp in enumerate(change_points):
            ncp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")
            obs.append([n.pitch % 12 for n in sorted_m if cp <= n.start < ncp] or [0])
        return obs

    def _get_change_points(self, duration):
        step = (
            4.0
            if self.chord_change == "bars"
            else 2.0
            if self.chord_change == "strong_beats"
            else 1.0
        )
        pts, t = [], 0.0
        while t < duration:
            pts.append(t)
            t += step
        return pts
