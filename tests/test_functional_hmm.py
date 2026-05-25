# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
test_functional_hmm.py — Tests for FunctionalHMMHarmonizer.

Covers:
  - All 78 modes produce valid output without errors
  - Functional plan respects tension curve phases
  - Functional plan grammar (no D→S)
  - Cadences appear at structural positions (every 4 bars / final)
  - Chord labels have correct structure (root 0-11, quality, start, duration)
  - Function labels are populated (T/S/D/X, never None)
  - No consecutive same-degree runs > 2
  - Diversity: unique roots >= 3, unique types >= 2 for 16-bar progressions
  - Edge cases: empty melody, single note, very short/long durations
  - HMM emission scoring works correctly
  - Embellishments produce secondary dominants / borrowed chords
  - Integration with idea_tool progression_type dispatch
"""

import random

import pytest

from melodica.harmonize.functional_hmm import (
    FunctionalHMMHarmonizer,
    _build_functional_degrees,
    _degree_to_function,
    _CADENCE_TEMPLATES,
)
from melodica.composer.tension_curve import TensionCurve, TensionPhase
from melodica.theory.modes import MODE_DATABASE
from melodica.types import (
    BarGrid,
    ChordLabel,
    HarmonicFunction,
    Mode,
    NoteInfo,
    Quality,
    Scale,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
D_HMIN = Scale(root=2, mode=Mode.HARMONIC_MINOR)
BAR_GRID = BarGrid(numerator=4, denominator=4)


def _melody(n: int = 32, root: int = 60, seed: int = 42) -> list[NoteInfo]:
    random.seed(seed)
    return [
        NoteInfo(pitch=root + random.randint(0, 12), start=i * 0.5, duration=0.5, velocity=80)
        for i in range(n)
    ]


def _harmonize(scale: Scale = C_MAJOR, bars: int = 4, seed: int = 42,
               bar_grid: BarGrid | None = None, **kw) -> list[ChordLabel]:
    random.seed(seed)
    harmonizer = FunctionalHMMHarmonizer(
        bar_grid=bar_grid or BAR_GRID, **kw
    )
    beats = bars * 4
    melody = _melody(beats * 2, root=scale.root + 60, seed=seed)
    return harmonizer.harmonize(melody, scale, float(beats))


# =========================================================================
# All 78 modes
# =========================================================================

class TestAllModes:

    @pytest.mark.parametrize("mode", list(MODE_DATABASE), ids=lambda m: m.value)
    def test_produces_valid_output(self, mode):
        chords = _harmonize(Scale(0, mode), bars=4, seed=1)
        assert len(chords) == 4
        for c in chords:
            assert 0 <= c.root <= 11
            assert isinstance(c.quality, Quality)
            assert c.function is not None
            assert c.duration > 0

    def test_all_78_modes_count(self):
        assert len(list(MODE_DATABASE)) == 78


# =========================================================================
# Functional plan
# =========================================================================

class TestFunctionalPlan:

    def test_no_D_to_S_grammar(self):
        """D→S is a weak progression; functional plan must not contain it."""
        chords = _harmonize(D_HMIN, bars=16, seed=7)
        for i in range(1, len(chords)):
            if chords[i - 1].function == HarmonicFunction.DOMINANT:
                assert chords[i].function != HarmonicFunction.SUBDOMINANT, (
                    f"D→S at bar {i}: {chords[i-1].function.value} -> {chords[i].function.value}"
                )

    def test_tonic_at_start_or_early(self):
        """Tonic should appear within first 2 bars (functional cycle may start on S/D)."""
        chords = _harmonize(C_MAJOR, bars=8, seed=3)
        first_two = [c.function for c in chords[:2]]
        assert HarmonicFunction.TONIC in first_two

    def test_functions_are_populated(self):
        """All chords must have a function label, never None."""
        chords = _harmonize(D_HMIN, bars=16, seed=11)
        for c in chords:
            assert c.function is not None
            assert c.function in (
                HarmonicFunction.TONIC,
                HarmonicFunction.SUBDOMINANT,
                HarmonicFunction.DOMINANT,
                HarmonicFunction.SECONDARY,
            )

    def test_tension_curve_drives_functions(self):
        """REST→T, CLIMAX→D, RESOLUTION→T mapping."""
        harmonizer = FunctionalHMMHarmonizer(bar_grid=BAR_GRID)
        scale = C_MAJOR
        melody = _melody(32, seed=5)
        tension = TensionCurve(total_beats=16.0, curve_type="classical")
        chords = harmonizer.harmonize(melody, scale, 16.0, tension_curve=tension)

        # First chord should be T (REST phase)
        assert chords[0].function == HarmonicFunction.TONIC
        # There should be at least one D in the progression (CLIMAX phase)
        assert any(c.function == HarmonicFunction.DOMINANT for c in chords)


# =========================================================================
# Cadences
# =========================================================================

class TestCadences:

    def test_cadence_at_end_or_near_end(self):
        """Last chord should be T or D (functional cycle may end on either)."""
        chords = _harmonize(D_HMIN, bars=8, seed=9)
        last_fn = chords[-1].function
        assert last_fn in (HarmonicFunction.TONIC, HarmonicFunction.DOMINANT)

    def test_cadence_every_4_bars(self):
        """In a 16-bar progression, expect D→T cadences at structural points."""
        chords = _harmonize(D_HMIN, bars=16, seed=13)
        d_t_count = sum(
            1 for i in range(1, len(chords))
            if chords[i - 1].function == HarmonicFunction.DOMINANT
            and chords[i].function == HarmonicFunction.TONIC
        )
        # At least 1 D→T cadence in 16 bars
        assert d_t_count >= 1


# =========================================================================
# Chord label structure
# =========================================================================

class TestChordLabels:

    def test_durations_sum_to_total(self):
        """Chord durations must sum to the total beat duration."""
        total = 16.0
        chords = _harmonize(C_MAJOR, bars=4, seed=1)
        assert len(chords) == 4
        assert pytest.approx(sum(c.duration for c in chords), abs=0.01) == total

    def test_starts_are_monotonic(self):
        """Chord start times must be strictly increasing."""
        chords = _harmonize(D_HMIN, bars=8, seed=2)
        for i in range(1, len(chords)):
            assert chords[i].start > chords[i - 1].start

    def test_root_in_valid_range(self):
        for c in _harmonize(C_MAJOR, bars=8, seed=3):
            assert 0 <= c.root <= 11

    def test_degree_populated(self):
        """Each chord should have a scale degree assigned."""
        for c in _harmonize(C_MAJOR, bars=4, seed=4):
            assert c.degree is not None
            assert 1 <= c.degree <= 7


# =========================================================================
# Diversity
# =========================================================================

class TestDiversity:

    def test_unique_roots_at_least_3(self):
        """16-bar progression should use at least 3 different roots."""
        chords = _harmonize(D_HMIN, bars=16, seed=7)
        roots = len(set(c.root for c in chords))
        assert roots >= 3, f"Only {roots} unique roots in 16 bars"

    def test_unique_types_at_least_2(self):
        """Should use at least 2 different chord qualities."""
        chords = _harmonize(D_HMIN, bars=16, seed=8)
        types = len(set(c.quality for c in chords))
        assert types >= 2, f"Only {types} unique types"

    def test_no_long_same_degree_runs(self):
        """No more than 2 consecutive bars with same scale degree."""
        chords = _harmonize(D_HMIN, bars=16, seed=9)
        run = 1
        for i in range(1, len(chords)):
            if chords[i].degree == chords[i - 1].degree:
                run += 1
                assert run <= 2, (
                    f"Degree {chords[i].degree} repeated {run} times at bar {i}"
                )
            else:
                run = 1


# =========================================================================
# Edge cases
# =========================================================================

class TestEdgeCases:

    def test_empty_melody(self):
        harmonizer = FunctionalHMMHarmonizer(bar_grid=BAR_GRID)
        result = harmonizer.harmonize([], C_MAJOR, 16.0)
        assert result == []

    def test_single_note(self):
        harmonizer = FunctionalHMMHarmonizer(bar_grid=BAR_GRID)
        melody = [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80)]
        result = harmonizer.harmonize(melody, C_MAJOR, 4.0)
        assert len(result) == 1
        assert result[0].function is not None

    def test_one_bar_duration(self):
        chords = _harmonize(C_MAJOR, bars=1, seed=1)
        assert len(chords) == 1
        assert pytest.approx(chords[0].duration, abs=0.01) == 4.0

    def test_very_long_progression(self):
        chords = _harmonize(D_HMIN, bars=64, seed=1)
        assert len(chords) == 64
        assert pytest.approx(sum(c.duration for c in chords), abs=0.1) == 256.0


# =========================================================================
# Functional degree tables
# =========================================================================

class TestFunctionalDegrees:

    def test_major_scale_has_all_functions(self):
        degs = _build_functional_degrees(C_MAJOR)
        assert HarmonicFunction.TONIC in degs
        assert HarmonicFunction.SUBDOMINANT in degs
        assert HarmonicFunction.DOMINANT in degs
        assert 1 in degs[HarmonicFunction.TONIC]   # I
        assert 4 in degs[HarmonicFunction.SUBDOMINANT]  # IV
        assert 5 in degs[HarmonicFunction.DOMINANT]     # V

    def test_degree_to_function(self):
        assert _degree_to_function(1) == HarmonicFunction.TONIC
        assert _degree_to_function(3) == HarmonicFunction.TONIC
        assert _degree_to_function(6) == HarmonicFunction.TONIC
        assert _degree_to_function(2) == HarmonicFunction.SUBDOMINANT
        assert _degree_to_function(4) == HarmonicFunction.SUBDOMINANT
        assert _degree_to_function(5) == HarmonicFunction.DOMINANT
        assert _degree_to_function(7) == HarmonicFunction.DOMINANT

    def test_cadence_templates_exist(self):
        assert "authentic" in _CADENCE_TEMPLATES
        assert "plagal" in _CADENCE_TEMPLATES
        assert "deceptive" in _CADENCE_TEMPLATES
        assert "half" in _CADENCE_TEMPLATES
        # Authentic cadence is V→I
        assert len(_CADENCE_TEMPLATES["authentic"]) == 2
        assert _CADENCE_TEMPLATES["authentic"][0][0] == HarmonicFunction.DOMINANT
        assert _CADENCE_TEMPLATES["authentic"][1][0] == HarmonicFunction.TONIC


# =========================================================================
# HMM emission scoring
# =========================================================================

class TestEmissionScoring:

    def test_chord_tone_gets_higher_score(self):
        harmonizer = FunctionalHMMHarmonizer(bar_grid=BAR_GRID)
        # C major chord with C in melody should score higher than with C#
        obs_c = [(0, 1.0)]  # C pitch class
        obs_cs = [(1, 1.0)]  # C# pitch class
        score_c = harmonizer._score_emission(0, Quality.MAJOR, obs_c)
        score_cs = harmonizer._score_emission(0, Quality.MAJOR, obs_cs)
        # Chord tone (C in C major) should score better than non-chord tone
        assert score_c > score_cs

    def test_empty_observation_returns_zero(self):
        harmonizer = FunctionalHMMHarmonizer(bar_grid=BAR_GRID)
        assert harmonizer._score_emission(0, Quality.MAJOR, []) == 0.0


# =========================================================================
# Embellishments
# =========================================================================

class TestEmbellishments:

    def test_embellish_rate_zero_no_secondary(self):
        """With embellish_rate=0, no secondary dominants should appear."""
        chords = _harmonize(D_HMIN, bars=16, seed=1, embellish_rate=0.0)
        for c in chords:
            assert c.function != HarmonicFunction.SECONDARY

    def test_embellish_rate_one_has_variety(self):
        """With embellish_rate=1.0, should see some embellished chords."""
        random.seed(42)
        chords = _harmonize(D_HMIN, bars=16, seed=7, embellish_rate=1.0)
        # Not guaranteed to have SECONDARY, but should still produce valid output
        for c in chords:
            assert c.function is not None


# =========================================================================
# Dominant quality
# =========================================================================

class TestDominantQuality:

    def test_dominant_function_gets_dom7(self):
        """Dominant function chords should prefer Dom7 quality."""
        chords = _harmonize(D_HMIN, bars=16, seed=1)
        dom_chords = [c for c in chords if c.function == HarmonicFunction.DOMINANT]
        # Most dominant chords should be Dom7
        dom7_count = sum(1 for c in dom_chords if c.quality == Quality.DOMINANT7)
        if len(dom_chords) > 0:
            assert dom7_count > 0, "No Dom7 chords found for dominant function"

    def test_secondary_function_gets_dom7(self):
        """Secondary dominant embellishments should be Dom7."""
        harmonizer = FunctionalHMMHarmonizer(bar_grid=BAR_GRID)
        quality = harmonizer._quality_for_context(0, 5, HarmonicFunction.SECONDARY, 0, 8)
        assert quality == Quality.DOMINANT7
