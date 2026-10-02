# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.generate — Next-generation generation engine: profiles, families, and kernel.
"""

from __future__ import annotations

from melodica.generate.kernel import (
    apply_note_density,
    resolve_bounded_pitch,
    fit_to_range,
    generate_lfo_cc,
    apply_phrase_arch,
    limit_polyphony,
)
from melodica.generate.profile import (
    InstrumentProfile,
    load_profile,
    get_profile,
    list_profiles,
)
from melodica.generate.family import (
    FamilyGenerator,
    MalletFamily,
)

__all__ = [
    "apply_note_density",
    "resolve_bounded_pitch",
    "fit_to_range",
    "generate_lfo_cc",
    "apply_phrase_arch",
    "limit_polyphony",
    "InstrumentProfile",
    "load_profile",
    "get_profile",
    "list_profiles",
    "FamilyGenerator",
    "MalletFamily",
]
