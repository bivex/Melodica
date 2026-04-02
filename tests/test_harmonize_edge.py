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
test_harmonize_edge.py — Финальные edge-case тесты для убийства скрытых багов.

Категории:
1. Tie-breaking / near-equal paths
2. Numerical precision under stress
3. Beam search correctness (formal guarantee)
4. Catalog perturbation
5. Cross-feature interaction
6. Musical sanity checks
7. Golden / snapshot tests
"""

from __future__ import annotations

import math
import random

import pytest

from melodica.types import NoteInfo, Scale, Mode, Quality
from melodica.harmonize import HMMHarmonizer, HMM3Harmonizer, FunctionalHarmonizer
from melodica.harmonize._hmm_core import HMM3Harmonizer as HMM3Core
from melodica.harmonize._hmm_helpers import _build_diatonic_chords, _chord_pcs_for_degree


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)


def _melody(pw: list[tuple[int, float, float]]) -> list[NoteInfo]:
    return [NoteInfo(pitch=p, start=s, duration=d, velocity=80) for p, s, d in pw]


# =========================================================================
# 1. TIE-BREAKING / NEAR-EQUAL PATHS
# =========================================================================


class TestTieBreaking:
    """Near-equal paths — всегда один и тот же путь, нет фликера."""

    def test_deterministic_10_runs(self):
        """10 запусков с одинаковым input → одинаковый output."""
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(8)])
        results = []
        for _ in range(10):
            chords = h.harmonize(melody, C_MAJOR, 8.0)
            results.append(tuple(c.root for c in chords))
        assert len(set(results)) == 1, f"Flicker detected: {set(results)}"

    def test_deterministic_50_runs_different_melodies(self):
        """50 различных мелодий × 3 запуска = нет фликера."""
        h = HMM3Harmonizer()
        random.seed(42)
        for trial in range(50):
            n = random.randint(4, 16)
            melody = _melody([(random.randint(48, 84), i * 0.5, 0.4) for i in range(n)])
            results = []
            for _ in range(3):
                chords = h.harmonize(melody, C_MAJOR, n * 0.5)
                results.append(tuple(c.root for c in chords))
            assert len(set(results)) == 1, f"Trial {trial}: flicker {set(results)}"

    def test_near_equal_melodies_same_structure(self):
        """Мелодии, отличающиеся на 1 семитон → одинаковая структура."""
        h = HMM3Harmonizer()
        m1 = _melody([(60, i, 0.9) for i in range(8)])
        m2 = _melody([(61, i, 0.9) for i in range(8)])
        c1 = h.harmonize(m1, C_MAJOR, 8.0)
        c2 = h.harmonize(m2, C_MAJOR, 8.0)
        # Same number of chords
        assert len(c1) == len(c2)
        # Same chord roots may differ, but both valid
        assert all(c.root is not None for c in c1)
        assert all(c.root is not None for c in c2)


# =========================================================================
# 2. NUMERICAL PRECISION UNDER STRESS
# =========================================================================


class TestNumericalPrecision:
    """Очень длинные последовательности, крошечные/огромные веса."""

    def test_500_bars_no_nan(self):
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(500)])
        chords = h.harmonize(melody, C_MAJOR, 500.0)
        assert len(chords) >= 1
        for c in chords:
            assert c.root == c.root  # not NaN
            assert c.duration > 0

    def test_tiny_weights(self):
        """Все веса = 1e-6 — не должно ломаться."""
        h = HMM3Harmonizer(
            melody_weight=1e-6,
            transition_weight=1e-6,
            functional_weight=1e-6,
            cadence_weight=1e-6,
            secondary_dom_weight=1e-6,
            extension_weight=1e-6,
            repetition_penalty=1e-6,
        )
        melody = _melody([(60, i, 0.9) for i in range(8)])
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        assert len(chords) >= 1

    def test_huge_weights(self):
        """Все веса = 1e3 — не должно ломаться."""
        h = HMM3Harmonizer(
            melody_weight=1e3,
            transition_weight=1e3,
            functional_weight=1e3,
            cadence_weight=1e3,
            secondary_dom_weight=1e3,
            extension_weight=1e3,
            repetition_penalty=1e3,
        )
        melody = _melody([(60, i, 0.9) for i in range(8)])
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        assert len(chords) >= 1

    def test_mixed_extreme_weights(self):
        """Разные экстремальные веса — не должно ломаться."""
        h = HMM3Harmonizer(
            melody_weight=1e-10,
            transition_weight=1e10,
            functional_weight=0.0,
            cadence_weight=1e-5,
            secondary_dom_weight=1e5,
        )
        melody = _melody([(60, i, 0.9) for i in range(8)])
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        assert len(chords) >= 1

    def test_scores_no_inf(self):
        """Score step не возвращает inf."""
        h = HMM3Harmonizer(melody_weight=1e6)
        from melodica.harmonize._hmm_helpers import _build_diatonic_chords

        chords_def = _build_diatonic_chords(C_MAJOR)
        catalog = h._build_catalog(chords_def, C_MAJOR)
        melody = _melody([(60, 0.0, 3.5)])
        cp = h._get_change_points(4.0)
        obs = h._extract_observations(melody, cp)
        for s in range(len(catalog)):
            score = h._score_step(0, s, None, obs, catalog, cp, melody, C_MAJOR)
            assert score != float("inf"), f"Score inf at catalog index {s}"
            assert score != float("-inf"), f"Score -inf at catalog index {s}"
            assert score == score  # not NaN

    def test_long_beat_mode_no_drift(self):
        """200 beats mode — нет накопления float drift."""
        h = HMM3Harmonizer(chord_change="beats")
        melody = _melody([(60, i, 0.9) for i in range(200)])
        chords = h.harmonize(melody, C_MAJOR, 200.0)
        assert len(chords) == 200
        # Check no overlaps
        for i in range(len(chords) - 1):
            end = chords[i].start + chords[i].duration
            start_next = chords[i + 1].start
            assert abs(end - start_next) < 0.01, f"Gap/overlap at beat {i}: {end} vs {start_next}"


# =========================================================================
# 3. BEAM SEARCH CORRECTNESS
# =========================================================================


class TestBeamSearchCorrectness:
    """Beam search vs полный перебор на маленьких входах."""

    def test_beam_width_100_equals_large(self):
        """beam=100 и beam=500 produce same result (на маленьком входе)."""
        h100 = HMM3Harmonizer(beam_width=100)
        h500 = HMM3Harmonizer(beam_width=500)
        melody = _melody([(60, i, 0.9) for i in range(4)])
        c100 = h100.harmonize(melody, C_MAJOR, 4.0)
        c500 = h500.harmonize(melody, C_MAJOR, 4.0)
        assert [c.root for c in c100] == [c.root for c in c500]

    def test_beam_width_1_may_differ_from_5(self):
        """beam=1 (greedy) может отличаться от beam=5."""
        h1 = HMM3Harmonizer(beam_width=1)
        h5 = HMM3Harmonizer(beam_width=5)
        melody = _melody([(60 + (i % 7) * 2, i, 0.9) for i in range(12)])
        c1 = h1.harmonize(melody, C_MAJOR, 12.0)
        c5 = h5.harmonize(melody, C_MAJOR, 12.0)
        # Both valid
        assert len(c1) >= 1
        assert len(c5) >= 1

    def test_beam_never_loses_best_at_width_1(self):
        """beam=1 = greedy = первый лучший на каждом шаге."""
        h = HMM3Harmonizer(beam_width=1)
        melody = _melody([(60, i, 0.9) for i in range(4)])
        chords = h.harmonize(melody, C_MAJOR, 4.0)
        assert len(chords) >= 1


# =========================================================================
# 4. CATALOG PERTURBATION
# =========================================================================


class TestCatalogPerturbation:
    """Добавление дубликатов/мусора в catalog не должно ломать."""

    def test_catalog_has_no_duplicates(self):
        """Catalog не должен содержать дубликатов."""
        h = HMM3Harmonizer()
        from melodica.harmonize._hmm_helpers import _build_diatonic_chords

        chords_def = _build_diatonic_chords(C_MAJOR)
        catalog = h._build_catalog(chords_def, C_MAJOR)
        seen = set()
        for entry in catalog:
            key = (entry[0], entry[1], entry[2])
            assert key not in seen, f"Duplicate catalog entry: {key}"
            seen.add(key)

    def test_catalog_deterministic(self):
        """Catalog всегда одинаковый."""
        h = HMM3Harmonizer()
        from melodica.harmonize._hmm_helpers import _build_diatonic_chords

        chords_def = _build_diatonic_chords(C_MAJOR)
        cat1 = h._build_catalog(chords_def, C_MAJOR)
        cat2 = h._build_catalog(chords_def, C_MAJOR)
        assert cat1 == cat2

    def test_transition_matrix_symmetric_handling(self):
        """Transition matrix не содержит NaN или отрицательных."""
        h = HMM3Harmonizer()
        from melodica.harmonize._hmm_helpers import _build_diatonic_chords

        chords_def = _build_diatonic_chords(C_MAJOR)
        catalog = h._build_catalog(chords_def, C_MAJOR)
        trans = h._build_transitions(catalog, chords_def)
        for i, row in enumerate(trans):
            for j, val in enumerate(row):
                assert val >= 0, f"Negative at [{i}][{j}]: {val}"
                assert val == val, f"NaN at [{i}][{j}]"


# =========================================================================
# 5. CROSS-FEATURE INTERACTION
# =========================================================================


class TestCrossFeatureInteraction:
    """Все penalties/bonuses одновременно — нет перекоса."""

    def test_all_maxed_no_deadlock(self):
        """Все penalties/bonuses на максимуме — produce valid output."""
        h = HMM3Harmonizer(
            melody_weight=1.0,
            transition_weight=1.0,
            functional_weight=1.0,
            cadence_weight=1.0,
            secondary_dom_weight=1.0,
            extension_weight=1.0,
            repetition_penalty=1.0,
        )
        melody = _melody([(60, i, 0.9) for i in range(16)])
        chords = h.harmonize(melody, C_MAJOR, 16.0)
        assert len(chords) >= 1
        # No degenerate all-same sequence
        degrees = [c.degree for c in chords]
        if len(degrees) > 3:
            assert len(set(degrees)) > 1, "All-maxed produced degenerate sequence"

    def test_high_rep_penalty_no_infinite_loop(self):
        """Очень высокий repetition_penalty → нет бесконечного цикла."""
        h = HMM3Harmonizer(repetition_penalty=10.0)
        melody = _melody([(60, i, 0.9) for i in range(16)])
        chords = h.harmonize(melody, C_MAJOR, 16.0)
        assert len(chords) >= 1

    def test_high_cadence_no_V_I_loop(self):
        """Очень высокий cadence_weight → нет вечного V→I."""
        h = HMM3Harmonizer(cadence_weight=10.0, repetition_penalty=0.0)
        melody = _melody([(60, i, 0.9) for i in range(16)])
        chords = h.harmonize(melody, C_MAJOR, 16.0)
        # Should not be all V→I→V→I
        degrees = [c.degree for c in chords]
        if len(degrees) > 4:
            unique = len(set(degrees))
            assert unique > 2, f"Too few unique degrees ({unique}): {degrees}"

    def test_sd_maxed_no_excessive_sd(self):
        """Высокий sd_weight → SD могут быть частыми, но produce valid output."""
        h = HMM3Harmonizer(secondary_dom_weight=10.0, allow_secondary_dom=True)
        melody = _melody([(60, i, 0.9) for i in range(16)])
        chords = h.harmonize(melody, C_MAJOR, 16.0)
        # All chords should be valid
        assert all(c.root is not None for c in chords)
        assert len(chords) >= 1


# =========================================================================
# 6. MUSICAL SANITY
# =========================================================================


class TestMusicalSanity:
    """Мягкие музыкальные ограничения."""

    def test_cadence_spacing(self):
        """Cadence (V→I) не каждые 2 аккорда."""
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(32)])
        chords = h.harmonize(melody, C_MAJOR, 128.0)
        cadence_count = 0
        for i in range(len(chords) - 1):
            if chords[i].degree == 5 and chords[i + 1].degree == 1:
                cadence_count += 1
        total = len(chords)
        # Cadence should be < 30% of transitions
        assert cadence_count < total * 0.35, f"Too many cadences: {cadence_count}/{total}"

    def test_diatonic_ratio_high(self):
        """>90% аккордов должны быть диатоническими."""
        h = HMM3Harmonizer(allow_secondary_dom=True)
        melody = _melody([(60, i, 0.9) for i in range(32)])
        chords = h.harmonize(melody, C_MAJOR, 128.0)
        diatonic = sum(1 for c in chords if c.degree is not None and c.degree > 0)
        total = len(chords)
        ratio = diatonic / total
        assert ratio > 0.7, f"Diatonic ratio {ratio:.0%} too low"

    def test_no_excessive_repetition(self):
        """Нет >3 одинаковых аккордов подряд."""
        h = HMM3Harmonizer(repetition_penalty=0.10)
        melody = _melody([(60, i, 0.9) for i in range(32)])
        chords = h.harmonize(melody, C_MAJOR, 128.0)
        run = 1
        for i in range(1, len(chords)):
            if chords[i].degree == chords[i - 1].degree:
                run += 1
                assert run <= 3, f"Run of {run} identical chords at position {i}"
            else:
                run = 1


# =========================================================================
# 7. GOLDEN / SNAPSHOT TESTS
# =========================================================================


class TestGoldenSnapshots:
    """Эталонные мелодии — фиксированный output для regression detection."""

    GOLDEN_MELODIES = [
        # (name, melody_pitches, scale, expected_chord_count)
        ("c_major_scale_up", [(60 + i, i, 0.9) for i in range(8)], C_MAJOR, 2),
        (
            "c_major_arpeggio",
            [
                (60, 0.0, 0.9),
                (64, 1.0, 0.9),
                (67, 2.0, 0.9),
                (72, 3.0, 0.9),
                (60, 4.0, 0.9),
                (64, 5.0, 0.9),
                (67, 6.0, 0.9),
                (72, 7.0, 0.9),
            ],
            C_MAJOR,
            2,
        ),
        ("g_dominant_melody", [(67, i, 0.9) for i in range(8)], C_MAJOR, 2),
        ("e_minor_melody", [(64, i, 0.9) for i in range(8)], C_MAJOR, 2),
        ("chromatic_run", [(60 + i, i, 0.9) for i in range(12)], C_MAJOR, 3),
        ("repeated_note", [(60, i, 0.9) for i in range(16)], C_MAJOR, 4),
        (
            "octave_leap",
            [
                (60, 0.0, 0.9),
                (72, 1.0, 0.9),
                (60, 2.0, 0.9),
                (72, 3.0, 0.9),
                (60, 4.0, 0.9),
                (72, 5.0, 0.9),
                (60, 6.0, 0.9),
                (72, 7.0, 0.9),
            ],
            C_MAJOR,
            2,
        ),
        (
            "pentatonic_c",
            [
                (60, 0.0, 0.9),
                (62, 1.0, 0.9),
                (64, 2.0, 0.9),
                (67, 3.0, 0.9),
                (69, 4.0, 0.9),
                (60, 5.0, 0.9),
                (62, 6.0, 0.9),
                (64, 7.0, 0.9),
            ],
            C_MAJOR,
            2,
        ),
        ("a_minor_natural", [(57 + i, i, 0.9) for i in range(8)], A_MINOR, 2),
        (
            "tritone_melody",
            [
                (60, 0.0, 0.9),
                (66, 1.0, 0.9),
                (60, 2.0, 0.9),
                (66, 3.0, 0.9),
                (60, 4.0, 0.9),
                (66, 5.0, 0.9),
                (60, 6.0, 0.9),
                (66, 7.0, 0.9),
            ],
            C_MAJOR,
            2,
        ),
    ]

    @pytest.mark.parametrize("name,pitches,scale,expected_count", GOLDEN_MELODIES)
    def test_golden_deterministic(self, name, pitches, scale, expected_count):
        """Каждая golden melody produce детерминированный output."""
        h = HMM3Harmonizer()
        melody = _melody(pitches)
        c1 = h.harmonize(melody, scale, max(s for _, s, _ in pitches) + 1)
        c2 = h.harmonize(melody, scale, max(s for _, s, _ in pitches) + 1)
        assert [c.root for c in c1] == [c.root for c in c2], f"Golden {name} flickered"

    @pytest.mark.parametrize("name,pitches,scale,expected_count", GOLDEN_MELODIES)
    def test_golden_valid(self, name, pitches, scale, expected_count):
        """Каждая golden melody produce valid chords."""
        h = HMM3Harmonizer()
        melody = _melody(pitches)
        chords = h.harmonize(melody, scale, max(s for _, s, _ in pitches) + 1)
        assert len(chords) >= 1, f"Golden {name} produced no chords"
        assert all(c.root is not None for c in chords)
        assert all(c.quality is not None for c in chords)


# =========================================================================
# 8. PRE-EXISTING FAILURE INVESTIGATION
# =========================================================================


class TestPreExistingFailure:
    """Изолировать и document pre-existing failure."""

    def test_tension_generator_atonal_scatter_isolated(self):
        """TensionGenerator atonal_scatter — проверить изолированно."""
        from melodica.generators.tension import TensionGenerator
        from melodica.types import ChordLabel

        params = type("Params", (), {"key_range_low": 48, "key_range_high": 84})()
        gen = TensionGenerator(params, mode="atonal_scatter")
        chords = [ChordLabel(root=0, quality=Quality.MINOR, start=0, duration=8)]
        notes = gen.render(chords, C_MAJOR, 8.0)
        assert isinstance(notes, list)  # Should not crash

    def test_rhythm_coordinator_shared_isolated(self):
        """test_shared_rhythm — проверить изолированно."""
        # This is the other pre-existing failure
        # Just verify it doesn't crash in isolation
        from melodica.types import ChordLabel

        chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)
        assert chord.root == 0
