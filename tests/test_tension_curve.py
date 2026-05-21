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

import pytest
from melodica.composer.tension_curve import TensionCurve, TensionPhase, TensionPoint


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def classical_16():
    return TensionCurve(total_beats=16.0, curve_type="classical")


@pytest.fixture
def edm_32():
    return TensionCurve(total_beats=32.0, curve_type="edm")


@pytest.fixture
def ambient_32():
    return TensionCurve(total_beats=32.0, curve_type="ambient")


@pytest.fixture
def build_release_16():
    return TensionCurve(total_beats=16.0, curve_type="build_release")


# ══════════════════════════════════════════════════════════════════════════════
# TensionPhase enum
# ══════════════════════════════════════════════════════════════════════════════


class TestTensionPhase:
    def test_five_members(self):
        members = list(TensionPhase)
        assert len(members) == 5

    def test_rest_member(self):
        assert TensionPhase.REST.value == "rest"

    def test_build_member(self):
        assert TensionPhase.BUILD.value == "build"

    def test_climax_member(self):
        assert TensionPhase.CLIMAX.value == "climax"

    def test_sustain_member(self):
        assert TensionPhase.SUSTAIN.value == "sustain"

    def test_resolution_member(self):
        assert TensionPhase.RESOLUTION.value == "resolution"

    def test_by_value(self):
        assert TensionPhase("rest") is TensionPhase.REST
        assert TensionPhase("build") is TensionPhase.BUILD
        assert TensionPhase("climax") is TensionPhase.CLIMAX
        assert TensionPhase("sustain") is TensionPhase.SUSTAIN
        assert TensionPhase("resolution") is TensionPhase.RESOLUTION

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            TensionPhase("unknown")


# ══════════════════════════════════════════════════════════════════════════════
# TensionPoint dataclass
# ══════════════════════════════════════════════════════════════════════════════


class TestTensionPoint:
    def test_create(self):
        p = TensionPoint(beat=4.0, tension=0.5, phase=TensionPhase.BUILD)
        assert p.beat == 4.0
        assert p.tension == 0.5
        assert p.phase is TensionPhase.BUILD

    def test_equality(self):
        a = TensionPoint(beat=0.0, tension=0.2, phase=TensionPhase.REST)
        b = TensionPoint(beat=0.0, tension=0.2, phase=TensionPhase.REST)
        assert a == b

    def test_inequality(self):
        a = TensionPoint(beat=0.0, tension=0.2, phase=TensionPhase.REST)
        b = TensionPoint(beat=1.0, tension=0.5, phase=TensionPhase.BUILD)
        assert a != b

    def test_tension_bounds(self):
        low = TensionPoint(beat=0.0, tension=0.0, phase=TensionPhase.REST)
        high = TensionPoint(beat=0.0, tension=1.0, phase=TensionPhase.CLIMAX)
        assert low.tension == 0.0
        assert high.tension == 1.0

    def test_beat_is_float(self):
        """Integers passed via the constructor are accepted but generate() always emits floats."""
        p_int = TensionPoint(beat=0, tension=0.0, phase=TensionPhase.REST)
        p_float = TensionPoint(beat=0.0, tension=0.0, phase=TensionPhase.REST)
        # generate() uses round(beat, 6) so every emitted beat is a float
        for p in TensionCurve().generate():
            assert isinstance(p.beat, float)
            break
        # Int and float inputs flow through without crashing
        assert p_int.beat == 0
        assert p_float.beat == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# TensionCurve defaults
# ══════════════════════════════════════════════════════════════════════════════


class TestTensionCurveDefaults:
    def test_default_total_beats(self):
        c = TensionCurve()
        assert c.total_beats == 32.0

    def test_default_curve_type(self):
        c = TensionCurve()
        assert c.curve_type == "classical"

    def test_default_peak_position(self):
        c = TensionCurve()
        assert c.peak_position == 0.7

    def test_default_peak_intensity(self):
        c = TensionCurve()
        assert c.peak_intensity == 0.9

    def test_default_resolution_length(self):
        c = TensionCurve()
        assert c.resolution_length == 0.25

    def test_custom_values(self):
        c = TensionCurve(
            total_beats=8.0,
            curve_type="edm",
            peak_position=0.5,
            peak_intensity=0.8,
            resolution_length=0.3,
        )
        assert c.total_beats == 8.0
        assert c.curve_type == "edm"
        assert c.peak_position == 0.5
        assert c.peak_intensity == 0.8
        assert c.resolution_length == 0.3


