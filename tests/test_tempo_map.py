"""Tests for melodica.composer.tempo_map.TempoMap"""

import pytest

from melodica.composer.tempo_map import TempoMap


class TestDefaultBpm:
    def test_build_returns_initial(self):
        tm = TempoMap(120.0)
        result = tm.build()
        assert result == [(0.0, 120.0)]


class TestSetBpm:
    def test_instant_change(self):
        tm = TempoMap(120.0)
        tm.set_bpm(16.0, 80.0)
        result = tm.build()
        assert (16.0, 80.0) in result


class TestRitardando:
    def test_slowing(self):
        tm = TempoMap(120.0)
        tm.ritardando(120.0, 60.0, 0.0, 16.0, steps=4)
        result = tm.build()
        bpms = [bpm for _, bpm in result]
        assert bpms[0] == pytest.approx(120.0)
        assert bpms[-1] == pytest.approx(60.0)

    def test_intermediate_values(self):
        tm = TempoMap(120.0)
        tm.ritardando(120.0, 60.0, 0.0, 16.0, steps=4)
        result = tm.build()
        mid_bpm = result[2][1]
        assert 60.0 < mid_bpm < 120.0


class TestAccelerando:
    def test_speeding_up(self):
        tm = TempoMap(60.0)
        tm.set_bpm(0.0, 60.0)
        tm.accelerando(60.0, 140.0, 0.0, 16.0, steps=4)
        result = tm.build()
        bpms = [bpm for _, bpm in result]
        assert bpms[-1] == pytest.approx(140.0)


class TestFermata:
    def test_hold_and_resume(self):
        tm = TempoMap(120.0)
        tm.set_bpm(0.0, 120.0)
        tm.fermata(8.0, hold_bpm=20.0, duration_beats=2.0, resume_bpm=120.0)
        result = tm.build()
        beats = [b for b, _ in result]
        assert 8.0 in beats
        assert 10.0 in beats
        hold = [bpm for b, bpm in result if b == 8.0]
        assert hold[0] == pytest.approx(20.0)

    def test_auto_resume(self):
        tm = TempoMap(100.0)
        tm.set_bpm(0.0, 100.0)
        tm.fermata(8.0, hold_bpm=20.0, duration_beats=2.0)
        result = tm.build()
        resume = [bpm for b, bpm in result if b == 10.0]
        assert resume[0] == pytest.approx(100.0)


class TestRubato:
    def test_expressive_points(self):
        tm = TempoMap(100.0)
        tm.rubato([(4.0, 90.0), (8.0, 110.0), (12.0, 95.0)])
        result = tm.build()
        assert (4.0, 90.0) in result
        assert (12.0, 95.0) in result


class TestBuildSorted:
    def test_output_sorted_by_beat(self):
        tm = TempoMap(120.0)
        tm.set_bpm(8.0, 100.0)
        tm.set_bpm(2.0, 80.0)
        tm.set_bpm(16.0, 60.0)
        result = tm.build()
        beats = [b for b, _ in result]
        assert beats == sorted(beats)

    def test_duplicate_beats_last_wins(self):
        tm = TempoMap(120.0)
        tm.set_bpm(4.0, 100.0)
        tm.set_bpm(4.0, 80.0)
        result = tm.build()
        at_4 = [bpm for b, bpm in result if b == 4.0]
        assert len(at_4) == 1
        assert at_4[0] == pytest.approx(80.0)


class TestCurves:
    def test_sine_curve(self):
        tm = TempoMap(120.0)
        tm.ritardando(120.0, 60.0, 0.0, 16.0, curve="sine", steps=8)
        result = tm.build()
        bpms = [bpm for _, bpm in result]
        assert bpms[0] == pytest.approx(120.0)
        assert bpms[-1] == pytest.approx(60.0)

    def test_exponential_curve(self):
        tm = TempoMap(120.0)
        tm.accelerando(60.0, 120.0, 0.0, 16.0, curve="exponential", steps=8)
        result = tm.build()
        bpms = [bpm for _, bpm in result]
        assert bpms[0] == pytest.approx(60.0)
        assert bpms[-1] == pytest.approx(120.0)


class TestMidiCompatible:
    def test_output_is_list_of_tuples(self):
        tm = TempoMap(120.0)
        tm.ritardando(120.0, 60.0, 0.0, 16.0, steps=4)
        result = tm.build()
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], float)
            assert isinstance(item[1], float)
