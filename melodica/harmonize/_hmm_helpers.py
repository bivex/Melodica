"""
_hmm_helpers.py — Shared helpers and constants for harmonizers.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

from melodica.types import ChordLabel, Quality, HarmonicFunction, Scale, Mode, NoteInfo

def _chord_pcs_for_degree(root_pc: int, quality: Quality) -> list[int]:
    """Get pitch classes for a chord given its root pitch class and quality."""
    if quality == Quality.MAJOR:
        return [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12]
    elif quality == Quality.MINOR:
        return [root_pc, (root_pc + 3) % 12, (root_pc + 7) % 12]
    elif quality == Quality.DIMINISHED:
        return [root_pc, (root_pc + 3) % 12, (root_pc + 6) % 12]
    elif quality == Quality.DOMINANT7:
        return [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12, (root_pc + 10) % 12]
    elif quality == Quality.MAJOR7:
        return [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12, (root_pc + 11) % 12]
    elif quality == Quality.MINOR7:
        return [root_pc, (root_pc + 3) % 12, (root_pc + 7) % 12, (root_pc + 10) % 12]
    return [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12]
def _voice_leading_cost(pcs_a: list[int], pcs_b: list[int]) -> float:
    """Minimal voice leading distance between two chord pitch-class sets."""
    if not pcs_a or not pcs_b:
        return 6.0
    # For each pc in A, find closest in B
    total = 0.0
    for a in pcs_a:
        best = min(abs(a - b) % 12 for b in pcs_b)
        # Also check wrapping (e.g., 11→0 is distance 1)
        best = min(best, 12 - best)
        total += best
    return total / len(pcs_a)
def _melody_fits_chord(melody_pc: int, chord_pcs: list[int]) -> bool:
    """Check if melody note fits chord."""
    return melody_pc in chord_pcs
def _build_diatonic_chords(scale: Scale) -> list[tuple[int, Quality]]:
    """Build all diatonic chords for a scale."""
    degs = scale.degrees()
    result = []
    for i, root_pc in enumerate(degs):
        deg = i + 1
        # Determine quality from interval pattern
        third = degs[(i + 2) % len(degs)]
        fifth = degs[(i + 4) % len(degs)]
        third_interval = (third - root_pc) % 12
        fifth_interval = (fifth - root_pc) % 12

        if third_interval == 4 and fifth_interval == 7:
            quality = Quality.MAJOR
        elif third_interval == 3 and fifth_interval == 7:
            quality = Quality.MINOR
        elif third_interval == 3 and fifth_interval == 6:
            quality = Quality.DIMINISHED
        elif third_interval == 4 and fifth_interval == 8:
            quality = Quality.AUGMENTED
        else:
            quality = Quality.MAJOR
        result.append((root_pc, quality))
    return result

_CADENCE_BONUSES: dict[tuple[int, int], float] = {
    (4, 0): 0.8,  # V → I  (authentic cadence)
    (1, 4): 0.5,  # ii → V  (half cadence setup)
    (5, 4): 0.6,  # vi → IV (deceptive setup)
    (3, 0): 0.4,  # IV → I  (plagal cadence)
    (6, 4): 0.3,  # vii° → V
}
_FUNCTION_MAP = {0: 0, 3: 1, 5: 2}  # degree → function (T=0, S=1, D=2)
_FUNCTION_RULES_HMM2 = {
    # function → {next_function: weight}
    0: {1: 0.45, 2: 0.40, 0: 0.15},  # T → S or D
    1: {2: 0.65, 0: 0.25, 1: 0.10},  # S → D
    2: {0: 0.60, 1: 0.25, 2: 0.15},  # D → T
}
_SECONDARY_DOMINANTS: dict[int, tuple[int, Quality]] = {
    1: ((7, Quality.DOMINANT7),),  # V7/vi → vi  (not used, vi=5 in 0-index)
    2: ((2, Quality.DOMINANT7),),  # V7/ii
    3: ((6, Quality.DOMINANT7),),  # V7/iii
    4: ((11, Quality.DOMINANT7),),  # V7/IV
    5: ((4, Quality.DOMINANT7),),  # V7/V
}
_EXTENSIONS: dict[int, list[Quality]] = {
    0: [Quality.MAJOR, Quality.MAJOR7, Quality.DOMINANT7],  # I
    1: [Quality.MINOR, Quality.MINOR7],  # ii
    2: [Quality.MINOR, Quality.MINOR7],  # iii
    3: [Quality.MAJOR, Quality.MAJOR7],  # IV
    4: [Quality.MAJOR, Quality.DOMINANT7],  # V
    5: [Quality.MINOR, Quality.MINOR7],  # vi
    6: [Quality.DIMINISHED, Quality.HALF_DIM7],  # vii°
}
