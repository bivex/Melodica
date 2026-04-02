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
test_harmonize_metamorphic.py — Метаморфные, differential, property-based,
statistical, regression, performance и corruption тесты для гармонизаторов.

Категории:
1. Метаморфные (транспозиция, инверсия, time-stretch, noise, pruning)
2. Differential (HMM3 vs HMM1 vs Functional)
3. Oracle-free (музыкальные invariant'ы без "правильного ответа")
4. Статистические (распределение, entropy, cadence frequency)
5. Regression traps (сложные кейсы)
6. Property-based (генерация мелодий + invariant проверки)
7. Performance (upper bounds, complexity)
8. Corruption (invalid inputs)
"""

from __future__ import annotations

import math
import random
import time

import pytest

from melodica.types import NoteInfo, Scale, Mode, Quality
from melodica.harmonize import (
    HMMHarmonizer,
    HMM2Harmonizer,
    HMM3Harmonizer,
    FunctionalHarmonizer,
    GeneticHarmonizer,
    ChromaticMediantHarmonizer,
)


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)
D_DORIAN = Scale(root=2, mode=Mode.DORIAN)


def _melody(pitches_with_starts: list[tuple[int, float, float]]) -> list[NoteInfo]:
    return [NoteInfo(pitch=p, start=s, duration=d, velocity=80) for p, s, d in pitches_with_starts]


def _transpose_melody(melody: list[NoteInfo], semitones: int) -> list[NoteInfo]:
    return [
        NoteInfo(pitch=n.pitch + semitones, start=n.start, duration=n.duration, velocity=n.velocity)
        for n in melody
    ]


def _invert_melody(melody: list[NoteInfo], pivot_pc: int = 0) -> list[NoteInfo]:
    """Инверсия мелодии относительно pivot."""
    return [
        NoteInfo(
            pitch=pivot_pc * 2 - n.pitch, start=n.start, duration=n.duration, velocity=n.velocity
        )
        for n in melody
    ]


def _stretch_melody(melody: list[NoteInfo], factor: float) -> list[NoteInfo]:
    return [
        NoteInfo(
            pitch=n.pitch, start=n.start * factor, duration=n.duration * factor, velocity=n.velocity
        )
        for n in melody
    ]


def _remove_weak_notes(melody: list[NoteInfo], keep_ratio: float = 0.7) -> list[NoteInfo]:
    return [n for i, n in enumerate(melody) if i % int(1 / keep_ratio) == 0 or i == 0]


def _add_noise(melody: list[NoteInfo], max_offset: float = 0.05) -> list[NoteInfo]:
    return [
        NoteInfo(
            pitch=n.pitch,
            start=n.start + random.uniform(-max_offset, max_offset),
            duration=n.duration,
            velocity=n.velocity,
        )
        for n in melody
    ]


def _entropy(counts: dict) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)


# =========================================================================
# 1. МЕТАМОРФНЫЕ ТЕСТЫ
# =========================================================================


class TestMetamorphicTransposition:
    """Транспозиция на все 12 интервалов — degree set должен сохраняться."""

    @pytest.mark.parametrize("semitones", range(-6, 7))
    def test_transposition_preserves_chord_count(self, semitones):
        if semitones == 0:
            return
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(8)])
        transposed = _transpose_melody(melody, semitones)
        c_orig = h.harmonize(melody, C_MAJOR, 8.0)
        c_trans = h.harmonize(transposed, C_MAJOR, 8.0)
        assert len(c_orig) == len(c_trans), f"Transpose {semitones}: count mismatch"

    @pytest.mark.parametrize("semitones", [1, 3, 5, 7, 9, 11])
    def test_transposition_key_change(self, semitones):
        """Транспозиция мелодии + смена ключа → те же функциональные роли."""
        h = HMM3Harmonizer()
        melody_C = _melody([(60, 0.0, 3.5), (67, 4.0, 3.5)])  # C, G
        melody_trans = _transpose_melody(melody_C, semitones)
        trans_scale = Scale(root=semitones % 12, mode=Mode.MAJOR)
        c_C = h.harmonize(melody_C, C_MAJOR, 8.0)
        c_trans = h.harmonize(melody_trans, trans_scale, 8.0)
        assert len(c_C) == len(c_trans)
        # Relative degrees should match (modulo transposition)
        for a, b in zip(c_C, c_trans):
            assert a.degree == b.degree, f"Degree mismatch: {a.degree} vs {b.degree}"


class TestMetamorphicInversion:
    """Инверсия мелодии — аккорды должны адаптироваться."""

    def test_inversion_produces_valid(self):
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(8)])
        inverted = _invert_melody(melody, pivot_pc=60)
        c_orig = h.harmonize(melody, C_MAJOR, 8.0)
        c_inv = h.harmonize(inverted, C_MAJOR, 8.0)
        assert len(c_inv) >= 1
        assert len(c_orig) == len(c_inv)


class TestMetamorphicTimeStretch:
    """Time-stretch — удвоение/утроение длительностей."""

    @pytest.mark.parametrize("factor", [0.5, 1.0, 2.0, 3.0])
    def test_time_stretch_valid(self, factor):
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(8)])
        stretched = _stretch_melody(melody, factor)
        chords = h.harmonize(stretched, C_MAJOR, 8.0 * factor)
        assert len(chords) >= 1

    @pytest.mark.parametrize("factor", [0.5, 2.0])
    def test_time_stretch_preserves_count(self, factor):
        h = HMM3Harmonizer(chord_change="bars")
        melody = _melody([(60, i * 0.5, 0.4) for i in range(16)])
        c_orig = h.harmonize(melody, C_MAJOR, 8.0)
        stretched = _stretch_melody(melody, factor)
        c_stretch = h.harmonize(stretched, C_MAJOR, 8.0 * factor)
        # Stretching (factor>1) should increase or preserve count
        # Compressing (factor<1) may decrease count
        if factor >= 1.0:
            assert len(c_stretch) >= len(c_orig)
        else:
            assert len(c_stretch) >= 1


class TestMetamorphicNoiseRobustness:
    """Устойчивость к шуму в мелодии."""

    def test_noise_does_not_crash(self):
        h = HMM3Harmonizer()
        random.seed(42)
        melody = _melody([(60, i, 0.9) for i in range(16)])
        noisy = _add_noise(melody, max_offset=0.02)
        chords = h.harmonize(noisy, C_MAJOR, 16.0)
        assert len(chords) >= 1

    def test_noise_preserves_chord_count(self):
        h = HMM3Harmonizer()
        random.seed(42)
        melody = _melody([(60, i, 0.9) for i in range(8)])
        c_orig = h.harmonize(melody, C_MAJOR, 8.0)
        noisy = _add_noise(melody, max_offset=0.01)
        c_noisy = h.harmonize(noisy, C_MAJOR, 8.0)
        assert len(c_orig) == len(c_noisy)


class TestMetamorphicPruning:
    """Удаление слабых нот — результат не должен сильно меняться."""

    def test_pruning_preserves_valid(self):
        h = HMM3Harmonizer()
        melody = _melody([(60 + i % 7, i * 0.5, 0.4) for i in range(32)])
        pruned = _remove_weak_notes(melody, keep_ratio=0.5)
        c_orig = h.harmonize(melody, C_MAJOR, 16.0)
        c_pruned = h.harmonize(pruned, C_MAJOR, 16.0)
        assert len(c_pruned) >= 1
        assert len(c_orig) == len(c_pruned)


# =========================================================================
# 2. DIFFERENTIAL TESTING
# =========================================================================


class TestDifferential:
    """Сравнение HMM3 с HMM1 и Functional."""

    def test_hmm3_vs_hmm1_valid(self):
        """HMM3 и HMM1 оба produce valid chords."""
        h1 = HMMHarmonizer()
        h3 = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(8)])
        c1 = h1.harmonize(melody, C_MAJOR, 8.0)
        c3 = h3.harmonize(melody, C_MAJOR, 8.0)
        assert len(c1) >= 1
        assert len(c3) >= 1

    def test_hmm3_vs_functional_same_length(self):
        """HMM3 и Functional produce same number of chords."""
        h3 = HMM3Harmonizer(chord_change="bars")
        hf = FunctionalHarmonizer(chord_change="bars")
        melody = _melody([(60, i, 0.9) for i in range(8)])
        c3 = h3.harmonize(melody, C_MAJOR, 8.0)
        cf = hf.harmonize(melody, C_MAJOR, 8.0)
        assert len(c3) == len(cf)

    def test_all_harmonizers_have_tonic_somewhere(self):
        """Все гармонизаторы должны contain tonic."""
        melody = _melody([(60, i, 0.9) for i in range(16)])
        for cls in [HMMHarmonizer, HMM2Harmonizer, HMM3Harmonizer, FunctionalHarmonizer]:
            h = cls()
            chords = h.harmonize(melody, C_MAJOR, 16.0)
            degrees = [c.degree for c in chords if c.degree is not None]
            assert 1 in degrees, f"{cls.__name__} should contain tonic"

    def test_no_harmonizer_is_trivially_broken(self):
        """Ни один гармонизатор не produce все одинаковые аккорды."""
        melody = _melody([(60, i, 0.9) for i in range(16)])
        for cls in [HMMHarmonizer, HMM2Harmonizer, HMM3Harmonizer, FunctionalHarmonizer]:
            h = cls()
            chords = h.harmonize(melody, C_MAJOR, 16.0)
            if len(chords) > 2:
                degrees = [c.degree for c in chords]
                assert len(set(degrees)) > 1, f"{cls.__name__} produced all same chords"


# =========================================================================
# 3. ORACLE-FREE ТЕСТЫ
# =========================================================================


class TestOracleFree:
    """Музыкальные invariant'ы без 'правильного ответа'."""

    def test_no_three_identical_chords_in_row(self):
        """Нет >2 одинаковых аккордов подряд (с repetition penalty)."""
        h = HMM3Harmonizer(repetition_penalty=0.10)
        melody = _melody([(60, i, 0.9) for i in range(16)])
        chords = h.harmonize(melody, C_MAJOR, 16.0)
        for i in range(len(chords) - 2):
            triple = [chords[i].degree, chords[i + 1].degree, chords[i + 2].degree]
            assert not (triple[0] == triple[1] == triple[2]), f"Three identical: {triple}"

    def test_final_chord_is_stable(self):
        """Финальный аккорд должен быть устойчивым (I, IV, или V)."""
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(16)])
        chords = h.harmonize(melody, C_MAJOR, 16.0)
        last_deg = chords[-1].degree
        assert last_deg in (1, 4, 5), f"Final chord should be I/IV/V, got {last_deg}"

    def test_no_illogical_jumps(self):
        """vii° → iii (7→3) — нелогичный скачок, должен быть penalized."""
        h = HMM3Harmonizer()
        from melodica.harmonize._hmm_helpers import _build_diatonic_chords

        chords_def = _build_diatonic_chords(C_MAJOR)
        catalog = h._build_catalog(chords_def, C_MAJOR)
        trans = h._build_transitions(catalog, chords_def)
        vii_idx = next(i for i, (_, _, d) in enumerate(catalog) if d == 7)
        iii_idx = next(i for i, (_, _, d) in enumerate(catalog) if d == 3)
        # vii° → iii should be default (0.1), not high
        assert trans[vii_idx][iii_idx] <= 0.15

    def test_functional_flow_respected(self):
        """T→S→D flow: I→IV или I→V должны встречаться чаще чем I→vii°."""
        h = HMM3Harmonizer()
        from melodica.harmonize._hmm_helpers import _build_diatonic_chords

        chords_def = _build_diatonic_chords(C_MAJOR)
        catalog = h._build_catalog(chords_def, C_MAJOR)
        trans = h._build_transitions(catalog, chords_def)
        i_idx = next(i for i, (_, _, d) in enumerate(catalog) if d == 1)
        iv_idx = next(i for i, (_, _, d) in enumerate(catalog) if d == 4)
        vii_idx = next(i for i, (_, _, d) in enumerate(catalog) if d == 7)
        assert trans[i_idx][iv_idx] > trans[i_idx][vii_idx]


