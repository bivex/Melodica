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

"""
advanced.py — Advanced harmonization algorithms (re-export hub).
"""

from __future__ import annotations

from melodica.harmonize._hmm_helpers import (
    _chord_pcs_for_degree,
    _voice_leading_cost,
    _melody_fits_chord,
    _build_diatonic_chords,
)
from melodica.harmonize._hmm_core import (
    HMMHarmonizer,
    HMM2Harmonizer,
    HMM3Harmonizer,
)
from melodica.harmonize._specialized import (
    GraphSearchHarmonizer,
    GeneticHarmonizer,
    ChromaticMediantHarmonizer,
    ModalInterchangeHarmonizer,
)

__all__ = [
    "HMMHarmonizer",
    "HMM2Harmonizer",
    "HMM3Harmonizer",
    "GraphSearchHarmonizer",
    "GeneticHarmonizer",
    "ChromaticMediantHarmonizer",
    "ModalInterchangeHarmonizer",
]
