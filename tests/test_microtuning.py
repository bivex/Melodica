"""Tests for microtuning engine and microtonal melody generator."""

import pytest
from melodica.types import NoteInfo, Scale, Mode
from melodica.engines.microtuning import MicrotuningEngine
from melodica.generators.microtonal_melody import MicrotonalMelodyGenerator
from melodica.generators import GeneratorParams


class TestMicrotuningEngine:
    def setup_method(self):
        self.engine = MicrotuningEngine(bend_range=2)

    def test_snap_to_major_scale(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        # 61 is C#, should snap to C (60) or D (62) in C major
        snapped = self.engine.snap_to_scale(61.0, key)
        assert snapped == 60.0 or snapped == 62.0

    def test_quantize_returns_int_pitch(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        midi_int, expr = self.engine.quantize_pitch(60.0, key)
        assert isinstance(midi_int, int)
        assert 0 <= midi_int <= 127

    def test_quantize_no_bend_for_scale_degree(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        _, expr = self.engine.quantize_pitch(60.0, key)  # C = root
        assert expr == {}  # No bend needed for exact scale degree

    def test_render_microtonal_note(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        note = self.engine.render_microtonal_note(61.0, 0.0, 2.0, 64, key)
        assert isinstance(note, NoteInfo)
        assert note.start == 0.0
        assert note.duration == 2.0
        assert note.velocity == 64

    def test_wrap_notes_preserves_count(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=64),
            NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=64),
        ]
        wrapped = self.engine.wrap_notes(notes, key)
        assert len(wrapped) == 2

    def test_cents_to_bend_range(self):
        # +100 cents (1 semitone) with bend_range=2 -> ~4096
        val = self.engine._cents_to_bend(100)
        assert abs(val - 4096) < 100


class TestMicrotonalMelodyGenerator:
    def test_render_returns_notes(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        from melodica.types import ChordLabel, Quality
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=32)]

        gen = MicrotonalMelodyGenerator(
            GeneratorParams(density=0.3, key_range_low=60, key_range_high=84),
        )
        notes = gen.render(chords, key, 32.0)
        assert len(notes) > 0
        assert all(isinstance(n, NoteInfo) for n in notes)
        # All notes within range
        assert all(60 <= n.pitch <= 84 for n in notes)

    def test_render_empty_on_zero_duration(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        from melodica.types import ChordLabel, Quality
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=1)]

        gen = MicrotonalMelodyGenerator()
        notes = gen.render(chords, key, 0.0)
        assert notes == []