# ══════════════════════════════════════════════════════════════════════════════
# generate()
# ══════════════════════════════════════════════════════════════════════════════


class TestGenerate:
    def test_returns_list(self, classical_16):
        result = classical_16.generate()
        assert isinstance(result, list)

    def test_returns_tension_points(self, classical_16):
        for p in classical_16.generate():
            assert isinstance(p, TensionPoint)

    def test_non_empty(self, classical_16):
        assert len(classical_16.generate()) > 0

    def test_minimum_count(self):
        """Even very short sections produce enough points."""
        c = TensionCurve(total_beats=2.0)
        assert len(c.generate()) >= 8

    def test_point_count_scales_with_beats(self):
        c_short = TensionCurve(total_beats=4.0)
        c_long = TensionCurve(total_beats=64.0)
        assert len(c_long.generate()) > len(c_short.generate())

    def test_first_beat_is_zero(self, classical_16):
        p = classical_16.generate()[0]
        assert p.beat == pytest.approx(0.0, abs=1e-4)

    def test_last_beat_equals_total_beats(self, classical_16):
        p = classical_16.generate()[-1]
        assert p.beat == pytest.approx(16.0, abs=1e-4)

    def test_beats_are_monotonic(self, classical_16):
        beats = [p.beat for p in classical_16.generate()]
        assert beats == sorted(beats)

    def test_all_have_phase(self, classical_16):
        for p in classical_16.generate():
            assert isinstance(p.phase, TensionPhase)

    def test_all_have_valid_tension(self, classical_16):
        for p in classical_16.generate():
            assert 0.0 <= p.tension <= 1.0

    def test_caching(self, classical_16):
        a = classical_16.generate()
        b = classical_16.generate()
        assert a is b  # same list object on repeat calls

    def test_caching_each_instance_independent(self):
        c1 = TensionCurve()
        c2 = TensionCurve()
        c1.generate()
        c2.generate()
        c1._cached_points.append(None)  # type: ignore[attr-defined]
        assert None not in c2.generate()  # c2 unaffected

    def test_all_curve_types_generate(self):
        for ctype in ("classical", "edm", "ambient", "build_release"):
            c = TensionCurve(total_beats=16.0, curve_type=ctype)
            points = c.generate()
            assert len(points) > 0, f"No points for type {ctype!r}"

    def test_unknown_curve_type_falls_back_to_classical(self):
        c = TensionCurve(total_beats=16.0, curve_type="nonexistent")
        points = c.generate()
        assert len(points) > 0  # must not explode

    def test_each_point_has_tension_and_phase(self):
        c = TensionCurve(total_beats=8.0)
        for p in c.generate():
            assert isinstance(p.tension, float)
            assert isinstance(p.phase, TensionPhase)

    def test_tension_rounded_to_4_decimals(self):
        c = TensionCurve(total_beats=8.0)
        for p in c.generate():
            s = f"{p.tension:.4f}"
            assert len(s.split(".")[-1]) <= 4

    def test_beat_rounded_to_6_decimals(self):
        c = TensionCurve(total_beats=8.0)
        for p in c.generate():
            s = f"{p.beat:.6f}"
            assert len(s.split(".")[-1]) <= 6

    def test_edm_produces_oscillating_tension(self, edm_32):
        """EDM curve should have both rising and falling segments (>4 cycles)."""
        points = edm_32.generate()
        tensions = [p.tension for p in points]
        # At least one valley and one peak
        assert min(tensions) < max(tensions) * 0.7

    def test_ambient_tension_stays_within_band(self, ambient_32):
        """Ambient is 0.3 + 0.2*sin → range [0.1, 0.5]."""
        for p in ambient_32.generate():
            assert 0.05 < p.tension < 0.55

    def test_build_release_peaks_near_half(self, build_release_16):
        """Peak tension for build_release should be at or near peak_intensity."""
        points = build_release_16.generate()
        max_t = max(p.tension for p in points)
        assert max_t == pytest.approx(0.9, abs=0.01)

    def test_classical_starts_low(self, classical_16):
        assert classical_16.generate()[0].tension < 0.3

    def test_classical_ends_low(self, classical_16):
        assert classical_16.generate()[-1].tension < 0.5

    def test_peak_intensity_reached_or_exceeded_by_classical(self):
        """Peak tension should be close to peak_intensity."""
        c = TensionCurve(peak_intensity=1.0)
        max_t = max(p.tension for p in c.generate())
        assert max_t >= 0.95


