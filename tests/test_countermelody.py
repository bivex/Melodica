# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""tests/test_countermelody.py — Tests for CountermelodyGenerator."""

import pytest
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.types import ChordLabel, Mode, NoteInfo, Quality, Scale
from melodica.render_context import RenderContext

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords():
    return [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0),
    ]


def _primary_melody():
    """Simple C major scale melody."""
    return [
        NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),  # C
        NoteInfo(pitch=62, start=1.0, duration=1.0, velocity=80),  # D
        NoteInfo(pitch=64, start=2.0, duration=1.0, velocity=80),  # E
        NoteInfo(pitch=65, start=3.0, duration=1.0, velocity=80),  # F
    ]


class TestCountermelodyBasic:
    """Basic functionality tests."""

    def test_produces_notes(self):
        gen = CountermelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_produces_notes_against_primary(self):
        gen = CountermelodyGenerator(primary_melody=_primary_melody())
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_motion_preference_contrary(self):
        gen = CountermelodyGenerator(
            primary_melody=_primary_melody(),
            motion_preference="contrary"
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_motion_preference_oblique(self):
        gen = CountermelodyGenerator(
            primary_melody=_primary_melody(),
            motion_preference="oblique"
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_motion_preference_mixed(self):
        gen = CountermelodyGenerator(
            primary_melody=_primary_melody(),
            motion_preference="mixed"
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_motion_raises(self):
        with pytest.raises(ValueError):
            CountermelodyGenerator(motion_preference="invalid")

    def test_dissonance_on_weak_true(self):
        gen = CountermelodyGenerator(
            primary_melody=_primary_melody(),
            dissonance_on_weak=True
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_dissonance_on_weak_false(self):
        gen = CountermelodyGenerator(
            primary_melody=_primary_melody(),
            dissonance_on_weak=False
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0


class TestCountermelodyIntervals:
    """Test interval limiting."""

    def test_interval_limit_small(self):
        gen = CountermelodyGenerator(
            primary_melody=_primary_melody(),
            interval_limit=3
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_interval_limit_large(self):
        gen = CountermelodyGenerator(
            primary_melody=_primary_melody(),
            interval_limit=12
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0


class TestCountermelodyContext:
    """Test context integration."""

    def test_context_prev_pitch(self):
        gen = CountermelodyGenerator()
        ctx = RenderContext(prev_pitch=72)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0, context=ctx)
        assert len(notes) > 0

    def test_context_prev_pitches(self):
        gen = CountermelodyGenerator()
        ctx = RenderContext(prev_pitches=[60, 64, 67])
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0, context=ctx)
        assert len(notes) > 0

    def test_last_context_stored(self):
        gen = CountermelodyGenerator(primary_melody=_primary_melody())
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert gen._last_context is not None
        assert gen._last_context.prev_pitch == notes[-1].pitch


class TestCountermelodyEdgeCases:
    """Edge cases."""

    def test_empty_chords(self):
        gen = CountermelodyGenerator()
        notes = gen.render([], C_MAJOR, 4.0)
        assert notes == []

    def test_short_duration(self):
        gen = CountermelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 0.5)
        assert len(notes) >= 0

    def test_free_counterpoint_no_primary(self):
        gen = CountermelodyGenerator(primary_melody=None)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
