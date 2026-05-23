# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
coupled_hmm.py — Advanced Hierarchical HMM Harmonizer.
Based on research by Dmitri Tymoczko and Mark Newman (2024).

Implements:
1. Interval-based (modulo 12) transition probabilities.
2. Probabilistic chord note emissions (µ_t).
3. Hierarchical key-tracking layer.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.theory import CHORD_TEMPLATES

# ---------------------------------------------------------------------------
# Data Matrices (Trained on 371 Bach Chorales via Metal GPU)
# ---------------------------------------------------------------------------

# µ_t: Probability of note offset n-r given chord type t
# Columns: 0=Major, 1=Minor, 2=Dissonant (Diminished/Dominant7)
# Data source: pnote_metal.txt
CHORD_NOTE_EMISSIONS = [
    # Type 0 (Major)
    {0: 0.998, 4: 0.880, 7: 0.957, 2: 0.077, 5: 0.061, 9: 0.095, 11: 0.063, 1: 0.001, 3: 0.001, 6: 0.005, 8: 0.011, 10: 0.001},
    # Type 1 (Minor)
    {0: 0.970, 3: 0.946, 7: 0.962, 2: 0.102, 5: 0.049, 8: 0.004, 10: 0.087, 1: 0.004, 4: 0.001, 6: 0.001, 9: 0.105, 11: 0.009},
    # Type 2 (Dissonant)
    {0: 0.846, 3: 0.898, 6: 0.987, 8: 0.657, 10: 0.030, 1: 0.110, 4: 0.010, 7: 0.001, 2: 0.001, 5: 0.018, 9: 0.066, 11: 0.001}
]

# α: Chord transitions f(r2-r1, t1, t2)
# Data source: pchange_metal.npy (Simplified into high-impact transitions)
CHORD_TRANSITIONS = {}

def _init_chord_transitions():
    # Load raw data from training result (approximated here for code readability)
    # Format: (type_from, type_to) -> {interval: prob}
    # Values extracted from the 3x12x3 matrix
    
    # 0 -> 0 (Major to Major)
    CHORD_TRANSITIONS[(0, 0)] = {
        0: 0.187, 5: 0.165, 7: 0.129, 2: 0.067, 11: 0.007, 10: 0.010, 9: 0.009
    }
    # 0 -> 1 (Major to Minor)
    CHORD_TRANSITIONS[(0, 1)] = {
        5: 0.052, 2: 0.032, 9: 0.032, 0: 0.006, 4: 0.008, 7: 0.011
    }
    # 1 -> 0 (Minor to Major)
    CHORD_TRANSITIONS[(1, 0)] = {
        2: 0.127, 5: 0.089, 7: 0.133, 10: 0.092, 3: 0.044, 8: 0.037
    }
    # 1 -> 1 (Minor to Minor)
    CHORD_TRANSITIONS[(1, 1)] = {
        0: 0.165, 5: 0.050, 7: 0.046, 10: 0.011, 2: 0.009
    }
    # Dissonant transitions (Simplified)
    CHORD_TRANSITIONS[(2, 0)] = { 1: 0.592, 5: 0.018, 8: 0.028, 10: 0.017 } # Resolve to Major
    CHORD_TRANSITIONS[(2, 1)] = { 1: 0.165, 3: 0.018, 10: 0.035 } # Resolve to Minor
    CHORD_TRANSITIONS[(0, 2)] = { 4: 0.168, 6: 0.054, 11: 0.027, 1: 0.003 }
    CHORD_TRANSITIONS[(1, 2)] = { 9: 0.066, 6: 0.025, 11: 0.026, 2: 0.016 }
    CHORD_TRANSITIONS[(2, 2)] = { 0: 0.049, 2: 0.015, 5: 0.006 }

    # Fill missing with epsilon
    for t1 in range(3):
        for t2 in range(3):
            if (t1, t2) not in CHORD_TRANSITIONS:
                CHORD_TRANSITIONS[(t1, t2)] = {i: 1e-4 for i in range(12)}
            else:
                for i in range(12):
                    if i not in CHORD_TRANSITIONS[(t1, t2)]:
                        CHORD_TRANSITIONS[(t1, t2)][i] = 1e-4
            # Normalize
            s = sum(CHORD_TRANSITIONS[(t1, t2)].values())
            for i in range(12):
                CHORD_TRANSITIONS[(t1, t2)][i] /= s

