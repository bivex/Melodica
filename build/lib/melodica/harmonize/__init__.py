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
