# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
voice_leading.py — Post-generation parallel-motion correction.

Re-exports unified functionality from melodica.theory.voice_leading for backward compatibility.
"""

from __future__ import annotations

from melodica.theory.voice_leading import (
    DEFAULT_RANGE,
    GM_RANGES,
    _DEFAULT_RANGE,
    _GM_RANGE,
    _get_range,
    _note_with_pitch,
    correct_parallels,
    get_instrument_range,
    is_parallel_fifth,
    is_parallel_octave,
)

__all__ = [
    "correct_parallels",
    "get_instrument_range",
    "is_parallel_fifth",
    "is_parallel_octave",
    "GM_RANGES",
    "DEFAULT_RANGE",
    "_GM_RANGE",
    "_DEFAULT_RANGE",
    "_get_range",
    "_note_with_pitch",
]