_init_chord_transitions()

# Key Types: 0=Major, 1=Minor
KEY_TYPES = 2

# ν: Chord emissions given key ν_kc = P(c | k)
# Depends on key type u and offset r-s.
KEY_CHORD_EMISSIONS = [
    # Key Type 0 (Major): {0:I, 2:ii, 4:iii, 5:IV, 7:V, 9:vi, 11:vii}
    {0: 0.30, 7: 0.20, 5: 0.15, 2: 0.10, 9: 0.10, 4: 0.05, 11: 0.05},
    # Key Type 1 (Minor): {0:i, 2:ii°, 3:III, 5:iv, 7:v/V, 8:VI, 10:VII}
    {0: 0.30, 7: 0.20, 5: 0.15, 8: 0.10, 3: 0.10, 2: 0.05, 10: 0.05}
]

# ---------------------------------------------------------------------------
# Coupled HMM Harmonizer
# ---------------------------------------------------------------------------

@dataclass
class CoupledHMMHarmonizer:
    """
    Implements a hierarchical HMM for music harmonization and analysis.
    """
    beam_width: int = 12
    chord_change: str = "bars"
    
    # State Mapping
    # Chord States: 12 roots * 3 types = 36 states
    # Key States: 12 roots * 2 types = 24 states

    def harmonize(
        self,
        melody: list[NoteInfo],
        initial_scale: Scale,
        duration_beats: float
    ) -> list[ChordLabel]:
        if not melody: return []

        # 1. Prepare Observations
        change_points = self._get_change_points(duration_beats)
        observations = self._extract_observations(melody, change_points)
        T = len(observations)
        
        # 2. Layer 1: Notes to Chords (36 states)
        # We find the sequence of chords that best explains the notes.
        chord_path = self._viterbi_chords(observations, initial_scale)
        
        # 3. Layer 2: Chords to Keys (24 states)
        # We find the sequence of keys that best explains the chords.
        # This allows us to detect modulations.
        key_path = self._viterbi_keys(chord_path)
        
        # 4. Build Result
        result = []
        for i, c_state in enumerate(chord_path):
            root, t_idx = c_state
            # Map back to Quality
            quality = Quality.MAJOR if t_idx == 0 else (Quality.MINOR if t_idx == 1 else Quality.DIMINISHED)
            
            start = change_points[i]
            dur = (change_points[i+1]-start) if i+1 < len(change_points) else duration_beats-start
            
            # Detect Roman numeral relative to current key
            key_root, key_t = key_path[i]
            off = (root - key_root) % 12
            # (In a full implementation, we'd map (off, t_idx) to a degree 1-7)
            
            result.append(ChordLabel(
                root=root, quality=quality, 
                start=round(start, 6), duration=round(dur, 6)
            ))
            
        return result

    def _viterbi_chords(self, obs: list[list[int]], scale: Scale) -> list[tuple[int, int]]:
        """Find most likely sequence of (root, type) states."""
        states = []
        for r in range(12):
            for t in range(3):
                states.append((r, t))
        
        n_s = len(states)
        T = len(obs)
        
        dp = [[-1000.0] * n_s for _ in range(T)]
        backtrack = [[0] * n_s for _ in range(T)]
        
        # Init
        for s_idx, (r, t) in enumerate(states):
            emit = self._log_emit_chord(obs[0], r, t)
            # Bias toward tonic major/minor at start
            start_bias = 0.0
            if r == scale.root:
                start_bias = 2.0
            dp[0][s_idx] = emit + start_bias

        # Transitions
        for t_step in range(1, T):
            for s_idx, (r, t) in enumerate(states):
                emit = self._log_emit_chord(obs[t_step], r, t)
                
                best_prev_score = -1000.0
                best_prev_idx = 0
                
                for p_idx, (pr, pt) in enumerate(states):
                    interval = (r - pr) % 12
                    trans_prob = CHORD_TRANSITIONS[(pt, t)].get(interval, 0.001)
                    score = dp[t_step-1][p_idx] + math.log(trans_prob)
                    
                    if score > best_prev_score:
                        best_prev_score = score
                        best_prev_idx = p_idx
                        
                dp[t_step][s_idx] = emit + best_prev_score
                backtrack[t_step][s_idx] = best_prev_idx

        # Backtrack
        best_last = max(range(n_s), key=lambda i: dp[T-1][i])
        path_indices = [best_last]
        for t_step in range(T-1, 0, -1):
            path_indices.append(backtrack[t_step][path_indices[-1]])
        path_indices.reverse()
        
        return [states[i] for i in path_indices]

    def _viterbi_keys(self, chords: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Find most likely sequence of (root, type) keys given chord sequence."""
        states = []
        for r in range(12):
            for t in range(2): # Major/Minor keys
                states.append((r, t))
        
        n_s = len(states)
        T = len(chords)
        
        dp = [[-1000.0] * n_s for _ in range(T)]
        backtrack = [[0] * n_s for _ in range(T)]
        
        # Transition between keys is very slow (high probability of staying in same key)
        STAY_KEY_PROB = 0.98
        SWITCH_KEY_PROB = (1.0 - STAY_KEY_PROB) / (n_s - 1)

        # Init
        for s_idx, (kr, kt) in enumerate(states):
            dp[0][s_idx] = self._log_emit_key(chords[0], kr, kt)

        # Transitions
        for t_step in range(1, T):
            for s_idx, (kr, kt) in enumerate(states):
                emit = self._log_emit_key(chords[t_step], kr, kt)
                
                best_prev_score = -1000.0
                best_prev_idx = 0
                
                for p_idx, (pkr, pkt) in enumerate(states):
                    trans_prob = STAY_KEY_PROB if p_idx == s_idx else SWITCH_KEY_PROB
                    score = dp[t_step-1][p_idx] + math.log(trans_prob)
                    if score > best_prev_score:
                        best_prev_score = score
                        best_prev_idx = p_idx
                
                dp[t_step][s_idx] = emit + best_prev_score
                backtrack[t_step][s_idx] = best_prev_idx

        # Backtrack
        best_last = max(range(n_s), key=lambda i: dp[T-1][i])
        path_indices = [best_last]
        for t_step in range(T-1, 0, -1):
            path_indices.append(backtrack[t_step][path_indices[-1]])
        path_indices.reverse()
        
        return [states[i] for i in path_indices]

    def _log_emit_chord(self, pcs: list[int], root: int, type_idx: int) -> float:
        """Probability of seeing these pitch classes given chord (r, t)."""
        if not pcs: return -1.0
        log_p = 0.0
        dist = CHORD_NOTE_EMISSIONS[type_idx]
        for pc in pcs:
            off = (pc - root) % 12
            prob = dist.get(off, 0.001)
            log_p += math.log(prob)
        return log_p

    def _log_emit_key(self, chord: tuple[int, int], key_root: int, key_type: int) -> float:
        """Probability of seeing chord c given key k."""
        cr, ct = chord
        off = (cr - key_root) % 12
        # Use simple map: in key, certain chords are common
        dist = KEY_CHORD_EMISSIONS[key_type]
        prob = dist.get(off, 0.01)
        # Type check: minor chords more common in minor keys, etc.
        if ct != key_type: prob *= 0.5
        return math.log(prob)

    def _get_change_points(self, duration: float) -> list[float]:
        points = []
        step = 4.0 if self.chord_change == "bars" else 2.0
        t = 0.0
        while t < duration:
            points.append(t)
            t += step
        return points

    def _extract_observations(self, melody: list[NoteInfo], change_points: list[float]) -> list[list[int]]:
        observations = []
        sorted_m = sorted(melody, key=lambda n: n.start)
        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")
            pcs = [n.pitch % 12 for n in sorted_m if cp <= n.start < next_cp]
            observations.append(pcs if pcs else [0])
        return observations
