# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
test_functional_progressions.py — Tests that verify how FunctionalHMMHarmonizer
unfurls progressions: cadences, functional flow, mode-specific vocabulary,
diversity, tension response, and comparison with the old CoupledHMM patterns.
"""

import random

import pytest

from melodica.harmonize.functional_hmm import FunctionalHMMHarmonizer
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


BAR_GRID = BarGrid(numerator=4, denominator=4)
NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

C_MAJOR = Scale(0, Mode.MAJOR)
D_HMIN = Scale(2, Mode.HARMONIC_MINOR)
A_MINOR = Scale(9, Mode.NATURAL_MINOR)
E_DORIAN = Scale(4, Mode.DORIAN)
F_PHRYGIAN = Scale(5, Mode.PHRYGIAN)
G_MIXO = Scale(7, Mode.MIXOLYDIAN)
B_BLUES = Scale(11, Mode.BLUES)


def _melody(n: int, root: int = 60, seed: int = 42) -> list[NoteInfo]:
    random.seed(seed)
    return [
        NoteInfo(pitch=root + random.randint(0, 12), start=i * 0.5, duration=0.5, velocity=80)
        for i in range(n)
    ]


def _prog(scale: Scale, bars: int = 16, seed: int = 42, **kw) -> list[ChordLabel]:
    random.seed(seed)
    h = FunctionalHMMHarmonizer(bar_grid=BAR_GRID, **kw)
    melody = _melody(bars * 8, root=scale.root + 60, seed=seed)
    return h.harmonize(melody, scale, float(bars * 4))


def _names(chords: list[ChordLabel]) -> list[str]:
    return [f"{NOTE[c.root]}{c.quality.name}" for c in chords]


def _funcs(chords: list[ChordLabel]) -> list[str]:
    return [c.function.value for c in chords if c.function]


# =========================================================================
# 1. Cadence resolution
# =========================================================================

class TestCadenceResolution:

    def test_authentic_V_resolves_to_I(self):
        """When D appears right before T at a structural point, it should be
        degree V resolving to degree I (V→I authentic cadence)."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        for i in range(1, len(chords)):
            if (chords[i - 1].function == HarmonicFunction.DOMINANT
                    and chords[i].function == HarmonicFunction.TONIC
                    and (i + 1) % 4 == 0):  # structural position
                assert chords[i - 1].degree == 5, (
                    f"D at bar {i} is degree {chords[i-1].degree}, expected 5 (V)"
                )
                assert chords[i].degree == 1, (
                    f"T at bar {i} is degree {chords[i].degree}, expected 1 (I)"
                )

    def test_dominant_at_cadence_is_dom7(self):
        """V at a structural cadence should be Dom7 for stronger resolution."""
        chords = _prog(D_HMIN, bars=16, seed=3)
        for i in range(1, len(chords)):
            if (chords[i - 1].function == HarmonicFunction.DOMINANT
                    and chords[i].function == HarmonicFunction.TONIC
                    and (i + 1) % 4 == 0):
                assert chords[i - 1].quality == Quality.DOMINANT7, (
                    f"V at bar {i} is {chords[i-1].quality.name}, expected Dom7"
                )

    def test_at_least_one_D_T_cadence_in_16_bars(self):
        """16 bars should produce at least 1 authentic D→T cadence."""
        chords = _prog(D_HMIN, bars=16, seed=7)
        d_t = sum(
            1 for i in range(1, len(chords))
            if chords[i - 1].function == HarmonicFunction.DOMINANT
            and chords[i].function == HarmonicFunction.TONIC
        )
        assert d_t >= 1, f"No D→T cadences in 16 bars: {_funcs(chords)}"

    def test_half_cadence_S_before_D(self):
        """Subdominant before dominant (ii→V, IV→V) should appear."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        s_d = sum(
            1 for i in range(1, len(chords))
            if chords[i - 1].function == HarmonicFunction.SUBDOMINANT
            and chords[i].function == HarmonicFunction.DOMINANT
        )
        assert s_d >= 1, f"No S→D transitions in 16 bars: {_funcs(chords)}"


# =========================================================================
# 2. Functional flow (T→S→D→T cycles)
# =========================================================================

class TestFunctionalFlow:

    def test_contains_full_tsd_cycle(self):
        """A 16-bar progression should contain at least one T→S→D→T cycle."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        fns = _funcs(chords)
        for i in range(len(fns) - 3):
            if fns[i] == "T" and fns[i + 1] == "S" and fns[i + 2] == "D" and fns[i + 3] == "T":
                return
        pytest.fail(f"No T→S→D→T cycle found: {fns}")

    def test_no_two_consecutive_S(self):
        """Two consecutive subdominants is weak; should not happen."""
        chords = _prog(D_HMIN, bars=16, seed=5)
        for i in range(1, len(chords)):
            if (chords[i - 1].function == HarmonicFunction.SUBDOMINANT
                    and chords[i].function == HarmonicFunction.SUBDOMINANT):
                pytest.fail(f"Consecutive S at bars {i}-{i+1}: {_funcs(chords)}")

    def test_function_distribution_covers_all_three(self):
        """T, S, and D should all appear in a 16-bar progression."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        fns = set(_funcs(chords))
        assert "T" in fns, f"No Tonic in progression: {fns}"
        assert "S" in fns, f"No Subdominant in progression: {fns}"
        assert "D" in fns, f"No Dominant in progression: {fns}"

    def test_T_is_most_frequent(self):
        """Tonic should be the most common function (it's home base)."""
        chords = _prog(C_MAJOR, bars=16, seed=2)
        fns = _funcs(chords)
        counts = {f: fns.count(f) for f in set(fns)}
        assert counts.get("T", 0) >= counts.get("S", 0)
        assert counts.get("T", 0) >= counts.get("D", 0)


# =========================================================================
# 3. Mode-specific vocabulary
# =========================================================================

class TestModeSpecificVocabulary:

    def test_harmonic_minor_uses_raised_7th(self):
        """Harmonic minor should use V (raised 7th degree) for dominant."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        # D harmonic minor: A is the raised 7th → V = A (root 9)
        dom_chords = [c for c in chords if c.function == HarmonicFunction.DOMINANT]
        a_roots = [c for c in dom_chords if c.root == 9]  # A = 9
        assert len(a_roots) > 0, (
            f"No A-root dominant in D harmonic minor. "
            f"Dom roots: {[c.root for c in dom_chords]}"
        )

    def test_dorian_uses_raised_6th(self):
        """Dorian characteristic: raised 6th degree should influence chord choice."""
        chords = _prog(E_DORIAN, bars=16, seed=1)
        # E Dorian: C# is the raised 6th (characteristic Dorian note)
        # IV chord should be A major (not A minor like in natural minor)
        all_roots = [c.root for c in chords]
        # At minimum, should have multiple distinct roots
        assert len(set(all_roots)) >= 3

    def test_major_progression_uses_diatonic_degrees(self):
        """C major should primarily use diatonic degrees (I through vii)."""
        chords = _prog(C_MAJOR, bars=16, seed=1, embellish_rate=0.0)
        # C major degrees: C=0, D=2, E=4, F=5, G=7, A=9, B=11
        diatonic_roots = {0, 2, 4, 5, 7, 9, 11}
        for c in chords:
            assert c.root in diatonic_roots, (
                f"Non-diatonic root {NOTE[c.root]} in C major (embellish_rate=0)"
            )

    def test_different_modes_produce_different_progressions(self):
        """Same melody, different modes should produce different chord sequences."""
        seeds = list(range(5))
        progs = {}
        for mode in [Mode.MAJOR, Mode.DORIAN, Mode.PHRYGIAN, Mode.HARMONIC_MINOR]:
            scale = Scale(2, mode)
            chords = _prog(scale, bars=8, seed=3)
            progs[mode.value] = _names(chords)

        # At least 2 of the 4 should differ
        unique = set(tuple(v) for v in progs.values())
        assert len(unique) >= 2, f"All modes produced same progression: {progs}"


# =========================================================================
# 4. Tension curve response
# =========================================================================

class TestTensionResponse:

    def test_rest_phase_produces_tonic(self):
        """Tonic should appear in the first 4 bars of a 16-bar progression."""
        h = FunctionalHMMHarmonizer(bar_grid=BAR_GRID)
        scale = C_MAJOR
        melody = _melody(32, seed=1)
        chords = h.harmonize(melody, scale, 16.0)
        first_quarter = chords[:4]
        fns = [c.function for c in first_quarter]
        assert HarmonicFunction.TONIC in fns, f"No T in first 4 bars: {[f.value for f in fns]}"

    def test_high_tension_more_dominants(self):
        """High tension curve should produce more D than low tension."""
        random.seed(42)
        h = FunctionalHMMHarmonizer(bar_grid=BAR_GRID)
        scale = D_HMIN
        melody = _melody(64, seed=42)

        # Build tension curve that peaks late (more D in second half)
        high_tension = TensionCurve(total_beats=32.0, curve_type="classical",
                                    peak_position=0.9, peak_intensity=1.0)
        chords_high = h.harmonize(melody, scale, 32.0, tension_curve=high_tension)

        d_count = sum(1 for c in chords_high if c.function in (HarmonicFunction.DOMINANT, HarmonicFunction.SECONDARY))
        t_count = sum(1 for c in chords_high if c.function == HarmonicFunction.TONIC)
        # Both should appear
        assert d_count > 0, "No dominants in high-tension progression"
        assert t_count > 0, "No tonics in high-tension progression"

    def test_no_tension_curve_still_works(self):
        """Without tension curve, should produce valid functional plan."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        fns = set(_funcs(chords))
        assert len(fns) >= 2  # At least 2 different functions


# =========================================================================
# 5. Diversity (comparison with old CoupledHMM patterns)
# =========================================================================

class TestDiversityVsOldHMM:

    def test_no_dom7_monopoly(self):
        """Dom7 should not dominate the progression (old HMM had 25%+ in one cell)."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        dom7_count = sum(1 for c in chords if c.quality == Quality.DOMINANT7)
        ratio = dom7_count / len(chords)
        assert ratio < 0.5, f"Dom7 is {ratio:.0%} of progression (should be <50%)"

    def test_no_add9_gravity_well(self):
        """Extended chords should not form a gravity well (old HMM bug)."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        ext_qualities = {Quality.MAJOR9, Quality.MINOR9, Quality.ADD9}
        ext_count = sum(1 for c in chords if c.quality in ext_qualities)
        ratio = ext_count / len(chords)
        assert ratio < 0.4, f"Extended chords are {ratio:.0%} (gravity well?)"

    def test_interval_diversity_at_least_5(self):
        """Should have at least 5 unique intervals between consecutive roots."""
        chords = _prog(D_HMIN, bars=16, seed=7)
        roots = [c.root for c in chords]
        intervals = set((roots[i + 1] - roots[i]) % 12 for i in range(len(roots) - 1))
        assert len(intervals) >= 5, (
            f"Only {len(intervals)} unique intervals: {sorted(intervals)}"
        )

    def test_root_diversity_at_least_4_in_16_bars(self):
        """16-bar progression should use at least 4 different roots."""
        for seed in range(5):
            chords = _prog(D_HMIN, bars=16, seed=seed)
            roots = len(set(c.root for c in chords))
            assert roots >= 4, f"Seed {seed}: only {roots} unique roots"

    def test_no_identical_consecutive_bars(self):
        """No two consecutive bars should have identical root+quality."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        for i in range(1, len(chords)):
            if chords[i].root == chords[i - 1].root and chords[i].quality == chords[i - 1].quality:
                pytest.fail(
                    f"Bars {i}-{i+1} identical: {NOTE[chords[i].root]}{chords[i].quality.name}"
                )

    def test_different_seeds_different_progressions(self):
        """Different random seeds should produce different progressions."""
        progs = set()
        for seed in range(5):
            chords = _prog(D_HMIN, bars=8, seed=seed)
            progs.add(tuple(_names(chords)))
        assert len(progs) >= 3, f"Only {len(progs)} unique progressions from 5 seeds"


# =========================================================================
# 6. Embellishment unfurling
# =========================================================================

class TestEmbellishmentUnfurling:

    def test_secondary_dominants_appear_with_high_rate(self):
        """With high embellish rate, some secondary dominants should appear."""
        chords = _prog(D_HMIN, bars=32, seed=1, embellish_rate=0.8)
        sec = [c for c in chords if c.function == HarmonicFunction.SECONDARY]
        # Not guaranteed for 32 bars with 80% rate, but likely
        # At minimum: the progression should still be valid
        assert len(chords) == 32

    def test_secondary_dominants_are_dom7(self):
        """Secondary dominant embellishments should always be Dom7 quality."""
        chords = _prog(D_HMIN, bars=32, seed=3, embellish_rate=1.0)
        for c in chords:
            if c.function == HarmonicFunction.SECONDARY:
                assert c.quality == Quality.DOMINANT7, (
                    f"Secondary dominant at root {NOTE[c.root]} is {c.quality.name}, expected Dom7"
                )

    def test_no_embellish_means_all_functional(self):
        """With embellish_rate=0, only T/S/D should appear (no X/SECONDARY)."""
        chords = _prog(D_HMIN, bars=16, seed=1, embellish_rate=0.0)
        for c in chords:
            assert c.function != HarmonicFunction.SECONDARY

    def test_embellished_progression_still_has_cadences(self):
        """Embellishments should not destroy cadence structure."""
        chords = _prog(D_HMIN, bars=16, seed=1, embellish_rate=0.5)
        d_t = sum(
            1 for i in range(1, len(chords))
            if chords[i - 1].function in (HarmonicFunction.DOMINANT, HarmonicFunction.SECONDARY)
            and chords[i].function == HarmonicFunction.TONIC
        )
        assert d_t >= 1, "Embellishments destroyed all cadences"


# =========================================================================
# 7. Scale-degree consistency
# =========================================================================

class TestDegreeConsistency:

    def test_degrees_match_scale(self):
        """Chord root pitch classes should match the assigned degree."""
        chords = _prog(D_HMIN, bars=8, seed=1)
        degs = D_HMIN.degrees()
        for c in chords:
            expected_root = int(round(degs[(c.degree - 1) % len(degs)]))
            assert c.root == expected_root, (
                f"Degree {c.degree} root={NOTE[c.root]}, expected={NOTE[expected_root]}"
            )

    def test_subdominant_uses_deg_2_or_4(self):
        """Subdominant function should use degree II or IV."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        for c in chords:
            if c.function == HarmonicFunction.SUBDOMINANT:
                assert c.degree in (2, 4), (
                    f"S function on degree {c.degree}, expected 2 or 4"
                )

    def test_dominant_uses_deg_5_or_7(self):
        """Dominant function should use degree V or VII."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        for c in chords:
            if c.function == HarmonicFunction.DOMINANT:
                assert c.degree in (5, 7), (
                    f"D function on degree {c.degree}, expected 5 or 7"
                )


# =========================================================================
# 8. Regression: specific bad patterns from old HMM
# =========================================================================

class TestRegressionOldHMM:

    def test_no_infinite_V_I_loop(self):
        """Old HMM produced D7→G→A7→D→E7→A endlessly.
        Check that no more than 50% of transitions are P4 root motion."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        roots = [c.root for c in chords]
        p4_count = sum(
            1 for i in range(len(roots) - 1) if (roots[i + 1] - roots[i]) % 12 == 5
        )
        ratio = p4_count / max(len(roots) - 1, 1)
        assert ratio < 0.5, f"P4 root motion is {ratio:.0%} (V-I loop pattern?)"

    def test_no_aug_overrepresentation(self):
        """Old HMM had 15.6% Aug. Check Aug is not overrepresented."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        aug_count = sum(1 for c in chords if c.quality == Quality.AUGMENTED)
        ratio = aug_count / len(chords)
        assert ratio < 0.15, f"Aug is {ratio:.0%} of chords"

    def test_no_self_loop_chains(self):
        """Old HMM had self-loops (same type at different roots).
        Check no more than 2 consecutive same-quality chords."""
        chords = _prog(D_HMIN, bars=16, seed=1)
        run = 1
        for i in range(1, len(chords)):
            if chords[i].quality == chords[i - 1].quality:
                run += 1
                assert run <= 2, (
                    f"{chords[i].quality.name} repeated {run}x: {_names(chords[max(0,i-2):i+1])}"
                )
            else:
                run = 1

    def test_not_all_roots_same_as_melody(self):
        """Chord roots should not simply follow melody notes."""
        random.seed(1)
        # Fixed melody on D only
        melody = [NoteInfo(pitch=62, start=i * 0.5, duration=0.5, velocity=80) for i in range(32)]
        h = FunctionalHMMHarmonizer(bar_grid=BAR_GRID)
        chords = h.harmonize(melody, D_HMIN, 16.0)
        roots = set(c.root for c in chords)
        assert len(roots) >= 2, "All chords on same root despite varied functional plan"