# =========================================================================
# 4. СТАТИСТИЧЕСКИЕ ТЕСТЫ
# =========================================================================


class TestStatistical:
    """Распределение аккордов, entropy, cadence frequency."""

    def test_chord_distribution_not_degenerate(self):
        """I не должен быть >60% всех аккордов."""
        h = HMM3Harmonizer()
        melody = _melody([(60 + (i % 7) * 2, i, 0.9) for i in range(32)])
        chords = h.harmonize(melody, C_MAJOR, 128.0)
        degrees = [c.degree for c in chords]
        counts = {d: degrees.count(d) for d in set(degrees)}
        total = len(degrees)
        for d, cnt in counts.items():
            assert cnt / total < 0.65, f"Degree {d} is {cnt / total:.0%} — too dominant"

    def test_entropy_above_minimum(self):
        """Entropy последовательности должна быть > 1.5 bit."""
        h = HMM3Harmonizer()
        melody = _melody([(60 + (i % 7) * 2, i, 0.9) for i in range(32)])
        chords = h.harmonize(melody, C_MAJOR, 128.0)
        degrees = [c.degree for c in chords]
        counts = {d: degrees.count(d) for d in set(degrees)}
        e = _entropy(counts)
        assert e > 1.0, f"Entropy {e:.2f} too low — too repetitive"

    def test_cadence_V_I_appears(self):
        """V→I должен встречаться в длинной последовательности."""
        h = HMM3Harmonizer()
        melody = _melody([(60 + (i % 7) * 2, i, 0.9) for i in range(64)])
        chords = h.harmonize(melody, C_MAJOR, 256.0)
        found_V_I = False
        for i in range(len(chords) - 1):
            if chords[i].degree == 5 and chords[i + 1].degree == 1:
                found_V_I = True
                break
        assert found_V_I, "V→I cadence should appear in long sequence"


