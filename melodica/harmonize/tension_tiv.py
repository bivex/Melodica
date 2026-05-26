# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tension_tiv.py — Tonal Interval Vector tension metric.

Implements TIV-based tonal tension from:
  Ebrahimzadeh et al., "Explicit Tonal Tension Conditioning via Dual-Level
  Beam Search for Symbolic Music Generation" (2025).

Three components:
  1. Tonal distance  — chord-to-prev (Euclidean), chord-to-key (angle),
                        chord-to-function (angle)
  2. Tonal dissonance — 1 - ||TIV|| / ||TIV_max||
  3. Voice leading   — melodic stability between consecutive chords

All computed in the 6D Tonal Interval Space (TIS) via DFT of chroma vectors.
"""

from __future__ import annotations

import math
import numpy as np
from typing import Sequence


# ---------------------------------------------------------------------------
# DFT basis for chroma → TIV projection
# ---------------------------------------------------------------------------

# The 6 DFT coefficients (indices 1-6) applied to a 12-dim chroma vector.
# Each row is a complex exponential basis vector.
_DFT_BASIS = np.array([
    [np.exp(2j * math.pi * k * n / 12) for n in range(12)]
    for k in range(1, 7)
])  # shape [6, 12]

# Normalization weights per coefficient (from Bernardes et al. 2016)
_TIV_WEIGHTS = np.array([1.0, 0.5, 0.35, 0.25, 0.20, 0.15])


def chroma_to_tiv(chroma: np.ndarray) -> np.ndarray:
    """Project a 12-dim chroma vector into 6D Tonal Interval Space.

    Args:
        chroma: shape [12], non-negative values (pitch-class activations).
    Returns:
        Complex-valued TIV, shape [6].
    """
    chroma = np.asarray(chroma, dtype=np.float64)
    raw = _DFT_BASIS @ chroma  # [6]
    return raw * _TIV_WEIGHTS


def _tiv_euclidean(tiv1: np.ndarray, tiv2: np.ndarray) -> float:
    """Euclidean distance between two TIVs (same-level comparison)."""
    diff = tiv1 - tiv2
    return float(np.sqrt(np.sum(diff * np.conj(diff)).real))


def _tiv_angle(tiv1: np.ndarray, tiv2: np.ndarray) -> float:
    """Angular distance between two TIVs (cross-level comparison)."""
    dot = np.sum(tiv1 * np.conj(tiv2)).real
    n1 = np.sqrt(np.sum(tiv1 * np.conj(tiv1)).real)
    n2 = np.sqrt(np.sum(tiv2 * np.conj(tiv2)).real)
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    cos_val = np.clip(dot / (n1 * n2), -1.0, 1.0)
    return float(np.arccos(cos_val))


# ---------------------------------------------------------------------------
# Chroma construction helpers
# ---------------------------------------------------------------------------

# Interval patterns for quality → pitch classes relative to root
_QUALITY_INTERVALS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "dominant7": [0, 4, 7, 10],
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "major9": [0, 4, 7, 11, 14],
    "minor9": [0, 3, 7, 10, 14],
    "add9": [0, 4, 7, 14],
    "half_dim7": [0, 3, 6, 10],
}


def chord_chroma(root_pc: int, quality: str) -> np.ndarray:
    """Build a 12-dim chroma vector for a chord."""
    intervals = _QUALITY_INTERVALS.get(quality, [0, 4, 7])
    chroma = np.zeros(12)
    for iv in intervals:
        chroma[(root_pc + iv) % 12] = 1.0
    return chroma


def key_chroma(root_pc: int, major: bool = True) -> np.ndarray:
    """Build a chroma vector for a key (major or minor scale)."""
    if major:
        intervals = [0, 2, 4, 5, 7, 9, 11]
    else:
        intervals = [0, 2, 3, 5, 7, 8, 10]
    chroma = np.zeros(12)
    for iv in intervals:
        chroma[(root_pc + iv) % 12] = 1.0
    return chroma


# ---------------------------------------------------------------------------
# Tonal tension computation
# ---------------------------------------------------------------------------

# Tonic/subdominant/dominant degree offsets (0-indexed) for key-relative
_FUNCTION_ROOTS_MAJOR = {0: 0, 3: 5, 4: 7}   # T=I, S=IV, D=V
_FUNCTION_ROOTS_MINOR = {0: 0, 3: 5, 4: 7}   # i, iv, V

# Empirical weights from Navarro et al. (2020)
_DISSONANCE_WEIGHT = 3.0
_VOICE_LEADING_WEIGHT = 1.5


def compute_tension(
    chord_pcs: Sequence[int],
    prev_chord_pcs: Sequence[int] | None = None,
    key_root: int = 0,
    key_major: bool = True,
    function_degree: int | None = None,
    max_tiv_norm: float = 5.0,
) -> dict[str, float]:
    """Compute tonal tension for a single chord in context.

    Args:
        chord_pcs: Pitch classes in the current chord.
        prev_chord_pcs: Pitch classes in the previous chord (for voice leading).
        key_root: Root PC of the key (0 = C).
        key_major: True for major key, False for minor.
        function_degree: Current chord's scale degree (0-indexed) for
                         chord-to-function distance. None to skip.
        max_tiv_norm: Normalization constant for dissonance.

    Returns:
        Dict with 'tonal_distance', 'dissonance', 'voice_leading', 'total'.
    """
    # Build chromas
    cur_chroma = np.zeros(12)
    for pc in chord_pcs:
        cur_chroma[pc % 12] = 1.0

    cur_tiv = chroma_to_tiv(cur_chroma)

    # --- Tonal distance ---
    tonal_dist = 0.0

    # (a) Chord-to-prev-chord (Euclidean)
    if prev_chord_pcs is not None:
        prev_chroma = np.zeros(12)
        for pc in prev_chord_pcs:
            prev_chroma[pc % 12] = 1.0
        prev_tiv = chroma_to_tiv(prev_chroma)
        tonal_dist += _tiv_euclidean(cur_tiv, prev_tiv)

    # (b) Chord-to-key (angle)
    key_c = key_chroma(key_root, key_major)
    key_tiv = chroma_to_tiv(key_c)
    tonal_dist += _tiv_angle(cur_tiv, key_tiv)

    # (c) Chord-to-function (angle)
    if function_degree is not None:
        roots = _FUNCTION_ROOTS_MAJOR if key_major else _FUNCTION_ROOTS_MINOR
        fn_root = roots.get(function_degree)
        if fn_root is not None:
            fn_chroma = np.zeros(12)
            fn_chroma[(key_root + fn_root) % 12] = 1.0
            fn_tiv = chroma_to_tiv(fn_chroma)
            tonal_dist += _tiv_angle(cur_tiv, fn_tiv)

    # --- Tonal dissonance ---
    tiv_norm = np.sqrt(np.sum(cur_tiv * np.conj(cur_tiv)).real)
    dissonance = max(0.0, 1.0 - tiv_norm / max_tiv_norm)

    # --- Voice leading ---
    vl = 0.0
    if prev_chord_pcs is not None:
        prev_sorted = sorted(pc % 12 for pc in prev_chord_pcs)
        cur_sorted = sorted(pc % 12 for pc in chord_pcs)
        # Match voices by minimizing total semitone movement
        n = max(len(prev_sorted), len(cur_sorted))
        # Pad shorter with repeated notes
        while len(prev_sorted) < n:
            prev_sorted.append(prev_sorted[-1])
        while len(cur_sorted) < n:
            cur_sorted.append(cur_sorted[-1])
        for p, c in zip(prev_sorted, cur_sorted):
            s = abs(c - p)
            s = min(s, 12 - s)
            if s > 0:
                # Perceptual distance in TIS
                p_tiv = chroma_to_tiv(chord_chroma(p, "major"))
                c_tiv = chroma_to_tiv(chord_chroma(c, "major"))
                mu = _tiv_euclidean(p_tiv, c_tiv) + 0.01
                vl += s * (1.0 + mu)

    total = tonal_dist + _DISSONANCE_WEIGHT * dissonance + _VOICE_LEADING_WEIGHT * vl

    return {
        "tonal_distance": tonal_dist,
        "dissonance": dissonance,
        "voice_leading": vl,
        "total": total,
    }


def tension_curve_for_progression(
    progression: list[tuple[int, str]],
    key_root: int = 0,
    key_major: bool = True,
) -> list[float]:
    """Compute per-chord tension values for a complete progression.

    Args:
        progression: List of (root_pc, quality_name) tuples.
        key_root: Key root pitch class.
        key_major: True for major key.

    Returns:
        List of total tension values, one per chord.
    """
    if not progression:
        return []

    tensions = []
    prev_pcs = None

    for i, (root, quality) in enumerate(progression):
        intervals = _QUALITY_INTERVALS.get(quality, [0, 4, 7])
        pcs = [(root + iv) % 12 for iv in intervals]

        t = compute_tension(pcs, prev_pcs, key_root, key_major)
        tensions.append(t["total"])
        prev_pcs = pcs

    return tensions


def tension_similarity(
    candidate: list[float],
    target: list[float],
) -> float:
    """Score how well a candidate tension curve matches a target.

    Uses Pearson correlation when target has meaningful variance,
    otherwise negative mean absolute difference.

    Returns:
        Float score. Higher = better match.
    """
    if not candidate or not target:
        return 0.0

    n = min(len(candidate), len(target))
    c = np.array(candidate[:n])
    t = np.array(target[:n])

    if n < 2:
        return -abs(c[0] - t[0])

    t_var = float(np.var(t))
    if t_var < 1e-3:
        # Flat target: use negative MAE
        return -float(np.mean(np.abs(c - t)))

    # Pearson correlation
    c_mean = c - np.mean(c)
    t_mean = t - np.mean(t)
    denom = np.sqrt(np.sum(c_mean ** 2) * np.sum(t_mean ** 2))
    if denom < 1e-10:
        return 0.0
    return float(np.sum(c_mean * t_mean) / denom)


# ---------------------------------------------------------------------------
# Surprise contour (from SurpriseNet, Chen et al. 2021)
# ---------------------------------------------------------------------------

def surprise_contour(
    progression: list[tuple[int, str]],
    pchange: np.ndarray,
    type_to_idx: dict[str, int],
) -> list[float]:
    """Compute surprise contour for a chord progression.

    Surprise = -log p(chord_t | chord_{t-1}) from a first-order Markov chain.

    Args:
        progression: List of (root_pc, quality_name) tuples.
        pchange: Trained transition matrix, shape [n_types, 12, n_types].
                 pchange[type_prev, interval, type_next].
        type_to_idx: Mapping from quality name to type index.

    Returns:
        List of surprise values (one per transition, so len-1).
    """
    if len(progression) < 2:
        return []

    surprises = []
    eps = 1e-10

    for i in range(1, len(progression)):
        prev_root, prev_quality = progression[i - 1]
        cur_root, cur_quality = progression[i]

        prev_type = type_to_idx.get(prev_quality, 0)
        cur_type = type_to_idx.get(cur_quality, 0)
        interval = (cur_root - prev_root) % 12

        if prev_type < pchange.shape[0] and cur_type < pchange.shape[2]:
            prob = pchange[prev_type, interval, cur_type]
        else:
            prob = eps

        surprises.append(-math.log(max(prob, eps)))

    return surprises
