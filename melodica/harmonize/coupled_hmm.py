# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
coupled_hmm.py — Hierarchical HMM Harmonizer (12 chord types).
Based on research by Dmitri Tymoczko and Mark Newman (2024).

Layer 1: Notes -> Chords via Viterbi over 144 states (12 roots x 12 types).
Layer 2: Chords -> Keys via Viterbi over 12 roots x N key types.

Weights loaded from melodica/harmonize/weights/ (trained by train_full_modes.py).
"""

from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from melodica.theory.modes import MODE_DATABASE, get_mode_intervals, Mode
from melodica.types import BarGrid, ChordLabel, Quality, Scale, NoteInfo

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

N_TONES = 12
N_TYPES = 12  # Maj, Min, Dim, Aug, sus2, sus4, Maj7, Min7, Dom7, Maj9, Min9, Add9

# List of all supported modes for Layer 2
MODES_LIST = list(MODE_DATABASE.keys())
N_KEY_TYPES = len(MODES_LIST)

# Mapping from training type index to Quality enum
TYPE_TO_QUALITY = [
    Quality.MAJOR,       # 0
    Quality.MINOR,       # 1
    Quality.DIMINISHED,  # 2
    Quality.AUGMENTED,   # 3
    Quality.SUS2,        # 4
    Quality.SUS4,        # 5
    Quality.MAJOR7,      # 6
    Quality.MINOR7,      # 7
    Quality.DOMINANT7,   # 8
    Quality.MAJOR9,      # 9
    Quality.MINOR9,      # 10
    Quality.ADD9,        # 11
]

# Reverse map: Quality → type index (for constraints)
_QUALITY_TO_TYPE = {q: i for i, q in enumerate(TYPE_TO_QUALITY)}

# Fallback map for unsupported qualities → closest supported type
_QUALITY_FALLBACK = {
    Quality.HALF_DIM7: Quality.MINOR7,
    Quality.FULL_DIM7: Quality.DIMINISHED,
    Quality.POWER: Quality.MAJOR,
    Quality.DOM7_FLAT9: Quality.DOMINANT7,
    Quality.DOM7_SHARP9: Quality.DOMINANT7,
    Quality.DOM7_SHARP11: Quality.DOMINANT7,
    Quality.ALTERED_DOMINANT: Quality.DOMINANT7,
    Quality.PHRYGIAN_MAJOR: Quality.MAJOR,
    Quality.LYDIAN_AUG: Quality.AUGMENTED,
}


def _resolve_type_idx(quality: Quality) -> int:
    """Map any Quality to a valid HMM type index, with fallback."""
    idx = _QUALITY_TO_TYPE.get(quality)
    if idx is not None:
        return idx
    fallback = _QUALITY_FALLBACK.get(quality, Quality.MAJOR)
    return _QUALITY_TO_TYPE[fallback]

# ---------------------------------------------------------------------------
# Weight Loading
# ---------------------------------------------------------------------------

_WEIGHTS_DIR = Path(__file__).parent / "weights"


def _load_weights():
    """Load trained HMM weights from files."""
    pnote_path = _WEIGHTS_DIR / "pnote_full.txt"
    pchange_path = _WEIGHTS_DIR / "pchange_full.npy"

    if not pnote_path.exists() or not pchange_path.exists():
        raise FileNotFoundError(
            f"Trained weights not found in {_WEIGHTS_DIR}. "
            "Run scripts/train_full_modes.py first."
        )

    # pnote: shape [12, 6] — pnote[pitch_offset, chord_type]
    pnote = np.loadtxt(pnote_path)

    # pchange: shape [6, 12, 6] — pchange[type_prev, interval, type_next]
    pchange = np.load(pchange_path)

    return pnote, pchange


# Load once at module level
PNOTE, PCHANGE = _load_weights()

# Pre-compute log versions for Viterbi (add small epsilon to avoid log(0))
_EPS = 1e-8
LOG_PNOTE = np.log(np.clip(PNOTE, _EPS, 1.0))
LOG_NOT_PNOTE = np.log(np.clip(1.0 - PNOTE, _EPS, 1.0))
LOG_PCHANGE = np.log(np.clip(PCHANGE, _EPS, 1.0))

# ---------------------------------------------------------------------------
# Universal Modal Priors (Layer 2)
# ---------------------------------------------------------------------------

def _init_modal_priors():
    """Dynamically build priors for all 78 modes."""
    # ν: P(chord_type | key_type)
    type_priors = np.full((N_KEY_TYPES, N_TYPES), 0.05)
    # κ: P(root_offset | key_type)
    offset_logs = np.full((N_KEY_TYPES, N_TONES), math.log(0.01))
    
    # Chord type definitions (3rd, 5th, 7th, 9th) for compatibility checking
    type_intervals = [
        (4, 7, None, None), # Major
        (3, 7, None, None), # Minor
        (3, 6, None, None), # Dim
        (4, 8, None, None), # Aug
        (2, 7, None, None), # sus2
        (5, 7, None, None), # sus4
        (4, 7, 11, None),   # Major7
        (3, 7, 10, None),   # Minor7
        (4, 7, 10, None),   # Dominant7
        (4, 7, 11, 2),      # Major9
        (3, 7, 10, 2),      # Minor9
        (4, 7, None, 2),    # Add9
    ]

    for m_idx, mode in enumerate(MODES_LIST):
        intervals = get_mode_intervals(mode)
        scale_pcs = {round(iv) % 12 for iv in intervals}
        
        # 1. Root offsets: high weight for notes in scale
        for pc in scale_pcs:
            offset_logs[m_idx, pc] = math.log(0.8 / len(scale_pcs))
            
        # 2. Chord types: check which types fit the scale notes best
        for t_idx, (third, fifth, seventh, ninth) in enumerate(type_intervals):
            # A chord type is "diatonic" if its notes are generally found in the mode
            fit_score = 0
            if third in scale_pcs: fit_score += 1
            if fifth in scale_pcs: fit_score += 1
            if seventh is not None and seventh in scale_pcs: fit_score += 1
            if ninth is not None and ninth in scale_pcs: fit_score += 1
            
            # Base probability based on fit
            # Higher reward for 9ths in cinematic context
            if fit_score >= 3:
                type_priors[m_idx, t_idx] = 0.35 if t_idx >= 9 else 0.25
            elif fit_score == 2:
                type_priors[m_idx, t_idx] = 0.15
            
            # Special case for Dominant 7 (often used even if not strictly diatonic)
            if t_idx == 8 and 4 in scale_pcs and 10 in scale_pcs:
                type_priors[m_idx, t_idx] = 0.20
            
        # Normalize priors
        type_priors[m_idx] /= type_priors[m_idx].sum()
        
    return type_priors, offset_logs

KEY_TYPE_PRIOR, KEY_OFFSET_LOG = _init_modal_priors()
LOG_KEY_TYPE_PRIOR = np.log(KEY_TYPE_PRIOR + _EPS)


# ---------------------------------------------------------------------------
# Coupled HMM Configuration & Harmonizer
# ---------------------------------------------------------------------------

@dataclass
class HMMConfig:
    """Configuration hyperparameters for CoupledHMMHarmonizer."""
    anti_stagnation_penalty: float = 2.0
    interval_diversity_penalty: float = 1.5
    tension_weight: float = 4.0
    key_coupling_weight: float = 0.5
    tonic_bias: float = 2.0
    epsilon: float = 1e-8
    emission_weight: float = 1.0  # Hyperparameter to scale emissions


@dataclass
class WeightedNote:
    pitch_class: int
    weight: float


# ---------------------------------------------------------------------------
# Coupled HMM Harmonizer
# ---------------------------------------------------------------------------

@dataclass
class CoupledHMMHarmonizer:
    """Hierarchical HMM Harmonizer with Duration and Metric Weighting."""
    beam_width: int = 12
    chord_change: str = "bars"
    bar_grid: BarGrid | None = None
    config: HMMConfig = field(default_factory=HMMConfig)

    def harmonize(
        self,
        melody: list[NoteInfo],
        initial_scale: Scale,
        duration_beats: float,
        constraints: list[ChordLabel] | None = None,
        tension_curve: Any | None = None
    ) -> list[ChordLabel]:
        if not melody:
            return []

        # 1. Prepare observations
        change_points = self._get_change_points(duration_beats)
        observations = self._extract_observations(melody, change_points)
        T = len(observations)

        # 1b. Snap constraints to change points
        if constraints and change_points:
            constraints = self._snap_constraints(constraints, change_points)

        # 2. Pass 1: Get initial draft chord sequence (unbiased by key layer)
        draft_chords = self._viterbi_chords(
            observations, initial_scale, change_points, constraints, tension_curve, key_path=None
        )

        # 3. Pass 2: Estimate key center sequence (Layer 2) from initial chords
        key_path = self._viterbi_keys(draft_chords)

        # 4. Pass 3: Refined chord sequence, now coupled to estimated key centers
        chord_path = self._viterbi_chords(
            observations, initial_scale, change_points, constraints, tension_curve, key_path=key_path
        )

        # 5. Build result
        result = []
        for i, (root, t_idx) in enumerate(chord_path):
            quality = TYPE_TO_QUALITY[t_idx]

            start = change_points[i]
            dur = (change_points[i + 1] - start) if i + 1 < len(change_points) else duration_beats - start

            result.append(ChordLabel(
                root=root, quality=quality,
                start=round(start, 6), duration=round(dur, 6)
            ))

        return result

    def _viterbi_chords(
        self, 
        obs: list[list[WeightedNote]], 
        scale: Scale,
        change_points: list[float],
        constraints: list[ChordLabel] | None = None,
        tension_curve: Any | None = None,
        key_path: list[tuple[int, int]] | None = None
    ) -> list[tuple[int, int]]:
        """Find most likely chord sequence using 2nd-order state-expanded Viterbi (1728 states)."""
        T = len(obs)
        if T == 0:
            return []

        NEG_INF = -1e12

        # Pre-compute emissions via vectorized _log_emit_chord
        emit = np.zeros((T, N_TONES, N_TYPES))
        base_not_pnote = LOG_NOT_PNOTE.sum(axis=0)  # [N_TYPES]

        for t_step in range(T):
            wpcs = obs[t_step]
            if not wpcs:
                emit[t_step] = -20.0
                continue
            
            step_emit = np.tile(base_not_pnote, (N_TONES, 1))
            total_w = 0.0

            for wn in wpcs:
                off = np.arange(N_TONES, dtype=np.intp)
                off = (wn.pitch_class - off) % N_TONES
                step_emit += wn.weight * (LOG_PNOTE[off] - LOG_NOT_PNOTE[off])
                total_w += wn.weight

            emit[t_step] = (step_emit / (total_w + 1e-6)) * self.config.emission_weight

        # Tension indices
        STABLE_INDICES = {0, 1, 11}
        UNSTABLE_INDICES = {2, 3, 8}

        # DP table of shape [T, 12, 12, 12] where dimensions are:
        # dp[t, r_curr, k_curr, r_prev]
        # backtrack stores predecessor state's (k_prev, r_prevprev) encoded as: k_prev * 12 + r_prevprev
        dp = np.full((T, 12, 12, 12), NEG_INF)
        backtrack = np.zeros((T, 12, 12, 12), dtype=np.int32)

        # Init step (t = 0)
        init_scores = emit[0].copy()
        if scale.root is not None:
            init_scores[scale.root, :] += self.config.tonic_bias

        if tension_curve:
            tau = tension_curve.tension_at(change_points[0])
            for k in range(N_TYPES):
                if k in UNSTABLE_INDICES:
                    init_scores[:, k] += tau * self.config.tension_weight
                elif k in STABLE_INDICES:
                    init_scores[:, k] += (1.0 - tau) * self.config.tension_weight

        if key_path:
            key_root, key_type = key_path[0]
            for r in range(N_TONES):
                bias = self.config.key_coupling_weight * (
                    KEY_OFFSET_LOG[key_type, (r - key_root) % 12] 
                    + LOG_KEY_TYPE_PRIOR[key_type]
                )
                init_scores[r, :] += bias

        if constraints:
            cp = change_points[0]
            target = next((c for c in constraints if c.start <= cp < c.start + c.duration), None)
            if target:
                t_idx = _resolve_type_idx(target.quality)
                for r in range(N_TONES):
                    for k in range(N_TYPES):
                        if r != target.root or k != t_idx:
                            init_scores[r, k] = NEG_INF

        # Initialize all possible predecessor roots with the same initial score
        for r_prev in range(12):
            dp[0, :, :, r_prev] = init_scores

        # Forward pass
        for t_step in range(1, T):
            cp = change_points[t_step]
            tau = tension_curve.tension_at(cp) if tension_curve else 0.5

            target_chord = None
            if constraints:
                target_chord = next((c for c in constraints if c.start <= cp < c.start + c.duration), None)

            dp_prev_reshaped = dp[t_step - 1]
            dp_new = np.full((12, 12, 12), NEG_INF)

            for r_prev in range(12):
                for r_curr in range(12):
                    interval = (r_curr - r_prev) % 12
                    
                    # Copy predecessor slice [k_prev, r_prevprev]
                    dp_slice = dp_prev_reshaped[r_prev].copy()
                    
                    # Apply path-dependent interval diversity penalty
                    if t_step >= 2:
                        r_prevprev_penalized = (r_prev - interval) % 12
                        dp_slice[:, r_prevprev_penalized] -= self.config.interval_diversity_penalty
                    
                    # Max over r_prevprev
                    best_r_prevprev = np.argmax(dp_slice, axis=1)
                    max_prevprev = dp_slice[np.arange(12), best_r_prevprev]
                    
                    # Base transition matrix lookup [k_prev, k_curr]
                    trans_base = LOG_PCHANGE[:, interval, :].copy()
                    np.fill_diagonal(trans_base, trans_base.diagonal() - self.config.anti_stagnation_penalty)
                    
                    # Combine path scores and transitions
                    scores = max_prevprev[:, None] + trans_base
                    
                    # Max over k_prev for each k_curr
                    best_k_prev = np.argmax(scores, axis=0)
                    best_scores = scores[best_k_prev, np.arange(12)]
                    
                    dp_new[r_curr, :, r_prev] = best_scores
                    
                    # Backtrack encoding: k_prev * 12 + r_prevprev
                    best_r_prevprev_for_best_k = best_r_prevprev[best_k_prev]
                    backtrack[t_step, r_curr, :, r_prev] = best_k_prev * 12 + best_r_prevprev_for_best_k

            # Add emissions and step biases
            for r_curr in range(12):
                for k_curr in range(12):
                    score_emit = emit[t_step, r_curr, k_curr]
                    
                    # Tension bias
                    t_bias = 0.0
                    if tension_curve:
                        if k_curr in UNSTABLE_INDICES:
                            t_bias = tau * self.config.tension_weight
                        elif k_curr in STABLE_INDICES:
                            t_bias = (1.0 - tau) * self.config.tension_weight
                            
                    # Key coupling bias
                    coupling_bias = 0.0
                    if key_path:
                        key_root, key_type = key_path[t_step]
                        coupling_bias = self.config.key_coupling_weight * (
                            KEY_OFFSET_LOG[key_type, (r_curr - key_root) % 12] 
                            + LOG_KEY_TYPE_PRIOR[key_type, k_curr]
                        )
                        
                    dp_new[r_curr, k_curr, :] += score_emit + t_bias + coupling_bias

            # Constraints filtering
            if target_chord:
                t_idx = _resolve_type_idx(target_chord.quality)
                for r in range(N_TONES):
                    for k in range(N_TYPES):
                        if r != target_chord.root or k != t_idx:
                            dp_new[r, k, :] = NEG_INF

            dp[t_step] = dp_new

        # Backtrack
        best_flat_idx = np.argmax(dp[T - 1])
        r_curr, k_curr, r_prev = np.unravel_index(best_flat_idx, (12, 12, 12))
        
        path = [(r_curr, k_curr)]
        
        for t_step in range(T - 1, 0, -1):
            back_val = backtrack[t_step, r_curr, k_curr, r_prev]
            k_prev = back_val // 12
            r_prevprev = back_val % 12
            
            r_curr, k_curr, r_prev = r_prev, k_prev, r_prevprev
            path.append((r_curr, k_curr))
            
        path.reverse()
        return path

    # ------------------------------------------------------------------
    # Layer 2: Key Viterbi
    # ------------------------------------------------------------------

    def _viterbi_keys(self, chords: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Find most likely key sequence given chord observations."""
        n_s = N_TONES * N_KEY_TYPES  # 24
        T = len(chords)

        STAY_LOG = math.log(0.98)
        SWITCH_LOG = math.log(0.02 / (n_s - 1))

        trans = np.full((n_s, n_s), SWITCH_LOG)
        np.fill_diagonal(trans, STAY_LOG)

        roots = np.array([c[0] for c in chords])
        ctypes = np.array([c[1] for c in chords])

        key_roots = np.arange(N_TONES)
        key_types = np.arange(N_KEY_TYPES)
        offsets = (roots[:, None] - key_roots[None, :]) % N_TONES  # [T, 12]

        emit_all = np.empty((T, n_s))
        for kt in range(N_KEY_TYPES):
            emit_all[:, kt::N_KEY_TYPES] = (
                KEY_OFFSET_LOG[kt][offsets]
                + LOG_KEY_TYPE_PRIOR[kt, ctypes[:, None]]
            )

        NEG_INF = -1e9
        backtrack = np.zeros((T, n_s), dtype=np.int32)

        dp = emit_all[0].copy()
        for t_step in range(1, T):
            scores = dp[:, None] + trans
            backtrack[t_step] = np.argmax(scores, axis=0)
            dp = emit_all[t_step] + np.max(scores, axis=0)

        best_last = int(np.argmax(dp))
        path = [best_last]
        for t_step in range(T - 1, 0, -1):
            path.append(int(backtrack[t_step, path[-1]]))
        path.reverse()

        return [(s // N_KEY_TYPES, s % N_KEY_TYPES) for s in path]

    # ------------------------------------------------------------------
    # Emission helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _log_emit_chord(weighted_pcs: list[WeightedNote], root: int, type_idx: int) -> float:
        """log P(weighted_pitch_classes | chord root, type) with normalization."""
        if not weighted_pcs:
            return -1.0

        log_p = 0.0
        total_weight = 0.0

        for wn in weighted_pcs:
            off = (wn.pitch_class - root) % N_TONES
            weight = wn.weight
            log_p += weight * LOG_PNOTE[off, type_idx]
            total_weight += weight

        # Normalization to keep likelihoods comparable across different densities
        return log_p / (total_weight + 1e-6)

    @staticmethod
    def _log_emit_key(chord: tuple[int, int], key_root: int, key_type: int) -> float:
        """log P(chord | key) using key offset distribution + type prior."""
        cr, ct = chord
        off = (cr - key_root) % N_TONES
        log_off = KEY_OFFSET_LOG[key_type, off]
        log_type = LOG_KEY_TYPE_PRIOR[key_type, ct]
        return log_off + log_type

    # ------------------------------------------------------------------
    # Observation extraction
    # ------------------------------------------------------------------

    def _get_change_points(self, duration: float) -> list[float]:
        if self.bar_grid:
            mode_map = {"bars": "bars", "half": "strong_beats", "beats": "beats"}
            return self.bar_grid.change_points(duration, mode=mode_map.get(self.chord_change, "bars"))

        # Fallback if no bar_grid
        step = 4.0 if self.chord_change == "bars" else 2.0
        pts = []
        t = 0.0
        while t < duration - 0.01:
            pts.append(round(t, 6))
            t += step
        return pts

    @staticmethod
    def _snap_constraints(constraints: list[ChordLabel], change_points: list[float]) -> list[ChordLabel]:
        """Snap constraint start/duration to the nearest change points."""
        if not change_points:
            return constraints
        snapped = []
        for c in constraints:
            # Find nearest change point to constraint start
            best_cp = min(change_points, key=lambda cp: abs(cp - c.start))
            # Find the change point that covers the constraint end
            c_end = c.start + c.duration
            # Pick the first cp >= c_end, or last cp + step
            end_cp = None
            for i, cp in enumerate(change_points):
                if cp >= c_end - 0.01:
                    end_cp = cp
                    break
            if end_cp is None:
                end_cp = c_end
            new_dur = max(end_cp - best_cp, change_points[1] - change_points[0] if len(change_points) > 1 else 4.0)
            snapped.append(ChordLabel(
                root=c.root, quality=c.quality, extensions=c.extensions,
                bass=c.bass, inversion=c.inversion,
                start=round(best_cp, 6), duration=round(new_dur, 6),
            ))
        return snapped

    def _extract_observations(self, melody: list[NoteInfo], change_points: list[float]) -> list[list[WeightedNote]]:
        observations = []
        bpb = self.bar_grid.beats_per_bar if self.bar_grid else 4.0

        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")

            # Use dict to consolidate same pitch classes in this window
            pc_weights: dict[int, float] = {}

            for n in melody:
                n_end = n.start + n.duration
                # Find overlap between note [n.start, n_end] and window [cp, next_cp]
                overlap_start = max(cp, n.start)
                overlap_end = min(next_cp, n_end)

                if overlap_end > overlap_start:
                    active_dur = overlap_end - overlap_start
                    pc = n.pitch % 12

                    # 1. Duration Weighting (sqrt to avoid domination)
                    duration_weight = math.sqrt(active_dur)

                    # 2. Metric Weighting
                    # Calculate position within bar
                    pos_in_bar = self.bar_grid.beat_in_bar(n.start) if self.bar_grid else (n.start % 4.0)

                    metric_weight = 1.0
                    if abs(pos_in_bar) < 0.01: # Beat 1
                        metric_weight = 1.5
                    elif abs(pos_in_bar - (bpb / 2.0)) < 0.01: # Beat 3 (in 4/4)
                        metric_weight = 1.2
                    elif abs(pos_in_bar % 1.0) > 0.01: # Syncopated / Off-beat
                        metric_weight = 0.8

                    weight = duration_weight * metric_weight
                    pc_weights[pc] = pc_weights.get(pc, 0.0) + weight

            obs_list = [WeightedNote(pc, w) for pc, w in pc_weights.items()]
            observations.append(obs_list)

        return observations