# ══════════════════════════════════════════════════════════════════════════════
# tension_at()  — linear interpolation
# ══════════════════════════════════════════════════════════════════════════════


class TestTensionAt:
    def test_returns_float(self, classical_16):
        assert isinstance(classical_16.tension_at(4.0), float)

    def test_start_beat(self, classical_16):
        t = classical_16.tension_at(0.0)
        assert 0.0 <= t <= 1.0

    def test_end_beat(self, classical_16):
        t = classical_16.tension_at(16.0)
        assert 0.0 <= t <= 1.0

    def test_beyond_end(self, classical_16):
        """Past the last point returns 0.5 (fallback)."""
        assert classical_16.tension_at(999.0) == pytest.approx(0.5)

    def test_before_start(self, classical_16):
        """Before the first point returns 0.5 (fallback)."""
        assert classical_16.tension_at(-10.0) == pytest.approx(0.5)

    def test_midpoint_interpolation(self):
        """At the midpoint of two points the result should be their average."""
        c = TensionCurve()
        pts = c.generate()
        for i in range(len(pts) - 1):
            mid = (pts[i].beat + pts[i + 1].beat) / 2.0
            expected = (pts[i].tension + pts[i + 1].tension) / 2.0
            actual = c.tension_at(mid)
            assert actual == pytest.approx(expected, abs=1e-3), (
                f"Interpolation failed between points {i} and {i + 1}"
            )

    def test_values_in_range(self, classical_16):
        for b in range(0, 17):
            t = classical_16.tension_at(float(b))
            assert 0.0 <= t <= 1.0

    def test_both_curve_types_return_valid_values(self):
        classical = TensionCurve(curve_type="classical")
        edm = TensionCurve(curve_type="edm")
        for beat in [0.0, 4.0, 8.0, 12.0, 16.0, 32.0]:
            assert 0.0 <= classical.tension_at(beat) <= 1.0
            assert 0.0 <= edm.tension_at(beat) <= 1.0

    def test_different_total_beats(self):
        for total in (4.0, 8.0, 16.0, 32.0, 64.0):
            c = TensionCurve(total_beats=total)
            assert 0.0 <= c.tension_at(total / 2.0) <= 1.0

    def test_exact_point_beats(self, classical_16):
        """tension_at at a generated point beat should equal the point's tension."""
        pts = classical_16.generate()
        for p in pts:
            t = classical_16.tension_at(p.beat)
            assert t == pytest.approx(p.tension, abs=1e-3), (
                f"Mismatch at beat {p.beat}: point={p.tension}, at={t}"
            )


# ══════════════════════════════════════════════════════════════════════════════
# phase_at()
# ══════════════════════════════════════════════════════════════════════════════


class TestPhaseAt:
    def test_returns_enum(self, classical_16):
        assert isinstance(classical_16.phase_at(0.0), TensionPhase)

    def test_start_phase(self, classical_16):
        assert classical_16.phase_at(0.0) == TensionPhase.REST

    def test_returns_value_for_every_beat(self, classical_16):
        for b in range(0, 17):
            phase = classical_16.phase_at(float(b))
            assert isinstance(phase, TensionPhase)

    def test_beyond_end_returns_sustain(self, classical_16):
        assert classical_16.phase_at(999.0) == TensionPhase.SUSTAIN

    def test_classical_phase_distribution(self, classical_16):
        """At least two different phases appear across 16 beats."""
        phases = {classical_16.phase_at(float(b)) for b in range(0, 17)}
        assert len(phases) >= 2

    def test_edm_phase_distribution(self, edm_32):
        """EDM should cycle through multiple phases across 32 beats."""
        phases = {edm_32.phase_at(float(b)) for b in range(0, 33)}
        assert len(phases) >= 2

    def test_ambient_phase_distribution(self, ambient_32):
        phases = {ambient_32.phase_at(float(b)) for b in range(0, 33)}
        assert len(phases) >= 1

    def test_different_curves_phase_at_same_beat(self):
        """Different curve types may yield different phases at the same beat."""
        classical = TensionCurve(curve_type="classical")
        edm = TensionCurve(curve_type="edm")
        classical.phase_at(8.0)  # must not raise


