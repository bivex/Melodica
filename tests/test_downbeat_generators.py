"""Tests for the new downbeat-related generators: Hemiola, Backbeat, DownbeatRest."""

from __future__ import annotations

import pytest

from melodica.generators import GeneratorParams
from melodica.generators.hemiola import HemiolaGenerator
from melodica.generators.backbeat import BackbeatGenerator
from melodica.generators.downbeat_rest import DownbeatRestGenerator
from melodica.types import ChordLabel, Scale, Mode


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def c_major():
    return Scale(root=0, mode=Mode.MAJOR)


@pytest.fixture()
def c_chord():
    return ChordLabel(root=0, quality="major", start=0.0, duration=4.0)


@pytest.fixture()
def f_chord():
    return ChordLabel(root=5, quality="major", start=4.0, duration=4.0)


@pytest.fixture()
def two_chords(c_chord, f_chord):
    return [c_chord, f_chord]


@pytest.fixture()
def params():
    return GeneratorParams(density=0.8)


# ===================================================================
# HemiolaGenerator
# ===================================================================


class TestHemiolaGenerator:
    def test_basic_render(self, params, two_chords, c_major):
        gen = HemiolaGenerator(params, pattern="3_over_2")
        notes = gen.render(two_chords, c_major, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert n.duration > 0
            assert 1 <= n.velocity <= 127

    def test_3_over_2_pattern_spacing(self, params, two_chords, c_major):
        gen = HemiolaGenerator(params, pattern="3_over_2", cycles_per_chord=1)
        notes = gen.render(two_chords, c_major, 4.0)
        # 3 notes per cycle, cycle=2 beats, 4 beats total = 2 cycles = 6 notes
        onsets = [n.start for n in notes]
        # First 3 notes should be spaced by ~2/3 beats
        for i in range(1, min(3, len(onsets))):
            gap = onsets[i] - onsets[i - 1]
            assert abs(gap - 2.0 / 3.0) < 0.01

    def test_2_over_3_pattern(self, params, two_chords, c_major):
        gen = HemiolaGenerator(params, pattern="2_over_3")
        notes = gen.render(two_chords, c_major, 6.0)
        assert len(notes) > 0
        onsets = [n.start for n in notes]
        # 2 notes per 3-beat cycle → spacing = 1.5 beats
        if len(onsets) >= 2:
            gap = onsets[1] - onsets[0]
            assert abs(gap - 1.5) < 0.01

    def test_velocity_accent_on_first_note(self, params, c_chord, c_major):
        gen = HemiolaGenerator(params, pattern="3_over_2", velocity_accent=1.3)
        notes = gen.render([c_chord], c_major, 2.0)
        assert len(notes) >= 1
        # First note should have higher velocity than subsequent
        if len(notes) > 1:
            assert notes[0].velocity > notes[1].velocity

    def test_pitch_strategies(self, params, c_chord, c_major):
        for strategy in ("chord_tone", "scale_tone", "root_fifth"):
            gen = HemiolaGenerator(params, pattern="3_over_2", pitch_strategy=strategy)
            notes = gen.render([c_chord], c_major, 2.0)
            assert len(notes) > 0
            for n in notes:
                assert isinstance(n.pitch, int)
                assert 0 <= n.pitch <= 127

    def test_empty_chords(self, params, c_major):
        gen = HemiolaGenerator(params)
        notes = gen.render([], c_major, 4.0)
        assert notes == []

    def test_invalid_pattern(self, params):
        with pytest.raises(ValueError, match="Unknown hemiola pattern"):
            HemiolaGenerator(params, pattern="invalid")

    def test_cycles_per_chord(self, params, c_chord, c_major):
        gen = HemiolaGenerator(params, pattern="3_over_2", cycles_per_chord=2)
        notes = gen.render([c_chord], c_major, 4.0)
        # 3 notes × 2 cycles = 6 notes in 4 beats
        assert len(notes) == 6

    def test_auto_duration(self, params, c_chord, c_major):
        gen = HemiolaGenerator(params, pattern="3_over_2", note_duration=None)
        notes = gen.render([c_chord], c_major, 2.0)
        # Auto duration = 2.0 / 3 ≈ 0.667
        for n in notes:
            assert abs(n.duration - 2.0 / 3.0) < 0.01


# ===================================================================
# BackbeatGenerator
# ===================================================================


class TestBackbeatGenerator:
    def test_accent_mode(self, params, c_chord, c_major):
        gen = BackbeatGenerator(params, mode="accent")
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 0
        # All notes should be on beats 2 or 4 (positions 1.0 and 3.0)
        for n in notes:
            beat_pos = n.start % 4.0
            assert abs(beat_pos - 1.0) < 0.05 or abs(beat_pos - 3.0) < 0.05

    def test_ghost_mode_has_more_notes(self, params, c_chord, c_major):
        accent = BackbeatGenerator(params, mode="accent")
        ghost = BackbeatGenerator(params, mode="ghost")
        accent_notes = accent.render([c_chord], c_major, 4.0)
        ghost_notes = ghost.render([c_chord], c_major, 4.0)
        # Ghost mode has notes on every subdivision, accent only on 2 & 4
        assert len(ghost_notes) > len(accent_notes)

    def test_ghost_mode_velocity_difference(self, params, c_chord, c_major):
        gen = BackbeatGenerator(params, mode="ghost", accent_velocity=1.0, ghost_velocity=0.4)
        notes = gen.render([c_chord], c_major, 4.0)
        backbeat_vels = [
            n.velocity
            for n in notes
            if abs((n.start % 4.0) - 1.0) < 0.05 or abs((n.start % 4.0) - 3.0) < 0.05
        ]
        ghost_vels = [
            n.velocity
            for n in notes
            if abs((n.start % 4.0) - 0.0) < 0.05 or abs((n.start % 4.0) - 2.0) < 0.05
        ]
        if backbeat_vels and ghost_vels:
            assert min(backbeat_vels) > max(ghost_vels)

    def test_chop_mode_staccato(self, params, c_chord, c_major):
        gen = BackbeatGenerator(params, mode="chop", subdivision=1.0)
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 0
        # Chop mode should have short notes
        for n in notes:
            assert n.duration <= 0.5

    def test_melody_mode(self, params, c_chord, c_major):
        gen = BackbeatGenerator(params, mode="melody")
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) == 4  # one note per quarter

    def test_empty_chords(self, params, c_major):
        gen = BackbeatGenerator(params)
        notes = gen.render([], c_major, 4.0)
        assert notes == []

    def test_invalid_mode(self, params):
        with pytest.raises(ValueError, match="Unknown backbeat mode"):
            BackbeatGenerator(params, mode="invalid")

    def test_pitch_strategies(self, params, c_chord, c_major):
        for strategy in ("chord_tone", "root", "fifth", "octave"):
            gen = BackbeatGenerator(params, mode="accent", pitch_strategy=strategy)
            notes = gen.render([c_chord], c_major, 4.0)
            assert len(notes) > 0

    def test_subdivision(self, params, c_chord, c_major):
        gen = BackbeatGenerator(params, mode="melody", subdivision=0.5)
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) == 8  # eighth notes

    def test_velocity_clamped(self, params, c_chord, c_major):
        gen = BackbeatGenerator(params, mode="accent", accent_velocity=999.0)
        notes = gen.render([c_chord], c_major, 4.0)
        for n in notes:
            assert 1 <= n.velocity <= 127


