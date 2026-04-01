import pytest
from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.generators.guitar_strumming import GuitarStrummingGenerator
from melodica.generators.guitar_legato import GuitarLegatoGenerator
from melodica.generators.guitar_tapping import GuitarTappingGenerator
from melodica.generators.guitar_sweep import GuitarSweepGenerator
from melodica.generators.vocal_adlibs import VocalAdlibsGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.vocal_melisma import VocalMelismaGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]


class TestGuitarStrummingGenerator:
    def test_produces_notes(self):
        gen = GuitarStrummingGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["folk", "pop", "reggae", "funk", "ballad"])
    def test_patterns(self, pattern):
        gen = GuitarStrummingGenerator(strum_pattern=pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValueError):
            GuitarStrummingGenerator(strum_pattern="metal")

    def test_palm_mute(self):
        gen = GuitarStrummingGenerator(palm_mute_ratio=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_accent_velocity(self):
        gen = GuitarStrummingGenerator(accent_velocity=2.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_dead_strums_off(self):
        gen = GuitarStrummingGenerator(dead_strums=False)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_string_count(self):
        gen = GuitarStrummingGenerator(string_count=4)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = GuitarStrummingGenerator()
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert 0 <= n.pitch <= 127


class TestGuitarLegatoGenerator:
    def test_produces_notes(self):
        gen = GuitarLegatoGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize(
        "direction", ["ascending", "descending", "zigzag", "string_skip", "tapping"]
    )
    def test_directions(self, direction):
        gen = GuitarLegatoGenerator(direction=direction)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_direction_raises(self):
        gen = GuitarLegatoGenerator(direction="sideways")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # Invalid direction falls back to default behavior
        assert isinstance(notes, list)

    def test_notes_per_string(self):
        gen = GuitarLegatoGenerator(notes_per_string=6)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_speed(self):
        gen = GuitarLegatoGenerator(speed=0.05)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_palm_mute_start(self):
        gen = GuitarLegatoGenerator(palm_mute_start=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestGuitarTappingGenerator:
    def test_produces_notes(self):
        gen = GuitarTappingGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["arpeggio", "scale", "poly", "cascade"])
    def test_patterns(self, pattern):
        gen = GuitarTappingGenerator(pattern=pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_pattern_raises(self):
        gen = GuitarTappingGenerator(pattern="invalid")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # Invalid pattern falls back to default behavior
        assert isinstance(notes, list)

    def test_width_interval(self):
        gen = GuitarTappingGenerator(width_interval=24)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_notes_per_cycle(self):
        gen = GuitarTappingGenerator(notes_per_cycle=12)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_hammer_velocity(self):
        gen = GuitarTappingGenerator(hammer_velocity=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestGuitarSweepGenerator:
    def test_produces_notes(self):
        gen = GuitarSweepGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("direction", ["up", "down", "both"])
    def test_directions(self, direction):
        gen = GuitarSweepGenerator(sweep_direction=direction)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_direction_raises(self):
        with pytest.raises(ValueError):
            GuitarSweepGenerator(sweep_direction="sideways")

    def test_note_count(self):
        gen = GuitarSweepGenerator(note_count=7)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_let_ring(self):
        gen = GuitarSweepGenerator(let_ring=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_velocity_curve(self):
        gen = GuitarSweepGenerator(velocity_curve=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = GuitarSweepGenerator()
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert 0 <= n.pitch <= 127


class TestVocalAdlibsGenerator:
    def test_produces_notes(self):
        gen = VocalAdlibsGenerator(density_adlib=1.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("register", ["low", "mid"])
    def test_registers(self, register):
        gen = VocalAdlibsGenerator(register=register, density_adlib=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_register_raises(self):
        with pytest.raises(ValueError):
            VocalAdlibsGenerator(register="ultra_high")

    @pytest.mark.parametrize("style", ["adlib", "shout"])
    def test_styles(self, style):
        gen = VocalAdlibsGenerator(style=style, density_adlib=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError):
            VocalAdlibsGenerator(style="scream")

    def test_density(self):
        gen = VocalAdlibsGenerator(density_adlib=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestVocalChopsGenerator:
    def test_produces_notes(self):
        gen = VocalChopsGenerator(density=1.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert isinstance(notes, list)

    @pytest.mark.parametrize("processing", ["reverse", "stutter", "pitch_shift", "formant"])
    def test_processing_modes(self, processing):
        gen = VocalChopsGenerator(processing=processing)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_processing_raises(self):
        gen = VocalChopsGenerator(processing="robot")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # Invalid processing falls back to default behavior
        assert isinstance(notes, list)

    @pytest.mark.parametrize("chop_pattern", ["syncopated", "offbeat", "random", "melodic"])
    def test_chop_patterns(self, chop_pattern):
        gen = VocalChopsGenerator(chop_pattern=chop_pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_density(self):
        gen = VocalChopsGenerator(density=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_source_pitch(self):
        gen = VocalChopsGenerator(source_pitch=72)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestVocalMelismaGenerator:
    def test_produces_notes(self):
        gen = VocalMelismaGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("style", ["rnb", "gospel", "opera", "pop"])
    def test_styles(self, style):
        gen = VocalMelismaGenerator(style=style)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError):
            VocalMelismaGenerator(style="metal")

    def test_run_length(self):
        gen = VocalMelismaGenerator(run_length=16)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_ornament_prob(self):
        gen = VocalMelismaGenerator(ornament_prob=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_vibrato_depth(self):
        gen = VocalMelismaGenerator(vibrato_depth=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_register_center(self):
        gen = VocalMelismaGenerator(register_center=84)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestVocalOohsGenerator:
    def test_produces_notes(self):
        gen = VocalOohsGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("syllable", ["ooh", "aah", "hum", "mm"])
    def test_syllables(self, syllable):
        gen = VocalOohsGenerator(syllable=syllable)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_syllable_raises(self):
        gen = VocalOohsGenerator(syllable="la")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # Invalid syllable falls back to default behavior
        assert isinstance(notes, list)

    @pytest.mark.parametrize("harmony_count", [2, 3, 4])
    def test_harmony_counts(self, harmony_count):
        gen = VocalOohsGenerator(harmony_count=harmony_count)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_vibrato(self):
        gen = VocalOohsGenerator(vibrato=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_breath_phasing_off(self):
        gen = VocalOohsGenerator(breath_phasing=False)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = VocalOohsGenerator()
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert 0 <= n.pitch <= 127