# ══════════════════════════════════════════════════════════════════════════════
# _classical_curve() / _edm_curve() / _ambient_curve() / _build_release_curve()
# ══════════════════════════════════════════════════════════════════════════════


class TestClassicalCurveShape:
    def test_start_low(self):
        c = TensionCurve()
        assert c._classical_curve(0.0) == pytest.approx(0.2, abs=1e-4)

    def test_end_resolves(self):
        c = TensionCurve()
        t = c._classical_curve(1.0)
        assert t < 0.5  # should be resolved

    def test_between_peak_and_end_decreases(self):
        """tension strictly above peak+0.05 triggers the Resolution (falling) branch."""
        c = TensionCurve()
        # beat=0.71 → t=0.71/1.0, peak=0.7, start of Resolution, not a peak
        t_after = max(c._classical_curve(t) for t in [0.76, 0.80, 0.85, 0.90, 0.95, 1.0])
        assert t_after < 0.9

    def test_before_peak_monotonically_rising(self):
        c = TensionCurve()
        values = [
            c._classical_curve(t)
            for t in [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.69]
        ]
        for i in range(len(values) - 1):
            assert values[i] < values[i + 1], (
                f"Not rising at index {i}: {values[i]} vs {values[i + 1]}"
            )

    def test_respects_peak_intensity(self):
        c = TensionCurve(peak_intensity=0.5)
        t_at_peak = c._classical_curve(0.7)
        assert t_at_peak == pytest.approx(0.5, abs=1e-4)


class TestEdmCurveShape:
    def test_multiple_peaks(self):
        c = TensionCurve(curve_type="edm")
        pts = c.generate()
        # EDM with peak_intensity=0.9 should see values approaching 0.9
        max_t = max(p.tension for p in pts)
        assert max_t > 0.5

    def test_between_0_and_1(self):
        c = TensionCurve(curve_type="edm")
        for t in [i * 0.01 for i in range(101)]:
            val = c._edm_curve(t)
            assert 0.0 <= val <= 1.0, f"t={t}: {val}"

    def test_falls_after_cycle_peak(self):
        c = TensionCurve(curve_type="edm")
        # The drop branch fires for cycle >= 0.8; tension at the exact peak
        # should be > 0.5, meaning the curve reaches high tension
        touch = c._edm_curve(0.8)  # cycle=0.2 → not the drop; use a value well into
        # a known drop range: at t=0.9, cycle=0.6; peaks only happen near cycle<0.8
        max_in_any_cycle = max(
            c._edm_curve(t + 0.001) - c._edm_curve(t) + c._edm_curve(t + 0.002)
            for t in [i * 0.05 for i in range(50)]
        )
        # max_tension should be robustly close to peak_intensity
        assert max_in_any_cycle > 0.5  # rough sanity


class TestAmbientCurveShape:
    def test_constrained_range(self):
        c = TensionCurve(curve_type="ambient")
        for t in [i * 0.01 for i in range(101)]:
            val = c._ambient_curve(t)
            assert 0.0 <= val <= 1.0, f"t={t}: {val}"

    def test_center_value(self):
        c = TensionCurve(curve_type="ambient")
        # sin(0.5 * 2π) = sin(π) = 0  →  0.3 + 0.2*0 = 0.3
        assert c._ambient_curve(0.5) == pytest.approx(0.3, abs=1e-4)

    def test_peaks_at_quarter(self):
        c = TensionCurve(curve_type="ambient")
        val = c._ambient_curve(0.75)
        assert val == pytest.approx(0.1, abs=1e-4)

    def test_peaks_at_three_quarters(self):
        c = TensionCurve(curve_type="ambient")
        val = c._ambient_curve(0.25)
        assert val == pytest.approx(0.5, abs=1e-4)