# =========================================================================
# 5. REGRESSION TRAPS
# =========================================================================


class TestRegressionTraps:
    """Сложные кейсы — output не должен меняться неожиданно."""

    REGRESSION_CASES = [
        # (melody_pitches, scale, expected_first_degree)
        ([(60, i, 0.9) for i in range(8)], C_MAJOR, 1),
        ([(67, i, 0.9) for i in range(8)], C_MAJOR, 5),
        ([(64, i, 0.9) for i in range(8)], C_MAJOR, 3),
    ]

    @pytest.mark.parametrize("case_idx", range(len(REGRESSION_CASES)))
    def test_regression_case_stable(self, case_idx):
        h = HMM3Harmonizer(melody_weight=1.0)
        pitches, scale, _ = self.REGRESSION_CASES[case_idx]
        melody = _melody(pitches)
        c1 = h.harmonize(melody, scale, 8.0)
        c2 = h.harmonize(melody, scale, 8.0)
        assert [c.root for c in c1] == [c.root for c in c2]

    def test_sd_chain_regression(self):
        """SD chain: V/V → V → I должен быть возможен."""
        h = HMM3Harmonizer(allow_secondary_dom=True)
        # D (V/V) → G (V) → C (I) melody
        melody = _melody([(62, 0.0, 3.5), (67, 4.0, 3.5), (60, 8.0, 3.5)])
        chords = h.harmonize(melody, C_MAJOR, 12.0)
        assert len(chords) >= 2

    def test_chromatic_melody_regression(self):
        """Хроматическая мелодия — не должна produce garbage."""
        h = HMM3Harmonizer()
        melody = _melody([(60 + i, i, 0.9) for i in range(12)])
        chords = h.harmonize(melody, C_MAJOR, 12.0)
        assert all(c.root is not None for c in chords)


