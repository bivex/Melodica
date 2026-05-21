# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import pytest
from melodica.generators.melody import MelodyGenerator
from melodica.generators import GeneratorParams
from melodica.composer.unified_style import get_unified_style, UnifiedStyle, RhythmProfile


class TestFromStyle:
    def test_jazz_style(self):
        style = get_unified_style("jazz")
        gen = MelodyGenerator.from_style(style)
        assert gen.harmony_note_probability == style.melody.harmony_note_probability
        assert gen.syncopation == style.rhythm.syncopation

    def test_baroque_style(self):
        style = get_unified_style("baroque")
        gen = MelodyGenerator.from_style(style)
        assert gen.steps_probability == style.melody.steps_probability

    def test_overrides(self):
        style = get_unified_style("pop")
        gen = MelodyGenerator.from_style(style, syncopation=0.9)
        assert gen.syncopation == 0.9

    def test_density_from_rhythm_profile(self):
        style = get_unified_style("edm")
        gen = MelodyGenerator.from_style(style)
        assert gen.params.density == style.rhythm.density

    def test_register_from_melody_profile(self):
        style = get_unified_style("jazz")
        gen = MelodyGenerator.from_style(style)
        assert gen.note_range_low == style.melody.register_low
        assert gen.note_range_high == style.melody.register_high

    def test_type_error_on_wrong_type(self):
        with pytest.raises(TypeError):
            MelodyGenerator.from_style("not_a_style")

    def test_can_render(self):
        from melodica.types import Scale, Mode, ChordLabel, Quality
        style = get_unified_style("classical")
        gen = MelodyGenerator.from_style(style)
        key = Scale(root=0, mode=Mode.MAJOR)
        chords = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0, degree=1),
            ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0, degree=4),
        ]
        notes = gen.render(chords, key, 8.0)
        assert len(notes) > 0

    def test_all_builtin_styles(self):
        from melodica.composer.unified_style import list_styles
        for name in list_styles():
            style = get_unified_style(name)
            gen = MelodyGenerator.from_style(style)
            assert gen is not None


class TestRhythmProfileExtended:
    def test_default_groove_template(self):
        rp = RhythmProfile()
        assert rp.groove_template == "straight"

    def test_default_meter(self):
        rp = RhythmProfile()
        assert rp.beats_per_bar == 4
        assert rp.denominator == 4

    def test_custom_meter(self):
        rp = RhythmProfile(beats_per_bar=3, denominator=4)
        assert rp.beats_per_bar == 3

    def test_custom_groove(self):
        rp = RhythmProfile(groove_template="swing_60")
        assert rp.groove_template == "swing_60"

    def test_frozen(self):
        rp = RhythmProfile()
        with pytest.raises(AttributeError):
            rp.groove_template = "shuffle"