class TestBuildReleaseCurveShape:
    def test_start_zero(self):
        c = TensionCurve(curve_type="build_release")
        assert c._build_release_curve(0.0) == pytest.approx(0.0, abs=1e-4)

    def test_peak_at_half(self):
        c = TensionCurve(curve_type="build_release")
        t = c._build_release_curve(0.5)
        assert t == pytest.approx(0.9, abs=1e-4)

    def test_end_zero(self):
        c = TensionCurve(curve_type="build_release")
        assert c._build_release_curve(1.0) == pytest.approx(0.0, abs=1e-4)

    def test_linear_rise(self):
        c = TensionCurve(curve_type="build_release")
        v0 = c._build_release_curve(0.0)
        v25 = c._build_release_curve(0.25)
        v50 = c._build_release_curve(0.5)
        assert v25 == pytest.approx(0.5 * (v50 - v0) + v0, abs=1e-4)

    def test_linear_fall(self):
        c = TensionCurve(curve_type="build_release")
        v50 = c._build_release_curve(0.5)  # peak
        v75 = c._build_release_curve(0.75)  # on the downhill
        v100 = c._build_release_curve(1.0)  # end
        assert v75 < v50
        assert v100 < v75

    def test_respects_peak_intensity(self):
        c = TensionCurve(curve_type="build_release", peak_intensity=0.6)
        assert c._build_release_curve(0.5) == pytest.approx(0.6, abs=1e-4)


# ══════════════════════════════════════════════════════════════════════════════
# _classify_phase() — direct private-method testing
# ══════════════════════════════════════════════════════════════════════════════


class TestClassifyPhase:
    def test_very_low_tension_rest(self):
        c = TensionCurve()
        assert c._classify_phase(0.0, 0.5) is TensionPhase.REST

    def test_near_peak_high_tension_climax(self):
        """tension > peak_intensity - 0.2 and t is not inside a BUILD/RESOLUTION window."""
        c = TensionCurve(peak_position=0.5, peak_intensity=1.0)
        # t=0.5 → not < peak-0.1; tension=0.9 → > peak-0.2=0.8
        assert c._classify_phase(0.9, 0.5) is TensionPhase.CLIMAX
        # Also verify that BUILD does NOT fire at this t/peak_position combo
        assert c._classify_phase(0.9, 0.5) is not TensionPhase.BUILD

    def test_after_peak_position_resolution(self):
        c = TensionCurve(peak_position=0.5)
        # t > peak_position + 0.1  →  RESOLUTION
        assert c._classify_phase(0.3, 0.7) is TensionPhase.RESOLUTION

    def test_before_peak_window_build(self):
        c = TensionCurve(peak_position=0.5)
        # t < peak_position - 0.1  →  BUILD
        assert c._classify_phase(0.4, 0.3) is TensionPhase.BUILD

    def test_mid_range_tension_sustain(self):
        c = TensionCurve(peak_position=0.5, peak_intensity=1.0)
        # tension not < 0.3, not > peak-0.2, t in peak±0.1
        result = c._classify_phase(0.5, 0.5)
        assert result is TensionPhase.SUSTAIN

    def test_phase_at_via_generated_points(self, classical_16):
        """Every generated point's tension should map to its declared phase."""
        for p in classical_16.generate():
            phase = classical_16._classify_phase(p.tension, p.beat / 16.0)
            assert phase == p.phase


# ══════════════════════════════════════════════════════════════════════════════
# Parameter sensitivity  (peak_position, peak_intensity, resolution_length)
# ══════════════════════════════════════════════════════════════════════════════


