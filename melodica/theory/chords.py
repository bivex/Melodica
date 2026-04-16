# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

from __future__ import annotations
from enum import IntEnum

class Quality(IntEnum):
    """Chord quality. Modeled after the chord-quality integer."""
    MAJOR = 0
    MINOR = 1
    DIMINISHED = 2
    AUGMENTED = 3
    MAJOR7 = 4
    DOMINANT7 = 5
    MINOR7 = 6
    HALF_DIM7 = 7
    FULL_DIM7 = 8
    SUS2 = 9
    SUS4 = 10
    POWER = 11
    
    # --- Orchestral & Cluster Extensions ---
    CLUSTER_MINOR_2 = 12
    CLUSTER_MAJOR_2 = 13
    POLY_CHORD_C_FM = 14
    SCRIABIN_MYSTIC = 15
    MAJ_TRIAD_B9 = 16  # Major triad with flat 9th for dissonance

CHORD_TEMPLATES: dict[Quality, list[int]] = {
    Quality.MAJOR:      [0, 4, 7],
    Quality.MINOR:      [0, 3, 7],
    Quality.DIMINISHED: [0, 3, 6],
    Quality.AUGMENTED:  [0, 4, 8],
    Quality.DOMINANT7:  [0, 4, 7, 10],
    Quality.MAJOR7:     [0, 4, 7, 11],
    Quality.MINOR7:     [0, 3, 7, 10],
    Quality.HALF_DIM7:  [0, 3, 6, 10],
    Quality.FULL_DIM7:  [0, 3, 6, 9],
    Quality.SUS2:       [0, 2, 7],
    Quality.SUS4:       [0, 5, 7],
    Quality.POWER:      [0, 7],
    
    # Clusters & Poly-chords
    Quality.CLUSTER_MINOR_2: [0, 1, 4, 7],
    Quality.CLUSTER_MAJOR_2: [0, 2, 4, 7],
    Quality.POLY_CHORD_C_FM: [0, 4, 7, 10, 14],
    Quality.SCRIABIN_MYSTIC: [0, 4, 7, 10, 13, 16],
    Quality.MAJ_TRIAD_B9: [0, 4, 7, 13],
}
