"""Central registry merging all generator category mappings."""

from ._basic import BASIC_GENERATORS
from ._ai import AI_GENERATORS
from ._patterns import PATTERN_GENERATORS
from ._ornamentation import ORNAMENTATION_GENERATORS
from ._genre_a_f import GENRE_A_F
from ._genre_g_p import GENRE_G_P
from ._genre_q_z_adv import GENRE_Q_Z_ADV
from ._utilities import UTILITY_GENERATORS

# Merge all mappings into one registry
GENERATOR_REGISTRY: dict[str, type] = {}
GENERATOR_REGISTRY.update(BASIC_GENERATORS)
GENERATOR_REGISTRY.update(AI_GENERATORS)
GENERATOR_REGISTRY.update(PATTERN_GENERATORS)
GENERATOR_REGISTRY.update(ORNAMENTATION_GENERATORS)
GENERATOR_REGISTRY.update(GENRE_A_F)
GENERATOR_REGISTRY.update(GENRE_G_P)
GENERATOR_REGISTRY.update(GENRE_Q_Z_ADV)
GENERATOR_REGISTRY.update(UTILITY_GENERATORS)

__all__ = ["GENERATOR_REGISTRY"]