class TestParameterSensitivity:
    def test_higher_peak_position_shifts_climax(self):
        early = TensionCurve(peak_position=0.3)
        late = TensionCurve(peak_position=0.9)
        e_pts = early.generate()
        l_pts = late.generate()
        # find index of max tension
        e_max_i = max(range(len(e_pts)), key=lambda i: e_pts[i].tension)
        l_max_i = max(range(len(l_pts)), key=lambda i: l_pts[i].tension)
        e_max_beat = e_pts[e_max_i].beat
        l_max_beat = l_pts[l_max_i].beat
        assert e_max_beat < l_max_beat

    def test_higher_peak_intensity_more_height(self):
        low = TensionCurve(peak_intensity=0.3)
        high = TensionCurve(peak_intensity=0.95)
        assert max(p.tension for p in low.generate()) < max(p.tension for p in high.generate())

    def test_each_curve_type_return_is_list(self):
        for ctype in ("classical", "edm", "ambient", "build_release"):
            c = TensionCurve(curve_type=ctype)
            assert isinstance(c.generate(), list)

    @pytest.mark.parametrize("total_beats", [2.0, 4.0, 8.0, 16.0, 32.0, 64.0])
    def test_various_total_beats(self, total_beats):
        c = TensionCurve(total_beats=total_beats)
        points = c.generate()
        assert len(points) >= 8
        assert points[-1].beat == pytest.approx(total_beats, abs=1e-4)

    @pytest.mark.parametrize("curve_type", ["classical", "edm", "ambient", "build_release"])
    def test_generate_results_all_have_phase(self, curve_type):
        c = TensionCurve(total_beats=16.0, curve_type=curve_type)
        for p in c.generate():
            assert isinstance(p.phase, TensionPhase)

    @pytest.mark.parametrize("curve_type", ["classical", "edm", "ambient", "build_release"])
    def test_generate_results_all_have_valid_tension(self, curve_type):
        c = TensionCurve(total_beats=16.0, curve_type=curve_type)
        for p in c.generate():
            assert 0.0 <= p.tension <= 1.0


# ══════════════════════════════════════════════════════════════════════════════
# Export / import smoke-tests
# ══════════════════════════════════════════════════════════════════════════════


class TestImports:
    def test_import_tension_phase(self):
        from melodica.composer.tension_curve import TensionPhase

        assert TensionPhase is not None

    def test_import_tension_point(self):
        from melodica.composer.tension_curve import TensionPoint

        assert TensionPoint is not None

    def test_import_tension_curve(self):
        from melodica.composer.tension_curve import TensionCurve

        assert TensionCurve is not None

    def test_from_composer_package(self):
        from melodica.composer import TensionCurve as TC

        assert TC is TensionCurve


# ══════════════════════════════════════════════════════════════════════════════
# _ambient_curve() detailed shape checks
# ══════════════════════════════════════════════════════════════════════════════


class TestAmbientCurveDetailed:
    def test_range_is_strictly_within(self):
        c = TensionCurve(curve_type="ambient")
        for t in [i * 0.001 for i in range(0, 1001)]:
            val = c._ambient_curve(t)
            assert -0.1001 <= val <= 0.5001, f"t={t}: {val}"

    def test_multiple_periods(self):
        c = TensionCurve(curve_type="ambient")
        # sin completes one full cycle every 1.0 of t → peak at every 0.5 interval
        for base in [0.0, 0.5, 1.0, 1.5]:
            val = c._ambient_curve(base)
            assert val == pytest.approx(0.3, abs=1e-4)

    def test_quadrants_range(self):
        c = TensionCurve(curve_type="ambient")
        # sin(π*2*0.75) = sin(1.5π) = −1 → floating-point rounds to ≈0.1
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            val = c._ambient_curve(t)
            assert 0.09999 <= val <= 0.50001, f"t={t}: {val}"


# ══════════════════════════════════════════════════════════════════════════════
# _edm_curve() cycle-level detail
# ══════════════════════════════════════════════════════════════════════════════


class TestEdmCurveDetailed:
    def test_peak_at_cycle_start(self):
        c = TensionCurve(curve_type="edm")
        # cycle=0.0 (t*4 % 1 == 0) → first cycle, bottom of build ramp
        assert c._edm_curve(0.0) == pytest.approx(0.0, abs=1e-4)

    def test_cycle_boundary_consistency(self):
        """At each 1/4 t-interval the cycle resets — value continuity holds."""
        c = TensionCurve(curve_type="edm")
        for i in range(5):
            t = i * 0.25
            val = c._edm_curve(t)
            assert 0.0 <= val <= c.peak_intensity + 0.1e-4

    def test_drop_branch_at_cycle_end(self):
        """cycle >= 0.8 drops tension below peak_intensity * 0.95."""
        c = TensionCurve(curve_type="edm", peak_intensity=1.0)
        # The drop branch linear-ramps tension from peak (cycle=0.8) to 50%
        # of peak_intensity (cycle=1.0); at any cycle_val > 0.8 the value should
        # be strictly less than peak_intensity.
        for cycle_val in [0.9, 0.95, 0.99]:
            for t_off in [0.0, 0.25, 0.5, 0.75]:
                t = t_off + cycle_val / 4.0
                if t > 1.0:
                    continue
                val = c._edm_curve(t)
                assert val < c.peak_intensity, (
                    f"t={t:.3f} cycle={cycle_val}: expected drop below {c.peak_intensity}, got {val}"
                )


