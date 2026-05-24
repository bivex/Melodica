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

from melodica.types import BarGrid, ChordLabel, Quality, Scale, NoteInfo

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

N_TONES = 12
N_TYPES = 6  # Major, Minor, Dim, Aug, sus2, sus4
N_KEY_TYPES = 2  # Major key, Minor key

# Mapping from training type index to Quality enum
TYPE_TO_QUALITY = [
    Quality.MAJOR,       # 0
    Quality.MINOR,       # 1
    Quality.DIMINISHED,  # 2
    Quality.AUGMENTED,   # 3
    Quality.SUS2,        # 4
    Quality.SUS4,        # 5
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
# Key-Chord Emissions (hand-coded functional harmony priors)
# ---------------------------------------------------------------------------

# ν: P(chord_type | key_type) — how likely each chord type is in each key
# Expanded to 6 types, weighted by functional harmony knowledge
KEY_TYPE_PRIOR = np.array([
    # Major key: I, ii, iii, IV, V, vi, vii° + extensions
    # Maj  Min  Dim  Aug  sus2 sus4
    [0.35, 0.20, 0.05, 0.02, 0.08, 0.10],  # diatonic offsets
    # Minor key: i, ii°, III, iv, V/v, VI, VII
    [0.20, 0.35, 0.08, 0.02, 0.05, 0.08],
])

# Key-chord offset distributions: P(root_offset | key_type)
# These encode which scale degrees are most likely
KEY_OFFSET_LOG = np.full((N_KEY_TYPES, N_TONES), math.log(0.01))
# Major key scale degrees: I(0), ii(2), iii(4), IV(5), V(7), vi(9), vii°(11)
KEY_OFFSET_LOG[0, [0, 2, 4, 5, 7, 9, 11]] = [math.log(0.30), math.log(0.12),
    math.log(0.06), math.log(0.15), math.log(0.20), math.log(0.10), math.log(0.04)]
# Minor key: i(0), ii°(2), III(3), iv(5), V(7), VI(8), VII(10)
KEY_OFFSET_LOG[1, [0, 2, 3, 5, 7, 8, 10]] = [math.log(0.30), math.log(0.05),
    math.log(0.10), math.log(0.15), math.log(0.20), math.log(0.10), math.log(0.05)]


# ---------------------------------------------------------------------------
# Coupled HMM Harmonizer
# ---------------------------------------------------------------------------

@dataclass
class CoupledHMMHarmonizer:
    beam_width: int = 12
    chord_change: str = "bars"
    bar_grid: BarGrid | None = None

    def harmonize(
        self,
        melody: list[NoteInfo],
        initial_scale: Scale,
        duration_beats: float
    ) -> list[ChordLabel]:
        if not melody:
            return []

        # 1. Prepare observations
        change_points = self._get_change_points(duration_beats)
        observations = self._extract_observations(melody, change_points)
        T = len(observations)

        # 2. Layer 1: Notes -> Chords (72 states = 12 roots x 6 types)
        chord_path = self._viterbi_chords(observations, initial_scale)

        # 3. Layer 2: Chords -> Keys (24 states = 12 roots x 2 key types)
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

    # ------------------------------------------------------------------
    # Layer 1: Chord Viterbi
    # ------------------------------------------------------------------

    def _viterbi_chords(self, obs: list[list[int]], scale: Scale) -> list[tuple[int, int]]:
        """Find most likely chord sequence via Viterbi over 72 states."""
        n_s = N_TONES * N_TYPES  # 72
        T = len(obs)

        # Pre-compute emissions: emit[t_step, r, k] = log P(obs[t_step] | chord r,k)
        emit = np.full((T, N_TONES, N_TYPES), -20.0)
        for t_step in range(T):
            for r in range(N_TONES):
                for k in range(N_TYPES):
                    emit[t_step, r, k] = self._log_emit_chord(obs[t_step], r, k)

        # Flatten to [n_s] for DP
        NEG_INF = -1e9
        dp = np.full((T, n_s), NEG_INF)
        backtrack = np.zeros((T, n_s), dtype=np.int32)

        # Init step
        for r in range(N_TONES):
            for k in range(N_TYPES):
                s_idx = r * N_TYPES + k
                score = emit[0, r, k]
                if r == scale.root:
                    score += 2.0  # tonic bias
                dp[0, s_idx] = score

        # Pre-compute transition log-probs: trans[k_prev, interval, k_next]
        # LOG_PCHANGE is [6, 12, 6]

        # Forward pass
        for t_step in range(1, T):
            cur_emit = emit[t_step]  # [12, 6]
            prev_dp = dp[t_step - 1]  # [72]

            # Vectorized: for each (r_next, k_next), find best (r_prev, k_prev)
            # score = emit[r_next, k_next] + max over (r_prev, k_prev) of
            #         dp[r_prev, k_prev] + log_pchange[k_prev, interval, k_next]
            # where interval = (r_next - r_prev) % 12

            for r_next in range(N_TONES):
                for k_next in range(N_TYPES):
                    best_score = NEG_INF
                    best_prev = 0

                    e = cur_emit[r_next, k_next]

                    for r_prev in range(N_TONES):
                        interval = (r_next - r_prev) % N_TONES
                        for k_prev in range(N_TYPES):
                            s_prev = r_prev * N_TYPES + k_prev
                            score = prev_dp[s_prev] + LOG_PCHANGE[k_prev, interval, k_next]
                            if score > best_score:
                                best_score = score
                                best_prev = s_prev

                    s_next = r_next * N_TYPES + k_next
                    dp[t_step, s_next] = e + best_score
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

        NEG_INF = -1e9
        dp = np.full((T, n_s), NEG_INF)
        backtrack = np.zeros((T, n_s), dtype=np.int32)

        # Init
        for kr in range(N_TONES):
            for kt in range(N_KEY_TYPES):
                dp[0, kr * N_KEY_TYPES + kt] = self._log_emit_key(chords[0], kr, kt)

        for t_step in range(1, T):
            for s_idx in range(n_s):
                kr = s_idx // N_KEY_TYPES
                kt = s_idx % N_KEY_TYPES
                emit_score = self._log_emit_key(chords[t_step], kr, kt)

                best_score = NEG_INF
                best_prev = 0
                for p_idx in range(n_s):
                    trans = STAY_LOG if p_idx == s_idx else SWITCH_LOG
                    score = dp[t_step - 1, p_idx] + trans
                    if score > best_score:
                        best_score = score
                        best_prev = p_idx

                dp[t_step, s_idx] = emit_score + best_score
                backtrack[t_step, s_idx] = best_prev

        best_last = int(np.argmax(dp[T - 1]))
        path = [best_last]
        for t_step in range(T - 1, 0, -1):
            path.append(int(backtrack[t_step, path[-1]]))
        path.reverse()

        return [(s // N_KEY_TYPES, s % N_KEY_TYPES) for s in path]

    # ------------------------------------------------------------------
    # Emission helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _log_emit_chord(pcs: list[int], root: int, type_idx: int) -> float:
        """log P(pitch_classes | chord root, type) using trained pnote."""
        if not pcs:
            return -1.0
        log_p = 0.0
        for pc in pcs:
            off = (pc - root) % N_TONES
            log_p += LOG_PNOTE[off, type_idx]
        return log_p

    @staticmethod
    def _log_emit_key(chord: tuple[int, int], key_root: int, key_type: int) -> float:
        """log P(chord | key) using key offset distribution + type prior."""
        cr, ct = chord
        off = (cr - key_root) % N_TONES
        log_off = KEY_OFFSET_LOG[key_type, off]
        log_type = math.log(KEY_TYPE_PRIOR[key_type, ct] + _EPS)
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

    def _extract_observations(self, melody: list[NoteInfo], change_points: list[float]) -> list[list[int]]:
        observations = []
        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")

            # Find notes that are ACTIVE during [cp, next_cp)
            active_pcs = []
            for n in melody:
                n_end = n.start + n.duration
                if n.start < next_cp and n_end > cp:
                    active_pcs.append(n.pitch % 12)

            observations.append(list(set(active_pcs)))
        return observations
