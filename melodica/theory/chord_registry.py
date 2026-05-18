# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18
# Last Updated: 2026-05-18
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

from melodica.theory.chords import Quality

ROMAN_QUALITY_MAP: dict[str, Quality] = {
    # Оркестровые
    "mystic":  Quality.SCRIABIN_MYSTIC,
    "poly":    Quality.POLY_CHORD_C_FM,
    "cl2":     Quality.CLUSTER_MINOR_2,
    "cM2":     Quality.CLUSTER_MAJOR_2,
    "b9":      Quality.MAJ_TRIAD_B9,
    # Jazz
    "7s11":    Quality.DOM7_SHARP11,   # V7s11 → Lydian dominant
    "7b9":     Quality.DOM7_FLAT9,     # V7b9  → Spanish Phrygian
    "7s9":     Quality.DOM7_SHARP9,    # V7s9  → Hendrix
    # Modal
    "phryg":   Quality.PHRYGIAN_MAJOR,
    "lyda":    Quality.LYDIAN_AUG,
    # Clusters
    "cl4":     Quality.CLUSTER_4TH,
    "tc":      Quality.TONE_CLUSTER,
    # Genre-Specific Extensions
    "oct":     Quality.OCTATONIC_CLUSTER,
    "7alt":    Quality.ALTERED_DOMINANT,
    "q4":      Quality.STACK_OF_4THS,
    "spec":    Quality.SPECTRAL_CHORD,
}

import re
_SORTED_TOKENS = sorted(ROMAN_QUALITY_MAP.keys(), key=len, reverse=True)
_CUSTOM_PATTERN = "|".join(re.escape(k) for k in _SORTED_TOKENS)