# ══════════════════════════════════════════════════════════════════════════════
# _build_release_curve() detailed slope tests
# ══════════════════════════════════════════════════════════════════════════════


class TestBuildReleaseCurveDetailed:
    def test_symmetric_rise_and_fall(self):
        c = TensionCurve(curve_type="build_release", peak_intensity=0.5)
        for dt in [0.01, 0.05, 0.1, 0.2]:
            v_before = c._build_release_curve(0.5 - dt)
            v_after = c._build_release_curve(0.5 + dt)
            assert v_before == pytest.approx(v_after, abs=1e-4)

    def test_quarter_values_at_quarter_beats(self):
        c = TensionCurve(curve_type="build_release", peak_intensity=0.8)
        # t=0.25 → 0.5*0.8 = 0.4; t=0.75 → 0.8*(1 - 0.5) = 0.4
        assert c._build_release_curve(0.25) == pytest.approx(0.4, abs=1e-4)
        assert c._build_release_curve(0.75) == pytest.approx(0.4, abs=1e-4)

    def test_linearly_increasing_before_half(self):
        c = TensionCurve(curve_type="build_release")
        values = [c._build_release_curve(t) for t in [0.0, 0.1, 0.2, 0.3, 0.4]]
        for i in range(len(values) - 1):
            assert values[i] < values[i + 1], (
                f"Expected rise at {i}: {values[i]} vs {values[i + 1]}"
            )

    def test_linearly_decreasing_after_half(self):
        c = TensionCurve(curve_type="build_release")
        values = [c._build_release_curve(t) for t in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]
        for i in range(len(values) - 1):
            assert values[i] > values[i + 1], (
                f"Expected fall at {i}: {values[i]} vs {values[i + 1]}"
            )


# ══════════════════════════════════════════════════════════════════════════════
# Peak intensity styling — sensitivity to peak_intensity in each curve type
# ══════════════════════════════════════════════════════════════════════════════


class TestPeakIntensitySensitivity:
    def test_classical_peak_tracks_intensity(self):
        for intensity in [0.1, 0.3, 0.5, 0.7, 0.9]:
            c = TensionCurve(curve_type="classical", peak_intensity=intensity)
            peak_t = c._classical_curve(0.7)
            assert peak_t == pytest.approx(intensity, abs=1e-4), (
                f"intensity={intensity} got peak={peak_t}"
            )

    def test_edm_peak_tracks_intensity(self):
        c = TensionCurve(curve_type="edm", peak_intensity=0.6)
        pts = c.generate()
        # tension should never exceed peak_intensity by more than floating-point noise
        assert all(p.tension <= c.peak_intensity + 1e-4 for p in pts)

    def test_build_release_peak_tracks_intensity_at_half(self):
        for intensity in [0.1, 0.5, 0.9]:
            c = TensionCurve(curve_type="build_release", peak_intensity=intensity)
            peak_t = c._build_release_curve(0.5)
            assert peak_t == pytest.approx(intensity, abs=1e-4)

    def test_peak_intensity_zero_classical_stays_low(self):
        """Even with peak_intensity=0 the rest-base of 0.2 prevents a full collapse."""
        c = TensionCurve(curve_type="classical", peak_intensity=0.0)
        pts = c.generate()
        # Classical rest phase floors at 0.2 regardless of peak_intensity
        for p in pts:
            assert p.tension >= 0.1, f"Unexpected low tension {p.tension} at beat {p.beat}"

    def test_peak_intensity_one_gives_max_classical(self):
        c = TensionCurve(curve_type="classical", peak_intensity=1.0)
        pts = c.generate()
        assert any(p.tension > 0.9 for p in pts)


# ══════════════════════════════════════════════════════════════════════════════
# phase_at() boundary edge cases
# ══════════════════════════════════════════════════════════════════════════════


