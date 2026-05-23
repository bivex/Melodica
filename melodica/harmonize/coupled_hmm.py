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
# Data Matrices (Simplified from paper visualizations)
# ---------------------------------------------------------------------------

# Chord Types: 0=Major, 1=Minor, 2=Dissonant (Diminished/Dominant7)
CHORD_TYPES = 3

# µ_t: Probability of note offset n-r given chord type t
# Values are rough estimates derived from the Bach Chorale study.
CHORD_NOTE_EMISSIONS = [
    # Type 0 (Major): {0: Root, 4: Maj3, 7: P5}
    {0: 0.35, 4: 0.25, 7: 0.25, 2: 0.03, 5: 0.03, 9: 0.03, 11: 0.03, 1: 1e-6, 3: 1e-6, 6: 1e-6, 8: 1e-6, 10: 1e-6},
    # Type 1 (Minor): {0: Root, 3: Min3, 7: P5}
    {0: 0.35, 3: 0.25, 7: 0.25, 2: 0.03, 5: 0.03, 8: 0.03, 10: 0.03, 1: 1e-6, 4: 1e-6, 6: 1e-6, 9: 1e-6, 11: 1e-6},
    # Type 2 (Dissonant): {0: Anchor, 3, 6, 8...}
    {0: 0.25, 3: 0.20, 6: 0.20, 8: 0.15, 10: 0.10, 1: 0.02, 4: 0.02, 7: 0.02, 2: 0.02, 5: 0.02, 9: 1e-6, 11: 1e-6}
]

# α: Chord transitions f(r2-r1, t1, t2)
# Interval 7 (+7 or -5) and 5 (+5 or -7) are favored (Circle of Fifths).
CHORD_TRANSITIONS = {} # (t1, t2) -> {interval: prob}

def _init_chord_transitions():
    for t1 in range(3):
        for t2 in range(3):
            # Default uniform + small noise
            d = {i: 0.05 for i in range(12)}
            # Strong V-I (7 -> 0)
            if t1 == 0 and t2 == 0: # Maj -> Maj (V -> I)
                d[5] = 0.30 # Up a 4th
                d[7] = 0.15 # Down a 4th / Up a 5th
                d[0] = 0.10 # Repeat
            elif t1 == 1 and t2 == 0: # Min -> Maj (ii -> V, vi -> V)
                d[5] = 0.25
                d[10] = 0.20
            # Normalize
            s = sum(d.values())
            CHORD_TRANSITIONS[(t1, t2)] = {k: v/s for k, v in d.items()}

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
