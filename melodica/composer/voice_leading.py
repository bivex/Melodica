# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
composer/voice_leading.py — SATB Voice Leading Engine.

Re-exports unified functionality from melodica.theory.voice_leading for backward compatibility.
"""

from __future__ import annotations

from melodica.theory.voice_leading import (
    VOICE_ORDER,
    VOICE_RANGES,
    VoiceLeadingEngine,
    _interval,
    _is_parallel_fifth,
    _is_parallel_octave,
    _motion_type,
    _pitch_class,
    classify_motion,
    has_parallel_motion,
    interval,
    is_parallel_fifth,
    is_parallel_octave,
    pitch_class,
)

__all__ = [
    "VOICE_RANGES",
    "VOICE_ORDER",
    "VoiceLeadingEngine",
    "pitch_class",
    "interval",
    "is_parallel_fifth",
    "is_parallel_octave",
    "classify_motion",
    "has_parallel_motion",
    "_pitch_class",
    "_interval",
    "_is_parallel_fifth",
    "_is_parallel_octave",
    "_motion_type",
]
