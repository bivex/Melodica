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
from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.staccato import StringsStaccatoGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]


class TestStringsLegatoGenerator:
    def test_produces_notes(self):
        gen = StringsLegatoGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        assert all(isinstance(n, NoteInfo) for n in notes)

    @pytest.mark.parametrize("section_size", ["solo", "ensemble", "full"])
    def test_section_sizes(self, section_size):
        gen = StringsLegatoGenerator(section_size=section_size)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("dynamic_shape", ["crescendo", "diminuendo", "cresc_dim", "flat"])
    def test_dynamic_shapes(self, dynamic_shape):
        gen = StringsLegatoGenerator(dynamic_shape=dynamic_shape)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("interval_pref", ["step", "leap", "wide", "mixed"])
    def test_interval_preferences(self, interval_pref):
        gen = StringsLegatoGenerator(interval_preference=interval_pref)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = StringsLegatoGenerator()
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert 0 <= n.pitch <= 127

    def test_empty_chords(self):
        gen = StringsLegatoGenerator()
        notes = gen.render([], C_MAJOR, 4.0)
        assert notes == []


class TestStringsPizzicatoGenerator:
    def test_produces_notes(self):
        gen = StringsPizzicatoGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["ostinato", "random", "waltz", "tremolo", "arco_mix"])
    def test_patterns(self, pattern):
        gen = StringsPizzicatoGenerator(pattern=pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_staccato_length(self):
        gen = StringsPizzicatoGenerator(staccato_length=0.1)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_divisi(self):
        gen = StringsPizzicatoGenerator(section_divisi=4)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_velocity_variation(self):
        gen = StringsPizzicatoGenerator(velocity_variation=0.8)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestStringsEnsembleGenerator:
    def test_produces_notes(self):
        gen = StringsEnsembleGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("section_size", ["solo", "chamber", "full"])
    def test_section_sizes(self, section_size):
        gen = StringsEnsembleGenerator(section_size=section_size)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("articulation", ["sustained", "staccato", "tremolo", "pizz"])
    def test_articulations(self, articulation):
        gen = StringsEnsembleGenerator(articulation=articulation)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("dynamic_curve", ["crescendo", "flat", "swell"])
    def test_dynamic_curves(self, dynamic_curve):
        gen = StringsEnsembleGenerator(dynamic_curve=dynamic_curve)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_divisi(self):
        gen = StringsEnsembleGenerator(divisi=6)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestTremoloStringsGenerator:
    def test_produces_notes(self):
        gen = TremoloStringsGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("variant", ["single", "chord", "octave", "cluster"])
    def test_variants(self, variant):
        gen = TremoloStringsGenerator(variant=variant)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_bow_speed(self):
        gen = TremoloStringsGenerator(bow_speed=0.03)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_dynamic_swell_off(self):
        gen = TremoloStringsGenerator(dynamic_swell=False)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_chord_variant_multiple_notes(self):
        gen = TremoloStringsGenerator(variant="chord")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) >= 2


class TestWoodwindsEnsembleGenerator:
    def test_produces_notes(self):
        gen = WoodwindsEnsembleGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("section", ["trio", "quartet", "full"])
    def test_sections(self, section):
        gen = WoodwindsEnsembleGenerator(section=section)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("articulation", ["legato", "staccato", "marcato"])
    def test_articulations(self, articulation):
        gen = WoodwindsEnsembleGenerator(articulation=articulation)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_dynamic_range(self):
        gen = WoodwindsEnsembleGenerator(dynamic_range=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestBrassSectionGenerator:
    def test_produces_notes(self):
        gen = BrassSectionGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize(
        "articulation", ["hit", "swell", "fanfare", "sustained", "falls", "doits"]
    )
    def test_articulations(self, articulation):
        gen = BrassSectionGenerator(articulation=articulation)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("voicing", ["closed", "open"])
    def test_voicings(self, voicing):
        gen = BrassSectionGenerator(voicing=voicing)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_intensity(self):
        gen = BrassSectionGenerator(intensity=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_divisi(self):
        gen = BrassSectionGenerator(divisi_count=5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_fanfare_has_multiple_notes(self):
        gen = BrassSectionGenerator(articulation="fanfare")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) >= 2


class TestOrchestralHitGenerator:
    def test_produces_notes(self):
        gen = OrchestralHitGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("hit_type", ["staccato", "sustain", "riser_hit", "braam"])
    def test_hit_types(self, hit_type):
        gen = OrchestralHitGenerator(hit_type=hit_type)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("voicing", ["unison", "octave", "chord"])
    def test_voicings(self, voicing):
        gen = OrchestralHitGenerator(voicing=voicing)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_staccato_short_duration(self):
        gen = OrchestralHitGenerator(hit_type="staccato", duration=0.2)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_sustain_long_duration(self):
        gen = OrchestralHitGenerator(hit_type="sustain", duration=4.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestStringsStaccatoGenerator:
    def test_produces_notes(self):
        gen = StringsStaccatoGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("style", ["roots", "octaves", "triad", "shell"])
    def test_styles(self, style):
        gen = StringsStaccatoGenerator(style=style)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_note_range(self):
        gen = StringsStaccatoGenerator(note_range_low=48, note_range_high=84)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert 48 <= n.pitch <= 84


class TestChoirAahsGenerator:
    def test_produces_notes(self):
        gen = ChoirAahsGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("voice_count", [2, 3, 4])
    def test_voice_counts(self, voice_count):
        gen = ChoirAahsGenerator(voice_count=voice_count)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("dynamics", ["pp", "mf", "ff"])
    def test_dynamics(self, dynamics):
        gen = ChoirAahsGenerator(dynamics=dynamics)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("syllable", ["aah", "oh", "mm"])
    def test_syllables(self, syllable):
        gen = ChoirAahsGenerator(syllable=syllable)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_vibrato(self):
        gen = ChoirAahsGenerator(vibrato=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = ChoirAahsGenerator()
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert 0 <= n.pitch <= 127
