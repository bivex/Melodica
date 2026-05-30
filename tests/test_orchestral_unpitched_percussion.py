"""Tests for the six orchestral unpitched percussion generators."""

import random

import pytest

from melodica.types import Scale, Mode, ChordLabel, Quality
from melodica.generators.orchestral_unpitched_percussion import (
    BassDrumGenerator,
    TamTamGenerator,
    GongGenerator,
    TriangleGenerator,
    CastanetsGenerator,
    WhipSlapstickGenerator,
    BASS_DRUM_GRAN_CASSA,
    BASS_DRUM_ACOUSTIC,
    TAM_TAM,
    GONG,
    TRIANGLE,
    CASTANETS,
    SLAPSTICK,
)

KEY = Scale(root=0, mode=Mode.MAJOR)
CHORDS = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=16)]


def _notes(gen, pattern_type=None):
    kw = {"pattern_type": pattern_type} if pattern_type else {}
    return gen.render(CHORDS, KEY, 16.0, **kw)


class TestBassDrumGenerator:
    def test_single_produces_notes(self):
        random.seed(42)
        gen = BassDrumGenerator(pattern_type="single")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) >= 1
        assert all(n.pitch in (BASS_DRUM_GRAN_CASSA, BASS_DRUM_ACOUSTIC) for n in notes)

    def test_roll_crescendo(self):
        random.seed(42)
        gen = BassDrumGenerator(pattern_type="roll")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) > 1
        vels = [n.velocity for n in notes]
        assert vels[-1] > vels[0]

    def test_march_steady_pulse(self):
        random.seed(42)
        gen = BassDrumGenerator(pattern_type="march")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) >= 8
        starts = [n.start for n in notes]
        for i in range(1, len(starts)):
            assert starts[i] - starts[i - 1] == pytest.approx(1.0)

    def test_velocities_in_range(self):
        random.seed(42)
        for pt in ("single", "roll", "march"):
            gen = BassDrumGenerator(pattern_type=pt)
            notes = gen.render(CHORDS, KEY, 16.0)
            for n in notes:
                assert 1 <= n.velocity <= 127


class TestTamTamGenerator:
    def test_strike_produces_notes(self):
        random.seed(42)
        gen = TamTamGenerator(pattern_type="strike")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) >= 1
        assert all(n.pitch == TAM_TAM for n in notes)

    def test_crescendo_strike_builds(self):
        random.seed(42)
        gen = TamTamGenerator(pattern_type="crescendo_strike")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) > 1
        # Last note should be the peak
        assert notes[-1].velocity >= 100

    def test_tremolo_durations_short(self):
        random.seed(42)
        gen = TamTamGenerator(pattern_type="tremolo")
        notes = gen.render(CHORDS, KEY, 4.0)
        assert len(notes) > 4
        for n in notes:
            assert n.duration <= 0.5


class TestGongGenerator:
    def test_strike_produces_notes(self):
        random.seed(42)
        gen = GongGenerator(pattern_type="strike")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) >= 1
        assert all(n.pitch == GONG for n in notes)

    def test_roll_ends_with_peak(self):
        random.seed(42)
        gen = GongGenerator(pattern_type="roll")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) > 1
        assert notes[-1].velocity >= 100

    def test_crescendo_ascending_velocity(self):
        random.seed(42)
        gen = GongGenerator(pattern_type="crescendo")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) >= 2
        assert notes[-1].velocity > notes[0].velocity


class TestTriangleGenerator:
    def test_single_may_produce_notes(self):
        random.seed(42)
        gen = TriangleGenerator(pattern_type="single")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert isinstance(notes, list)

    def test_roll_produces_stream(self):
        random.seed(42)
        gen = TriangleGenerator(pattern_type="roll")
        notes = gen.render(CHORDS, KEY, 4.0)
        assert len(notes) > 4
        assert all(n.pitch == TRIANGLE for n in notes)

    def test_trill_rapid(self):
        random.seed(42)
        gen = TriangleGenerator(pattern_type="trill")
        notes = gen.render(CHORDS, KEY, 2.0)
        assert len(notes) > 8

    def test_soft_velocities(self):
        random.seed(42)
        gen = TriangleGenerator(pattern_type="roll")
        notes = gen.render(CHORDS, KEY, 4.0)
        for n in notes:
            assert n.velocity <= 80


class TestCastanetsGenerator:
    def test_single_may_produce_notes(self):
        random.seed(42)
        gen = CastanetsGenerator(pattern_type="single")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert isinstance(notes, list)

    def test_roll_rapid(self):
        random.seed(42)
        gen = CastanetsGenerator(pattern_type="roll")
        notes = gen.render(CHORDS, KEY, 4.0)
        assert len(notes) > 8
        assert all(n.pitch == CASTANETS for n in notes)

    def test_rhythm_has_pattern(self):
        random.seed(42)
        gen = CastanetsGenerator(pattern_type="rhythm")
        notes = gen.render(CHORDS, KEY, 4.0)
        assert len(notes) >= 4
        # Should have pairs (long-short per beat)
        starts = [n.start for n in notes]
        assert any(s > 0 for s in starts)

    def test_short_durations(self):
        random.seed(42)
        gen = CastanetsGenerator(pattern_type="roll")
        notes = gen.render(CHORDS, KEY, 4.0)
        for n in notes:
            assert n.duration <= 0.5


class TestWhipSlapstickGenerator:
    def test_single_produces_notes(self):
        random.seed(42)
        gen = WhipSlapstickGenerator(pattern_type="single")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) >= 1
        assert all(n.pitch == SLAPSTICK for n in notes)

    def test_rapid_multiple_cracks(self):
        random.seed(42)
        gen = WhipSlapstickGenerator(pattern_type="rapid")
        notes = gen.render(CHORDS, KEY, 16.0)
        assert len(notes) >= 2

    def test_very_short_duration(self):
        random.seed(42)
        gen = WhipSlapstickGenerator(pattern_type="rapid")
        notes = gen.render(CHORDS, KEY, 16.0)
        for n in notes:
            assert n.duration <= 0.5

    def test_high_velocity(self):
        random.seed(42)
        gen = WhipSlapstickGenerator(pattern_type="single")
        notes = gen.render(CHORDS, KEY, 16.0)
        for n in notes:
            assert n.velocity >= 80


class TestCommonBehavior:
    @pytest.mark.parametrize("cls", [
        BassDrumGenerator, TamTamGenerator, GongGenerator,
        TriangleGenerator, CastanetsGenerator, WhipSlapstickGenerator,
    ])
    def test_empty_chords_returns_empty(self, cls):
        gen = cls()
        assert gen.render([], KEY, 16.0) == []

    @pytest.mark.parametrize("cls", [
        BassDrumGenerator, TamTamGenerator, GongGenerator,
        TriangleGenerator, CastanetsGenerator, WhipSlapstickGenerator,
    ])
    def test_returns_sorted_notes(self, cls):
        random.seed(42)
        multi = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=8),
            ChordLabel(root=5, quality=Quality.MAJOR, start=8, duration=8),
        ]
        gen = cls()
        notes = gen.render(multi, KEY, 16.0)
        if notes:
            starts = [n.start for n in notes]
            assert starts == sorted(starts)

    @pytest.mark.parametrize("cls", [
        BassDrumGenerator, TamTamGenerator, GongGenerator,
        TriangleGenerator, CastanetsGenerator, WhipSlapstickGenerator,
    ])
    def test_has_name(self, cls):
        gen = cls()
        assert gen.name  # non-empty string
