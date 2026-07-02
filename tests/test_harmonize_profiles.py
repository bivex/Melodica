# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""Tests for the named harmonizer profiles (genre presets)."""

from __future__ import annotations

import pytest

from melodica.harmonize import HARMONIZER_PROFILES, harmonizer_profile


def test_known_profiles():
    assert set(HARMONIZER_PROFILES) >= {"pop", "jazz"}


def test_genre_defining_knob():
    # completion_bonus is the genre-defining knob (see HARMONIZATION_CEILING.md).
    assert harmonizer_profile("pop").completion_bonus == 0.0
    assert harmonizer_profile("jazz").completion_bonus == 5.0


def test_default_is_pop():
    assert harmonizer_profile().completion_bonus == 0.0


def test_returns_independent_copy():
    a = harmonizer_profile("jazz")
    a.completion_bonus = 99.0
    # the stored preset is untouched
    assert harmonizer_profile("jazz").completion_bonus == 5.0
    assert HARMONIZER_PROFILES["jazz"].completion_bonus == 5.0


def test_overrides_apply():
    cfg = harmonizer_profile("jazz", key_coupling_weight=0.3, completion_bonus=8.0)
    assert cfg.completion_bonus == 8.0
    assert cfg.key_coupling_weight == 0.3
    # override does not leak into the preset
    assert harmonizer_profile("jazz").completion_bonus == 5.0


def test_unknown_profile_raises():
    with pytest.raises(ValueError, match="Unknown harmonizer profile"):
        harmonizer_profile("shoegaze")


# A harmonization-outcome assertion (jazz retains 7ths, pop collapses) belongs in
# the benchmark, not here: tests/conftest.py swaps in synth-gold weights, under
# which the triad-collapse doesn't reproduce. See docs/HARMONIZATION_CEILING.md.
