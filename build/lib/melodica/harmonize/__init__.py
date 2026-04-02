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
harmonize/ — Auto-harmonization module.

Two algorithms:
1. FunctionalHarmonizer — 18th-century functional harmony
2. RuleBasedHarmonizer — Markov chain with chord progression rules
"""

from melodica.harmonize.auto_harmonize import FunctionalHarmonizer, RuleBasedHarmonizer
from melodica.harmonize.advanced import (
    HMMHarmonizer,
    HMM2Harmonizer,
    HMM3Harmonizer,
    GraphSearchHarmonizer,
    GeneticHarmonizer,
    ChromaticMediantHarmonizer,
    ModalInterchangeHarmonizer,
)

__all__ = [
    "FunctionalHarmonizer",
    "RuleBasedHarmonizer",
    "HMMHarmonizer",
    "HMM2Harmonizer",
    "HMM3Harmonizer",
    "GraphSearchHarmonizer",
    "GeneticHarmonizer",
    "ChromaticMediantHarmonizer",
    "ModalInterchangeHarmonizer",
]
