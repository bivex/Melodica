import pytest
from melodica.types import Scale, Mode
from melodica.composition import Style, Section, Composition
from melodica.composition.styles import (
    STYLES,
    DARK_FANTASY_STYLE,
    SYMPHONIC_DARK_FANTASY_STYLE,
    CLASSICAL_STYLE,
    JAZZ_STYLE,
    FILM_STYLE,
    POP_STYLE,
    AMBIENT_STYLE,
)


class TestCompositionStyleRegistry:
    @pytest.mark.parametrize(
        "name", ["dark_fantasy", "symphonic", "classical", "jazz", "film", "pop", "ambient"]
    )
    def test_all_styles_exist(self, name):
        assert name in STYLES
        style = STYLES[name]
        assert isinstance(style, Style)
        assert style.name

    def test_style_count(self):
        assert len(STYLES) == 7

    def test_style_has_required_fields(self):
        for name, style in STYLES.items():
            assert style.name
            assert len(style.allowed_scales) > 0
            assert len(style.track_mapping) > 0
            assert len(style.instrument_mapping) > 0
            assert style.typical_bpm > 0


class TestDarkFantasyStyle:
    def test_name(self):
        assert DARK_FANTASY_STYLE.name == "Dark Fantasy"

    def test_scales_are_minor_oriented(self):
        pcs = set()
        for s in DARK_FANTASY_STYLE.allowed_scales:
            pcs.add(s.root)
        assert 9 in pcs  # A Minor

    def test_tracks(self):
        assert "Bass" in DARK_FANTASY_STYLE.track_mapping
        assert "Lead" in DARK_FANTASY_STYLE.track_mapping

    def test_instruments(self):
        assert DARK_FANTASY_STYLE.instrument_mapping["Lead"] == 73  # Flute

    def test_progressions(self):
        assert "Intro" in DARK_FANTASY_STYLE.progressions
        assert "Battle" in DARK_FANTASY_STYLE.progressions

    def test_slow_tempo(self):
        assert DARK_FANTASY_STYLE.typical_bpm <= 80


class TestSymphonicStyle:
    def test_name(self):
        assert SYMPHONIC_DARK_FANTASY_STYLE.name == "Symphonic Dark Fantasy"

    def test_full_orchestra(self):
        assert len(SYMPHONIC_DARK_FANTASY_STYLE.track_mapping) == 12

    def test_all_instruments_mapped(self):
        for track_name in SYMPHONIC_DARK_FANTASY_STYLE.track_mapping:
            assert track_name in SYMPHONIC_DARK_FANTASY_STYLE.instrument_mapping


class TestClassicalStyle:
    def test_name(self):
        assert CLASSICAL_STYLE.name == "Classical"

    def test_major_scales(self):
        modes = {s.mode for s in CLASSICAL_STYLE.allowed_scales}
        assert Mode.MAJOR in modes

    def test_traditional_instruments(self):
        assert CLASSICAL_STYLE.instrument_mapping["Melody"] == 40  # Violin
        assert CLASSICAL_STYLE.instrument_mapping["Bass"] == 42  # Cello

    def test_classical_progressions(self):
        progs = CLASSICAL_STYLE.progressions.get("Theme_A", [])
        assert any("I IV V I" in p for p in progs)


class TestJazzStyle:
    def test_name(self):
        assert JAZZ_STYLE.name == "Jazz"

    def test_bebop_scales(self):
        modes = {s.mode for s in JAZZ_STYLE.allowed_scales}
        assert Mode.BEBOP_DOMINANT in modes
        assert Mode.DORIAN in modes

    def test_jazz_instruments(self):
        assert JAZZ_STYLE.instrument_mapping["Melody"] == 65  # Alto Sax
        assert JAZZ_STYLE.instrument_mapping["Chords"] == 1  # Piano

    def test_extended_chord_progressions(self):
        progs = JAZZ_STYLE.progressions.get("Head", [])
        assert any("7" in p for p in progs)

    def test_fast_tempo(self):
        assert JAZZ_STYLE.typical_bpm >= 120