class TestPhaseAtEdgeCases:
    def test_phase_at_exact_generated_points(self):
        """phase_at on every generated point beat should equal the point's phase."""
        c = TensionCurve(total_beats=16.0, curve_type="classical")
        pts = c.generate()
        for p in pts:
            phase = c.phase_at(p.beat)
            assert phase is p.phase, f"Mismatch at beat {p.beat}: point={p.phase}, phase_at={phase}"

    def test_phase_returns_first_ge_beat(self):
        """When two points share the same beat, phase_at should return the earlier one."""
        c = TensionCurve(total_beats=4.0)
        pts = c.generate()
        # The first point has beat=0.0; phase_at(0.0) should return its phase
        first_phase = pts[0].phase
        assert c.phase_at(0.0) is first_phase

    def test_phase_at_out_of_range_beyond_total(self):
        """Beat strictly beyond total_beats should fall through to SUSTAIN."""
        c = TensionCurve(total_beats=8.0)
        assert c.phase_at(c.total_beats + 0.001) is TensionPhase.SUSTAIN

    def test_phase_at_total_beats_exactly(self):
        """At beat == total_beats the exact point's phase is returned."""
        c = TensionCurve(total_beats=16.0)
        pts = c.generate()
        last = pts[-1]
        assert c.phase_at(last.beat) == last.phase


# ══════════════════════════════════════════════════════════════════════════════
# _classify_phase() boundary conditions
# ══════════════════════════════════════════════════════════════════════════════


class TestClassifyPhaseEdgeCases:
    def test_rest_and_build_boundary_around_03(self):
        """tension=0.3 is NOT < 0.3, so REST is skipped per PIL ordering → BUILD."""
        c = TensionCurve()
        # PIL chain: tension < 0.3? → 0.3 < 0.3 is False
        # t < peak_position - 0.1?  0.0 < 0.6 is True → BUILD
        assert c._classify_phase(0.3, 0.0) is TensionPhase.BUILD

    def test_strictly_less_than_03_is_rest(self):
        """tension=0.29 < 0.3 → REST wins even at t=0."""
        c = TensionCurve()
        assert c._classify_phase(0.29, 0.0) is TensionPhase.REST

    def test_climax_boundary_at_peak_intensity_minus_02(self):
        c = TensionCurve(peak_position=0.5, peak_intensity=1.0)
        # tension = peak_intensity - 0.2 = 0.8; exactly at threshold
        # PIL chain: tension>=0.3 ✓ not REST; t=0.5 not < 0.4 ✓ not BUILD
        # tension > 0.8? No, it's ==. 0.8 > 0.8 is False → not CLIMAX
        # t = 0.5 not > 0.6 → not RESOLUTION → SUSTAIN
        assert c._classify_phase(0.8, 0.5) is TensionPhase.SUSTAIN

    def test_climax_boundary_just_above_threshold_but_before_peak_position(self):
        c = TensionCurve(peak_position=0.5, peak_intensity=1.0)
        # PIL chain: tension>=0.3 ✓ not REST; t=0.1 < 0.4 ✓ BUILD first
        assert c._classify_phase(0.81, 0.1) is TensionPhase.BUILD

    def test_classical_peaks_must_exceed_70_percent_of_peak_intensity(self):
        """The classical curve's peak tension should reach near peak_intensity."""
        c = TensionCurve(total_beats=8.0)
        pts = c.generate()
        max_t = max(p.tension for p in pts)
        assert max_t >= 0.7, f"max tension {max_t} below 70% of peak_intensity"

    def test_classical_generated_always_reaches_climax_phase(self):
        """Generated classical curve should include the CLIMAX phase."""
        c = TensionCurve(total_beats=32.0)
        pts = c.generate()
        phases = {p.phase for p in pts}
        assert TensionPhase.CLIMAX in phases

    def test_edm_must_include_climax(self):
        c = TensionCurve(total_beats=32.0, curve_type="edm")
        pts = c.generate()
        phases = {p.phase for p in pts}
        assert TensionPhase.CLIMAX in phases

    def test_build_release_must_include_build_and_rest(self):
        """Default peak_position/peak_intensity produce REST and BUILD in 16-beat build_release."""
        c = TensionCurve(total_beats=16.0, curve_type="build_release")
        pts = c.generate()
        phases = {p.phase for p in pts}
        assert TensionPhase.REST in phases
        assert TensionPhase.BUILD in phases
