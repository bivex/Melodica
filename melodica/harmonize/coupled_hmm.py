# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
coupled_hmm.py — Hierarchical HMM Harmonizer (6 chord types).
Based on research by Dmitri Tymoczko and Mark Newman (2024).

Layer 1: Notes -> Chords via Viterbi over 72 states (12 roots x 6 types).
Layer 2: Chords -> Keys via Viterbi over 24 states (12 roots x 2 key types).

Weights loaded from melodica/harmonize/weights/ (trained by train_full_modes.py).
"""

from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass
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
LOG_PNOTE = np.log(np.clip(PNOTE, _EPS, 1.0))       # [12, 6]
LOG_PCHANGE = np.log(np.clip(PCHANGE, _EPS, 1.0))    # [6, 12, 6]

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
# Coupled HMM Harmonizer
# ---------------------------------------------------------------------------

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

        # 2. Layer 1: Notes -> Chords (108 states)
        chord_path = self._viterbi_chords(observations, initial_scale, change_points, constraints, tension_curve)

        # 3. Layer 2: Chords -> Keys (24 states)
        key_path = self._viterbi_keys(chord_path)

        # 4. Build result
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
        tension_curve: Any | None = None
    ) -> list[tuple[int, int]]:
        """Find most likely chord sequence with optional hard constraints and tension bias."""
        n_s = N_TONES * N_TYPES  # 108
        T = len(obs)
        NEG_INF = -1e12 # Very large negative number

        # Pre-compute emissions
        emit = np.full((T, N_TONES, N_TYPES), -20.0)
        for t_step in range(T):
            for r in range(N_TONES):
                for k in range(N_TYPES):
                    emit[t_step, r, k] = self._log_emit_chord(obs[t_step], r, k)

        # Map Quality to index for constraints
        quality_to_idx = {q: i for i, q in enumerate(TYPE_TO_QUALITY)}

        dp = np.full((T, n_s), NEG_INF)
        backtrack = np.zeros((T, n_s), dtype=np.int32)

        # Tension indices (for bias)
        # 0: Maj, 1: Min, 2: Dim, 3: Aug, 8: Dom7, 11: Add9
        STABLE_INDICES = {0, 1, 11}
        UNSTABLE_INDICES = {2, 3, 8}

        # Init step
        for r in range(N_TONES):
            for k in range(N_TYPES):
                s_idx = r * N_TYPES + k
                score = emit[0, r, k]
                
                # Apply tonic bias
                if r == scale.root:
                    score += 2.0
                
                # Apply tension bias at T=0
                if tension_curve:
                    tau = tension_curve.tension_at(change_points[0])
                    if k in UNSTABLE_INDICES: score += tau * 4.0
                    if k in STABLE_INDICES: score += (1.0 - tau) * 4.0
                
                # Check for constraint at start (T=0)
                if constraints:
                    cp = change_points[0]
                    target = next((c for c in constraints if c.start <= cp < c.start + c.duration), None)
                    if target:
                        t_idx = quality_to_idx.get(target.quality)
                        if r != target.root or k != t_idx:
                            score = NEG_INF # Kill all other paths
                
                dp[0, s_idx] = score

        # Forward pass
        for t_step in range(1, T):
            cur_emit = emit[t_step]
            prev_dp = dp[t_step - 1]
            cp = change_points[t_step]
            
            # Tension level at this point
            tau = tension_curve.tension_at(cp) if tension_curve else 0.5

            # Find if there is a constraint for this time step
            target_chord = None
            if constraints:
                target_chord = next((c for c in constraints if c.start <= cp < c.start + c.duration), None)

            for r_next in range(N_TONES):
                for k_next in range(N_TYPES):
                    s_next = r_next * N_TYPES + k_next
                    
                    # If this state doesn't match the constraint, skip it
                    if target_chord:
                        t_idx = quality_to_idx.get(target_chord.quality)
                        if r_next != target_chord.root or k_next != t_idx:
                            dp[t_step, s_next] = NEG_INF
                            continue

                    best_score = NEG_INF
                    best_prev = 0
                    e = cur_emit[r_next, k_next]
                    
                    # Tension bias for entering this chord type
                    t_bias = 0.0
                    if k_next in UNSTABLE_INDICES: t_bias = tau * 4.0
                    if k_next in STABLE_INDICES: t_bias = (1.0 - tau) * 4.0
                    
                    for r_prev in range(N_TONES):
                        interval = (r_next - r_prev) % N_TONES
                        for k_prev in range(N_TYPES):
                            s_prev = r_prev * N_TYPES + k_prev
                            
                            # Optimization: skip calculation if previous path is already dead
                            if prev_dp[s_prev] <= NEG_INF / 2:
                                continue
                                
                            score = prev_dp[s_prev] + LOG_PCHANGE[k_prev, interval, k_next]
                            if score > best_score:
                                best_score = score
                                best_prev = s_prev
                                
                    dp[t_step, s_next] = e + t_bias + best_score
                    backtrack[t_step, s_next] = best_prev

        # Backtrack
        best_last = int(np.argmax(dp[T - 1]))
        path = [best_last]
        for t_step in range(T - 1, 0, -1):
            path.append(int(backtrack[t_step, path[-1]]))
        path.reverse()

        return [(s // N_TYPES, s % N_TYPES) for s in path]

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