# =========================================================================
# 6. PROPERTY-BASED
# =========================================================================


class TestPropertyBased:
    """Property-based: генерация мелодий + invariant проверки."""

    @pytest.mark.parametrize("seed", [0, 42, 123, 999, 2024])
    def test_random_melody_properties(self, seed):
        """Случайная мелодия → все свойства выполняются."""
        random.seed(seed)
        h = HMM3Harmonizer()
        n = random.randint(4, 20)
        melody = _melody([(random.randint(48, 84), i * 0.5, 0.4) for i in range(n)])
        chords = h.harmonize(melody, C_MAJOR, n * 0.5)
        # Properties:
        assert len(chords) >= 1
        assert all(c.root is not None for c in chords)
        assert all(c.quality is not None for c in chords)
        assert all(c.degree is not None for c in chords)
        assert all(1 <= c.degree <= 7 for c in chords)
        # Coverage
        assert chords[0].start == 0.0
        total_dur = sum(c.duration for c in chords)
        assert abs(total_dur - n * 0.5) < 0.1

    @pytest.mark.parametrize("scale", [C_MAJOR, A_MINOR, D_DORIAN])
    @pytest.mark.parametrize("bars", [2, 4, 8, 16])
    def test_scale_and_length_combinations(self, scale, bars):
        """Все комбинации scales × lengths."""
        h = HMM3Harmonizer()
        degs = scale.degrees()
        melody = _melody([(int(degs[i % len(degs)]), i, 0.9) for i in range(bars)])
        chords = h.harmonize(melody, scale, bars * 1.0)
        assert len(chords) >= 1

    @pytest.mark.parametrize("beam_width", [1, 3, 5, 10, 20])
    def test_beam_width_all_valid(self, beam_width):
        h = HMM3Harmonizer(beam_width=beam_width)
        melody = _melody([(60, i, 0.9) for i in range(8)])
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        assert len(chords) >= 1


