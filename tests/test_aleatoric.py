"""Tests for AleatoricGenerator — all six modes."""

import pytest
from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators.aleatoric import AleatoricGenerator
from melodica.generators import GeneratorParams


def _chords(dur=32.0):
    return [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=dur)]

KEY = Scale(root=0, mode=Mode.MAJOR)
PARAMS = GeneratorParams(density=0.5, key_range_low=48, key_range_high=84)


class TestAleatoricModes:
    @pytest.mark.parametrize("mode", [
        "tone_cluster", "chance_operations", "repeat_ad_lib",
        "graphic_score", "pointillist", "textural_cloud",
    ])
    def test_render_returns_notes(self, mode):
        gen = AleatoricGenerator(PARAMS, mode=mode, density=0.5)
        notes = gen.render(_chords(), KEY, 32.0)
        assert len(notes) > 0
        assert all(isinstance(n, NoteInfo) for n in notes)

    @pytest.mark.parametrize("mode", [
        "tone_cluster", "chance_operations", "repeat_ad_lib",
        "graphic_score", "pointillist", "textural_cloud",
    ])
    def test_notes_in_range(self, mode):
        gen = AleatoricGenerator(PARAMS, mode=mode, density=0.5)
        notes = gen.render(_chords(), KEY, 32.0)
        assert all(48 <= n.pitch <= 84 for n in notes)

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown mode"):
            AleatoricGenerator(PARAMS, mode="nonexistent")

    def test_empty_on_no_chords(self):
        gen = AleatoricGenerator(PARAMS, mode="tone_cluster")
        notes = gen.render([], KEY, 32.0)
        assert notes == []

    def test_empty_on_zero_duration(self):
        gen = AleatoricGenerator(PARAMS, mode="tone_cluster")
        notes = gen.render(_chords(), KEY, 0.0)
        assert notes == []

    def test_tone_cluster_simultaneous(self):
        gen = AleatoricGenerator(PARAMS, mode="tone_cluster", density=1.0)
        notes = gen.render(_chords(), KEY, 32.0)
        # All notes start at approximately the same time
        starts = set(round(n.start, 2) for n in notes)
        assert len(starts) <= 2  # Allow minimal variance

    def test_pointillist_short_durations(self):
        gen = AleatoricGenerator(PARAMS, mode="pointillist", density=0.8)
        notes = gen.render(_chords(), KEY, 32.0)
        # Pointillist notes should be short
        assert all(n.duration <= 2.0 for n in notes)