class TestFilmStyle:
    def test_name(self):
        assert FILM_STYLE.name == "Film Score"

    def test_lydian_scale(self):
        modes = {s.mode for s in FILM_STYLE.allowed_scales}
        assert Mode.LYDIAN in modes

    def test_orchestral_instruments(self):
        assert FILM_STYLE.instrument_mapping["Melody"] == 40  # Violins
        assert FILM_STYLE.instrument_mapping["Chords"] == 60  # French Horn

    def test_dramatic_sections(self):
        assert "Climax" in FILM_STYLE.progressions
        assert "Build" in FILM_STYLE.progressions


class TestPopStyle:
    def test_name(self):
        assert POP_STYLE.name == "Pop"

    def test_major_scales(self):
        modes = {s.mode for s in POP_STYLE.allowed_scales}
        assert Mode.MAJOR in modes
        assert Mode.NATURAL_MINOR in modes

    def test_tracks(self):
        assert "Melody" in POP_STYLE.track_mapping
        assert "Chords" in POP_STYLE.track_mapping
        assert "Bass" in POP_STYLE.track_mapping
        assert "Drums" in POP_STYLE.track_mapping

    def test_instruments(self):
        assert POP_STYLE.instrument_mapping["Melody"] == 81  # Lead Synth
        assert POP_STYLE.instrument_mapping["Bass"] == 33  # Electric Bass

    def test_pop_progressions(self):
        verse = POP_STYLE.progressions.get("Verse", [])
        assert any("I V vi IV" in p for p in verse)
        assert "Chorus" in POP_STYLE.progressions

    def test_upbeat_tempo(self):
        assert 100 <= POP_STYLE.typical_bpm <= 140

    def test_short_phrases(self):
        verse = POP_STYLE.progressions.get("Verse", [])
        for p in verse:
            parts = p.split()
            assert len(parts) <= 4  # short progressions


class TestAmbientStyle:
    def test_name(self):
        assert AMBIENT_STYLE.name == "Ambient"

    def test_lydian_and_dorian(self):
        modes = {s.mode for s in AMBIENT_STYLE.allowed_scales}
        assert Mode.LYDIAN in modes
        assert Mode.DORIAN in modes

    def test_pad_instruments(self):
        assert AMBIENT_STYLE.instrument_mapping["Pad"] == 89  # Synth Pad
        assert AMBIENT_STYLE.instrument_mapping["Drone"] == 48  # String Ensemble

    def test_sparse_progressions(self):
        drone = AMBIENT_STYLE.progressions.get("Drone", [])
        assert any(p == "I" for p in drone)
        assert any(p == "Im" for p in drone)

    def test_slow_tempo(self):
        assert AMBIENT_STYLE.typical_bpm <= 80

    def test_tracks(self):
        assert "Pad" in AMBIENT_STYLE.track_mapping
        assert "Drone" in AMBIENT_STYLE.track_mapping
        assert "Texture" in AMBIENT_STYLE.track_mapping

    def test_instruments_mapped(self):
        for track_name in AMBIENT_STYLE.track_mapping:
            assert track_name in AMBIENT_STYLE.instrument_mapping


class TestStyleIntegration:
    def test_composition_uses_style(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        comp = Composition("Test Pop Song", key)
        style = POP_STYLE
        comp.add_section("Verse", 16.0, "I V vi IV", style.track_mapping)
        assert len(comp.sections) == 1
        assert comp.sections[0].name == "Verse"

    def test_all_styles_have_consistent_mappings(self):
        for name, style in STYLES.items():
            for track_name in style.track_mapping:
                assert track_name in style.instrument_mapping, (
                    f"Style '{name}': track '{track_name}' missing instrument mapping"
                )

    def test_all_styles_have_progressions(self):
        for name, style in STYLES.items():
            assert len(style.progressions) > 0, f"Style '{name}' has no progressions"