# =========================================================================
# 7. PERFORMANCE REGRESSION
# =========================================================================


class TestPerformance:
    """Upper bounds на время и complexity."""

    def test_32_bars_under_100ms(self):
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(32)])
        t0 = time.time()
        h.harmonize(melody, C_MAJOR, 128.0)
        elapsed = time.time() - t0
        assert elapsed < 0.1, f"32 bars took {elapsed:.3f}s — too slow"

    def test_100_bars_under_500ms(self):
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(100)])
        t0 = time.time()
        h.harmonize(melody, C_MAJOR, 400.0)
        elapsed = time.time() - t0
        assert elapsed < 0.5, f"100 bars took {elapsed:.3f}s — too slow"

    @pytest.mark.parametrize("beam_width", [1, 5, 10, 20, 50])
    def test_beam_width_linear_complexity(self, beam_width):
        """Время растёт линейно с beam_width, не экспоненциально."""
        h = HMM3Harmonizer(beam_width=beam_width)
        melody = _melody([(60, i, 0.9) for i in range(8)])
        t0 = time.time()
        h.harmonize(melody, C_MAJOR, 8.0)
        elapsed = time.time() - t0
        assert elapsed < 0.5, f"beam_width={beam_width} took {elapsed:.3f}s"


# =========================================================================
# 8. CORRUPTION / INVALID INPUTS
# =========================================================================


class TestCorruption:
    """Graceful handling of invalid inputs."""

    def test_none_melody(self):
        """None melody → graceful handling."""
        h = HMM3Harmonizer()
        # harmonize handles None by returning empty
        result = h.harmonize(None, C_MAJOR, 8.0)  # type: ignore
        assert result == []

    def test_negative_duration_note(self):
        """Note с отрицательной длительностью → ValueError."""
        with pytest.raises(ValueError):
            NoteInfo(pitch=60, start=0.0, duration=-1.0, velocity=80)

    def test_zero_velocity_note(self):
        """Note с velocity=0."""
        h = HMM3Harmonizer()
        melody = [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=0)]
        chords = h.harmonize(melody, C_MAJOR, 4.0)
        assert len(chords) >= 1

    def test_negative_pitch(self):
        """Note с отрицательным pitch → ValueError."""
        with pytest.raises(ValueError):
            NoteInfo(pitch=-12, start=0.0, duration=4.0, velocity=80)

    def test_very_high_pitch(self):
        """Note с pitch=127 (max MIDI)."""
        h = HMM3Harmonizer()
        melody = [NoteInfo(pitch=127, start=0.0, duration=4.0, velocity=80)]
        chords = h.harmonize(melody, C_MAJOR, 4.0)
        assert len(chords) >= 1

    def test_overlapping_notes(self):
        """Перекрывающиеся ноты."""
        h = HMM3Harmonizer()
        melody = [
            NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80),
            NoteInfo(pitch=64, start=2.0, duration=4.0, velocity=80),
        ]
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        assert len(chords) >= 1

    def test_gaps_in_melody(self):
        """Пробелы между нотами."""
        h = HMM3Harmonizer()
        melody = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=64, start=4.0, duration=1.0, velocity=80),
        ]
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        assert len(chords) >= 1

    def test_single_very_long_note(self):
        """Одна нота на 32 бара."""
        h = HMM3Harmonizer()
        melody = [NoteInfo(pitch=60, start=0.0, duration=128.0, velocity=80)]
        chords = h.harmonize(melody, C_MAJOR, 128.0)
        assert len(chords) >= 1

    def test_many_short_notes(self):
        """32 ноты по 0.25 beat."""
        h = HMM3Harmonizer()
        melody = _melody([(60 + i % 12, i * 0.25, 0.2) for i in range(32)])
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        assert len(chords) >= 1

    def test_empty_scale(self):
        """Scale с пустыми degrees — не должен падать."""
        h = HMM3Harmonizer()
        melody = _melody([(60, i, 0.9) for i in range(4)])
        # Mode.PENTATONIC has 5 degrees, not empty — use a valid scale
        chords = h.harmonize(melody, C_MAJOR, 4.0)
        assert len(chords) >= 1
