"""Unit tests for BarGrid — beat↔bar conversion, change_points, alignment."""

from __future__ import annotations

import math

import pytest

from melodica.types import BarGrid


# ------------------------------------------------------------------
# beats_per_bar
# ------------------------------------------------------------------

class TestBeatsPerBar:
    def test_4_4(self):
        assert BarGrid(4, 4).beats_per_bar == 4.0

    def test_3_4(self):
        assert BarGrid(3, 4).beats_per_bar == 3.0

    def test_6_8(self):
        assert BarGrid(6, 8).beats_per_bar == 3.0

    def test_5_4(self):
        assert BarGrid(5, 4).beats_per_bar == 5.0

    def test_7_8(self):
        assert BarGrid(7, 8).beats_per_bar == 3.5

    def test_2_2(self):
        assert BarGrid(2, 2).beats_per_bar == 4.0


# ------------------------------------------------------------------
# bar_of / beat_in_bar
# ------------------------------------------------------------------

class TestBarOf:
    def test_first_beat(self):
        assert BarGrid(4, 4).bar_of(0.0) == 0

    def test_mid_bar(self):
        assert BarGrid(4, 4).bar_of(2.5) == 0

    def test_second_bar(self):
        assert BarGrid(4, 4).bar_of(4.0) == 1

    def test_3_4(self):
        g = BarGrid(3, 4)
        assert g.bar_of(0.0) == 0
        assert g.bar_of(2.9) == 0
        assert g.bar_of(3.0) == 1
        assert g.bar_of(6.0) == 2

    def test_6_8(self):
        g = BarGrid(6, 8)
        assert g.bar_of(0.0) == 0
        assert g.bar_of(2.9) == 0
        assert g.bar_of(3.0) == 1


class TestBeatInBar:
    def test_downbeat(self):
        assert BarGrid(4, 4).beat_in_bar(0.0) == 0.0

    def test_mid_bar(self):
        assert BarGrid(4, 4).beat_in_bar(2.5) == pytest.approx(2.5)

    def test_bar_boundary(self):
        assert BarGrid(4, 4).beat_in_bar(4.0) == pytest.approx(0.0)

    def test_3_4(self):
        g = BarGrid(3, 4)
        assert g.beat_in_bar(1.0) == pytest.approx(1.0)
        assert g.beat_in_bar(3.0) == pytest.approx(0.0)


# ------------------------------------------------------------------
# is_downbeat
# ------------------------------------------------------------------

class TestIsDownbeat:
    def test_zero(self):
        assert BarGrid(4, 4).is_downbeat(0.0)

    def test_bar_start(self):
        assert BarGrid(4, 4).is_downbeat(4.0)

    def test_mid_bar(self):
        assert not BarGrid(4, 4).is_downbeat(2.0)

    def test_3_4(self):
        g = BarGrid(3, 4)
        assert g.is_downbeat(0.0)
        assert g.is_downbeat(3.0)
        assert g.is_downbeat(6.0)
        assert not g.is_downbeat(1.5)

    def test_floating_point_tolerance(self):
        assert BarGrid(4, 4).is_downbeat(8.0000001)


# ------------------------------------------------------------------
# bar_start
# ------------------------------------------------------------------

class TestBarStart:
    def test_first(self):
        assert BarGrid(4, 4).bar_start(0) == 0.0

    def test_second(self):
        assert BarGrid(4, 4).bar_start(1) == 4.0

    def test_3_4(self):
        assert BarGrid(3, 4).bar_start(3) == 9.0

    def test_5_4(self):
        assert BarGrid(5, 4).bar_start(4) == 20.0


# ------------------------------------------------------------------
# alignment
# ------------------------------------------------------------------

class TestAlignUp:
    def test_already_aligned(self):
        assert BarGrid(4, 4).align_up(4.0) == 4.0

    def test_mid_bar(self):
        assert BarGrid(4, 4).align_up(2.0) == 4.0

    def test_near_zero(self):
        assert BarGrid(4, 4).align_up(0.1) == 4.0

    def test_3_4(self):
        assert BarGrid(3, 4).align_up(1.0) == 3.0
        assert BarGrid(3, 4).align_up(4.0) == 6.0


class TestAlignDown:
    def test_already_aligned(self):
        assert BarGrid(4, 4).align_down(4.0) == 4.0

    def test_mid_bar(self):
        assert BarGrid(4, 4).align_down(2.0) == 0.0

    def test_second_bar(self):
        assert BarGrid(4, 4).align_down(5.0) == 4.0

    def test_3_4(self):
        assert BarGrid(3, 4).align_down(5.0) == 3.0
        assert BarGrid(3, 4).align_down(2.9) == 0.0


# ------------------------------------------------------------------
# change_points
# ------------------------------------------------------------------

class TestChangePoints:
    def test_bars_4_4(self):
        pts = BarGrid(4, 4).change_points(16.0, "bars")
        assert pts == [0.0, 4.0, 8.0, 12.0]

    def test_bars_3_4(self):
        pts = BarGrid(3, 4).change_points(12.0, "bars")
        assert pts == [0.0, 3.0, 6.0, 9.0]

    def test_bars_6_8(self):
        pts = BarGrid(6, 8).change_points(12.0, "bars")
        assert pts == [0.0, 3.0, 6.0, 9.0]

    def test_bars_5_4(self):
        pts = BarGrid(5, 4).change_points(20.0, "bars")
        assert pts == [0.0, 5.0, 10.0, 15.0]

    def test_strong_beats(self):
        pts = BarGrid(4, 4).change_points(8.0, "strong_beats")
        assert pts == [0.0, 2.0, 4.0, 6.0]

    def test_beats_mode(self):
        pts = BarGrid(4, 4).change_points(4.0, "beats")
        assert pts == [0.0, 1.0, 2.0, 3.0]

    def test_strong_beats_3_4(self):
        pts = BarGrid(3, 4).change_points(6.0, "strong_beats")
        assert pts == [0.0, 1.5, 3.0, 4.5]

    def test_zero_duration(self):
        assert BarGrid(4, 4).change_points(0.0) == []

    def test_partial_bar(self):
        pts = BarGrid(4, 4).change_points(3.0, "bars")
        assert pts == [0.0]


# ------------------------------------------------------------------
# immutability
# ------------------------------------------------------------------

class TestImmutability:
    def test_frozen(self):
        g = BarGrid(4, 4)
        with pytest.raises(AttributeError):
            g.numerator = 3  # type: ignore[misc]

    def test_hashable(self):
        s = {BarGrid(4, 4), BarGrid(3, 4), BarGrid(4, 4)}
        assert len(s) == 2