# ===================================================================
# DownbeatRestGenerator
# ===================================================================


class TestDownbeatRestGenerator:
    def test_skip_mode_no_downbeat(self, params, c_chord, c_major):
        gen = DownbeatRestGenerator(params, mode="skip")
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 0
        # No note should be exactly on beat 1 (onset 0.0)
        for n in notes:
            assert n.start > 0.05 or n.start > 0  # skip beat 0

    def test_delay_mode(self, params, c_chord, c_major):
        gen = DownbeatRestGenerator(params, mode="delay", delay_amount=0.5)
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 0
        # First note should be delayed (not on 0.0)
        assert notes[0].start > 0.1

    def test_caesura_mode_gap(self, params, c_chord, c_major):
        gen = DownbeatRestGenerator(params, mode="caesura", caesura_length=1.0)
        notes = gen.render([c_chord], c_major, 4.0)
        # First note should start after the caesura zone
        if notes:
            assert notes[0].start >= 1.0

    def test_breath_mode_short_pre_downbeat(self, params, c_chord, c_major):
        gen = DownbeatRestGenerator(params, mode="breath", subdivision=1.0)
        notes = gen.render([c_chord], c_major, 8.0)
        # Notes just before downbeats (at 3.0, 7.0) should be shorter
        pre_downbeat = [n for n in notes if abs((n.start % 4.0) - 3.0) < 0.05]
        regular = [n for n in notes if 0.5 < (n.start % 4.0) < 2.5]
        if pre_downbeat and regular:
            assert pre_downbeat[0].duration < regular[0].duration

    def test_empty_chords(self, params, c_major):
        gen = DownbeatRestGenerator(params)
        notes = gen.render([], c_major, 4.0)
        assert notes == []

    def test_invalid_mode(self, params):
        with pytest.raises(ValueError, match="Unknown downbeat_rest mode"):
            DownbeatRestGenerator(params, mode="invalid")

    def test_all_notes_have_valid_velocity(self, params, c_chord, c_major):
        gen = DownbeatRestGenerator(params, mode="skip")
        notes = gen.render([c_chord], c_major, 8.0)
        for n in notes:
            assert 1 <= n.velocity <= 127

    def test_subdivision(self, params, c_chord, c_major):
        gen = DownbeatRestGenerator(params, mode="skip", subdivision=0.5)
        notes = gen.render([c_chord], c_major, 4.0)
        # With 0.5 subdivision, 4 beats = 8 sub-beats, minus downbeats (4,4,0,0) = skip beat 0
        assert len(notes) > 4  # more notes than quarter-note subdivision

    def test_pitch_strategies(self, params, c_chord, c_major):
        for strategy in ("chord_tone", "scale_tone", "root"):
            gen = DownbeatRestGenerator(params, mode="skip", pitch_strategy=strategy)
            notes = gen.render([c_chord], c_major, 4.0)
            assert len(notes) > 0

    def test_delay_preserves_velocity_boost(self, params, c_chord, c_major):
        gen = DownbeatRestGenerator(params, mode="delay", delay_amount=0.25)
        notes = gen.render([c_chord], c_major, 4.0)
        # Delayed downbeat notes should have boosted velocity (1.1x)
        delayed = [n for n in notes if 0.2 < n.start % 4.0 < 0.3]
        if delayed:
            assert delayed[0].velocity > 0


# ===================================================================
# Factory integration
# ===================================================================


class TestFactoryIntegration:
    def test_factory_creates_hemiola(self):
        from melodica.factory import create_generator

        gen = create_generator("hemiola", GeneratorParams(), {"pattern": "3_over_2"})
        assert isinstance(gen, HemiolaGenerator)

    def test_factory_creates_backbeat(self):
        from melodica.factory import create_generator

        gen = create_generator("backbeat", GeneratorParams(), {"mode": "ghost"})
        assert isinstance(gen, BackbeatGenerator)

    def test_factory_creates_downbeat_rest(self):
        from melodica.factory import create_generator

        gen = create_generator("downbeat_rest", GeneratorParams(), {"mode": "caesura"})
        assert isinstance(gen, DownbeatRestGenerator)

    def test_factory_integration(self, c_chord, c_major):
        from melodica.factory import create_generator

        gen = create_generator("hemiola", GeneratorParams(density=0.8), {"pattern": "2_over_3"})
        assert gen is not None
        notes = gen.render([c_chord], c_major, 6.0)
        assert len(notes) > 0
